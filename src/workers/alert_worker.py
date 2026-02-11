"""
告警Worker
从RabbitMQ消费告警任务并发送通知
"""

import asyncio
import logging
import json
from typing import Dict, Any
import aio_pika

from ..alerting.notifiers import TelegramNotifier, EmailNotifier, WebhookNotifier

logger = logging.getLogger(__name__)


class AlertWorker:
    """告警Worker"""

    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None
        self.notifiers = []
        self.running = False

    def add_notifier(self, notifier):
        """添加通知器"""
        self.notifiers.append(notifier)

    async def start(self):
        """启动Worker"""
        logger.info("Starting Alert Worker...")
        self.running = True

        self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=1)

        queue = await self.channel.declare_queue(
            'alert_tasks',
            durable=True
        )

        await queue.consume(self.process_message)
        logger.info("Alert Worker started")

        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            await self.stop()

    async def stop(self):
        """停止Worker"""
        logger.info("Stopping Alert Worker...")
        self.running = False

        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()

        logger.info("Alert Worker stopped")

    async def process_message(self, message: aio_pika.IncomingMessage):
        """处理消息"""
        async with message.process():
            try:
                alert = json.loads(message.body.decode())
                logger.info(f"Processing alert: {alert.get('title')}")

                await self.send_alert(alert)

            except Exception as e:
                logger.error(f"Failed to process alert: {e}", exc_info=True)

    async def send_alert(self, alert: Dict[str, Any]):
        """发送告警"""
        tasks = []
        for notifier in self.notifiers:
            tasks.append(notifier.send_alert(alert))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Notifier {i} failed: {result}")
            elif result:
                logger.info(f"Alert sent via {self.notifiers[i].name}")


async def main():
    """主函数"""
    import os

    rabbitmq_url = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/')
    worker = AlertWorker(rabbitmq_url)

    # 配置通知器
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if telegram_token and telegram_chat_id:
        worker.add_notifier(TelegramNotifier(telegram_token, telegram_chat_id))

    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()


if __name__ == '__main__':
    asyncio.run(main())
