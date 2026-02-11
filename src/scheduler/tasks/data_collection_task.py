"""
数据采集定时任务
定期采集市场数据
"""

import asyncio
import logging
from typing import List
import aio_pika
import json

logger = logging.getLogger(__name__)


class DataCollectionTask:
    """数据采集定时任务"""

    def __init__(self, rabbitmq_url: str, symbols: List[str]):
        self.rabbitmq_url = rabbitmq_url
        self.symbols = symbols

    async def run(self):
        """执行任务"""
        logger.info("Running data collection task...")

        try:
            # 连接RabbitMQ
            connection = await aio_pika.connect_robust(self.rabbitmq_url)
            channel = await connection.channel()

            # 声明队列
            queue = await channel.declare_queue('data_collection_tasks', durable=True)

            # 为每个交易对发送采集任务
            for symbol in self.symbols:
                task = {
                    'exchange': 'binance',
                    'symbol': symbol,
                    'data_type': 'kline',
                    'interval': '1m',
                    'limit': 100
                }

                await channel.default_exchange.publish(
                    aio_pika.Message(
                        body=json.dumps(task).encode(),
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                    ),
                    routing_key='data_collection_tasks'
                )

                logger.info(f"Sent collection task for {symbol}")

            await connection.close()
            logger.info("Data collection task completed")

        except Exception as e:
            logger.error(f"Data collection task failed: {e}", exc_info=True)
