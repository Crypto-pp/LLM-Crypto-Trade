"""
数据采集Worker
从RabbitMQ消费采集任务并执行数据采集
"""

import asyncio
import logging
import json
from typing import Dict, Any
import aio_pika
from datetime import datetime

from ..data_pipeline.collectors.binance_collector import BinanceCollector
from ..monitoring.metrics import DATA_COLLECTION_SUCCESS, DATA_COLLECTION_FAILURE

logger = logging.getLogger(__name__)


class DataCollectorWorker:
    """数据采集Worker"""

    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None
        self.collectors = {}
        self.running = False

    async def start(self):
        """启动Worker"""
        logger.info("Starting Data Collector Worker...")
        self.running = True

        # 连接RabbitMQ
        self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=1)

        # 声明队列
        queue = await self.channel.declare_queue(
            'data_collection_tasks',
            durable=True
        )

        # 开始消费
        await queue.consume(self.process_message)
        logger.info("Data Collector Worker started")

        # 保持运行
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            await self.stop()

    async def stop(self):
        """停止Worker"""
        logger.info("Stopping Data Collector Worker...")
        self.running = False

        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()

        logger.info("Data Collector Worker stopped")

    async def process_message(self, message: aio_pika.IncomingMessage):
        """处理消息"""
        async with message.process():
            try:
                # 解析消息
                task = json.loads(message.body.decode())
                logger.info(f"Processing collection task: {task}")

                # 执行采集
                await self.collect_data(task)

                # 记录成功
                DATA_COLLECTION_SUCCESS.labels(
                    exchange=task.get('exchange', 'unknown'),
                    symbol=task.get('symbol', 'unknown'),
                    data_type=task.get('data_type', 'unknown')
                ).inc()

            except Exception as e:
                logger.error(f"Failed to process message: {e}", exc_info=True)

                # 记录失败
                task = json.loads(message.body.decode())
                DATA_COLLECTION_FAILURE.labels(
                    exchange=task.get('exchange', 'unknown'),
                    symbol=task.get('symbol', 'unknown'),
                    error_type=type(e).__name__
                ).inc()

    async def collect_data(self, task: Dict[str, Any]):
        """执行数据采集"""
        exchange = task.get('exchange')
        symbol = task.get('symbol')
        data_type = task.get('data_type', 'kline')

        # 获取或创建采集器
        if exchange not in self.collectors:
            if exchange == 'binance':
                self.collectors[exchange] = BinanceCollector()
            else:
                raise ValueError(f"Unsupported exchange: {exchange}")

        collector = self.collectors[exchange]

        # 执行采集
        if data_type == 'kline':
            interval = task.get('interval', '1m')
            limit = task.get('limit', 100)
            await collector.collect_klines(symbol, interval, limit)
        elif data_type == 'ticker':
            await collector.collect_ticker(symbol)
        elif data_type == 'orderbook':
            await collector.collect_orderbook(symbol)
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

        logger.info(f"Data collection completed: {exchange} {symbol} {data_type}")


async def main():
    """主函数"""
    import os

    rabbitmq_url = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/')

    worker = DataCollectorWorker(rabbitmq_url)

    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()


if __name__ == '__main__':
    asyncio.run(main())
