"""
消息队列集成模块

提供RabbitMQ消息生产者和消费者
"""

import json
import asyncio
from typing import Dict, Callable, Optional
from datetime import datetime
from loguru import logger
import aio_pika
from aio_pika import ExchangeType, DeliveryMode

from .adapters.base import KlineData, TickerData


class MessageProducer:
    """消息生产者"""

    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.exchange: Optional[aio_pika.Exchange] = None

    async def connect(self):
        """连接到RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)

            # 创建交换机
            self.exchange = await self.channel.declare_exchange(
                'market.data',
                ExchangeType.TOPIC,
                durable=True
            )

            logger.info("Message producer connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self):
        """断开连接"""
        if self.connection:
            await self.connection.close()
            logger.info("Message producer disconnected")

    async def publish_kline(
        self,
        exchange: str,
        symbol: str,
        interval: str,
        kline: KlineData
    ):
        """发布K线数据"""
        if not self.exchange:
            raise RuntimeError("Not connected to RabbitMQ")

        routing_key = f"market.kline.{exchange}.{symbol}"

        message_body = {
            'exchange': exchange,
            'symbol': symbol,
            'interval': interval,
            'timestamp': kline.timestamp.isoformat(),
            'open': str(kline.open),
            'high': str(kline.high),
            'low': str(kline.low),
            'close': str(kline.close),
            'volume': str(kline.volume),
            'quote_volume': str(kline.quote_volume) if kline.quote_volume else None,
            'trades_count': kline.trades_count
        }

        message = aio_pika.Message(
            body=json.dumps(message_body).encode(),
            delivery_mode=DeliveryMode.PERSISTENT,
            content_type='application/json'
        )

        await self.exchange.publish(message, routing_key=routing_key)
        logger.debug(f"Published kline: {routing_key}")

    async def publish_ticker(
        self,
        exchange: str,
        ticker: TickerData
    ):
        """发布价格数据"""
        if not self.exchange:
            raise RuntimeError("Not connected to RabbitMQ")

        routing_key = f"market.ticker.{exchange}.{ticker.symbol}"

        message_body = {
            'exchange': exchange,
            'symbol': ticker.symbol,
            'timestamp': ticker.timestamp.isoformat(),
            'last_price': str(ticker.last_price),
            'bid_price': str(ticker.bid_price) if ticker.bid_price else None,
            'ask_price': str(ticker.ask_price) if ticker.ask_price else None,
            'volume_24h': str(ticker.volume_24h) if ticker.volume_24h else None,
            'price_change_24h': str(ticker.price_change_24h) if ticker.price_change_24h else None
        }

        message = aio_pika.Message(
            body=json.dumps(message_body).encode(),
            delivery_mode=DeliveryMode.PERSISTENT,
            content_type='application/json'
        )

        await self.exchange.publish(message, routing_key=routing_key)
        logger.debug(f"Published ticker: {routing_key}")


class MessageConsumer:
    """消息消费者"""

    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.consuming = False

    async def connect(self):
        """连接到RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)

            logger.info("Message consumer connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self):
        """断开连接"""
        self.consuming = False
        if self.connection:
            await self.connection.close()
            logger.info("Message consumer disconnected")

    async def consume_klines(
        self,
        exchange: str,
        symbol: str,
        callback: Callable
    ):
        """消费K线数据"""
        if not self.channel:
            raise RuntimeError("Not connected to RabbitMQ")

        # 声明交换机
        market_exchange = await self.channel.declare_exchange(
            'market.data',
            ExchangeType.TOPIC,
            durable=True
        )

        # 创建队列
        queue_name = f"kline.{exchange}.{symbol}"
        queue = await self.channel.declare_queue(
            queue_name,
            durable=True,
            arguments={
                'x-message-ttl': 3600000,  # 1小时TTL
                'x-max-length': 100000,
            }
        )

        # 绑定队列
        routing_key = f"market.kline.{exchange}.{symbol}"
        await queue.bind(market_exchange, routing_key=routing_key)

        logger.info(f"Consuming klines: {routing_key}")

        async def on_message(message: aio_pika.IncomingMessage):
            async with message.process():
                try:
                    data = json.loads(message.body.decode())
                    await callback(data)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        await queue.consume(on_message)
        self.consuming = True

    async def consume_tickers(
        self,
        exchange: str,
        symbol: str,
        callback: Callable
    ):
        """消费价格数据"""
        if not self.channel:
            raise RuntimeError("Not connected to RabbitMQ")

        # 声明交换机
        market_exchange = await self.channel.declare_exchange(
            'market.data',
            ExchangeType.TOPIC,
            durable=True
        )

        # 创建队列
        queue_name = f"ticker.{exchange}.{symbol}"
        queue = await self.channel.declare_queue(
            queue_name,
            durable=False,
            auto_delete=True
        )

        # 绑定队列
        routing_key = f"market.ticker.{exchange}.{symbol}"
        await queue.bind(market_exchange, routing_key=routing_key)

        logger.info(f"Consuming tickers: {routing_key}")

        async def on_message(message: aio_pika.IncomingMessage):
            async with message.process():
                try:
                    data = json.loads(message.body.decode())
                    await callback(data)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        await queue.consume(on_message)
        self.consuming = True
