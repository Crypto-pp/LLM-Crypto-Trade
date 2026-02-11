"""
策略Worker
从RabbitMQ消费策略任务并执行策略分析
"""

import asyncio
import logging
import json
from typing import Dict, Any
import aio_pika

from ..monitoring.metrics import SIGNAL_GENERATED

logger = logging.getLogger(__name__)


class StrategyWorker:
    """策略Worker"""

    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None
        self.running = False

    async def start(self):
        """启动Worker"""
        logger.info("Starting Strategy Worker...")
        self.running = True

        self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=1)

        queue = await self.channel.declare_queue(
            'strategy_tasks',
            durable=True
        )

        await queue.consume(self.process_message)
        logger.info("Strategy Worker started")

        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            await self.stop()

    async def stop(self):
        """停止Worker"""
        logger.info("Stopping Strategy Worker...")
        self.running = False

        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()

        logger.info("Strategy Worker stopped")

    async def process_message(self, message: aio_pika.IncomingMessage):
        """处理消息"""
        async with message.process():
            try:
                task = json.loads(message.body.decode())
                logger.info(f"Processing strategy task: {task}")

                await self.execute_strategy(task)

            except Exception as e:
                logger.error(f"Failed to process strategy task: {e}", exc_info=True)

    async def execute_strategy(self, task: Dict[str, Any]):
        """执行策略"""
        strategy_name = task.get('strategy_name')
        symbol = task.get('symbol')

        logger.info(f"Executing strategy {strategy_name} for {symbol}")

        # 这里应该执行实际的策略逻辑
        # 简化实现

        logger.info(f"Strategy execution completed for {symbol}")


async def main():
    """主函数"""
    import os

    rabbitmq_url = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/')
    worker = StrategyWorker(rabbitmq_url)

    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()


if __name__ == '__main__':
    asyncio.run(main())
