"""
事件驱动引擎

实现事件驱动架构的核心组件：
- Event 基类
- MarketEvent - 市场数据事件
- SignalEvent - 交易信号事件
- OrderEvent - 订单事件
- FillEvent - 成交事件
- EventQueue - 事件队列管理
"""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from queue import Queue, Empty
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型枚举"""
    MARKET = "MARKET"
    SIGNAL = "SIGNAL"
    ORDER = "ORDER"
    FILL = "FILL"


class Event:
    """
    事件基类

    所有事件的基础类，定义了事件的基本属性
    """

    def __init__(self, event_type: EventType):
        """
        初始化事件

        Args:
            event_type: 事件类型
        """
        self.type = event_type
        self.timestamp = datetime.now()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(type={self.type.value}, timestamp={self.timestamp})"


class MarketEvent(Event):
    """
    市场数据事件

    当新的市场数据到达时触发
    包含K线数据、价格、成交量等信息
    """

    def __init__(
        self,
        symbol: str,
        timestamp: datetime,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: float,
        **kwargs
    ):
        """
        初始化市场事件

        Args:
            symbol: 交易对符号
            timestamp: 时间戳
            open_price: 开盘价
            high_price: 最高价
            low_price: 最低价
            close_price: 收盘价
            volume: 成交量
            **kwargs: 其他市场数据
        """
        super().__init__(EventType.MARKET)
        self.symbol = symbol
        self.timestamp = timestamp
        self.open = open_price
        self.high = high_price
        self.low = low_price
        self.close = close_price
        self.volume = volume
        self.extra_data = kwargs

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            **self.extra_data
        }

    def __repr__(self) -> str:
        return (f"MarketEvent(symbol={self.symbol}, timestamp={self.timestamp}, "
                f"close={self.close}, volume={self.volume})")


class SignalEvent(Event):
    """
    交易信号事件

    策略生成交易信号时触发
    包含买入、卖出、持有等信号
    """

    def __init__(
        self,
        symbol: str,
        timestamp: datetime,
        signal_type: str,
        strength: float = 1.0,
        price: Optional[float] = None,
        metadata: Optional[Dict] = None
    ):
        """
        初始化信号事件

        Args:
            symbol: 交易对符号
            timestamp: 时间戳
            signal_type: 信号类型 ('BUY', 'SELL', 'HOLD', 'CLOSE')
            strength: 信号强度 (0-1)
            price: 信号价格
            metadata: 额外元数据
        """
        super().__init__(EventType.SIGNAL)
        self.symbol = symbol
        self.timestamp = timestamp
        self.signal_type = signal_type.upper()
        self.strength = max(0.0, min(1.0, strength))  # 限制在0-1之间
        self.price = price
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        return (f"SignalEvent(symbol={self.symbol}, type={self.signal_type}, "
                f"strength={self.strength:.2f}, price={self.price})")


class OrderEvent(Event):
    """
    订单事件

    根据信号生成订单时触发
    包含订单的详细信息
    """

    def __init__(
        self,
        symbol: str,
        timestamp: datetime,
        order_type: str,
        side: str,
        quantity: float,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        order_id: Optional[str] = None
    ):
        """
        初始化订单事件

        Args:
            symbol: 交易对符号
            timestamp: 时间戳
            order_type: 订单类型 ('MARKET', 'LIMIT', 'STOP')
            side: 订单方向 ('BUY', 'SELL')
            quantity: 数量
            price: 价格（限价单）
            stop_loss: 止损价格
            take_profit: 止盈价格
            order_id: 订单ID
        """
        super().__init__(EventType.ORDER)
        self.symbol = symbol
        self.timestamp = timestamp
        self.order_type = order_type.upper()
        self.side = side.upper()
        self.quantity = quantity
        self.price = price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.order_id = order_id or self._generate_order_id()

    def _generate_order_id(self) -> str:
        """生成订单ID"""
        return f"ORDER_{self.symbol}_{self.timestamp.strftime('%Y%m%d%H%M%S%f')}"

    def __repr__(self) -> str:
        return (f"OrderEvent(id={self.order_id}, symbol={self.symbol}, "
                f"side={self.side}, type={self.order_type}, "
                f"quantity={self.quantity}, price={self.price})")


class FillEvent(Event):
    """
    成交事件

    订单成交时触发
    包含成交的详细信息
    """

    def __init__(
        self,
        symbol: str,
        timestamp: datetime,
        side: str,
        quantity: float,
        fill_price: float,
        commission: float = 0.0,
        order_id: Optional[str] = None,
        fill_id: Optional[str] = None
    ):
        """
        初始化成交事件

        Args:
            symbol: 交易对符号
            timestamp: 时间戳
            side: 方向 ('BUY', 'SELL')
            quantity: 成交数量
            fill_price: 成交价格
            commission: 手续费
            order_id: 关联的订单ID
            fill_id: 成交ID
        """
        super().__init__(EventType.FILL)
        self.symbol = symbol
        self.timestamp = timestamp
        self.side = side.upper()
        self.quantity = quantity
        self.fill_price = fill_price
        self.commission = commission
        self.order_id = order_id
        self.fill_id = fill_id or self._generate_fill_id()

        # 计算成交金额
        self.fill_cost = quantity * fill_price
        self.total_cost = self.fill_cost + commission

    def _generate_fill_id(self) -> str:
        """生成成交ID"""
        return f"FILL_{self.symbol}_{self.timestamp.strftime('%Y%m%d%H%M%S%f')}"

    def __repr__(self) -> str:
        return (f"FillEvent(id={self.fill_id}, symbol={self.symbol}, "
                f"side={self.side}, quantity={self.quantity}, "
                f"price={self.fill_price}, commission={self.commission})")


class EventQueue:
    """
    事件队列管理器

    管理事件的添加、获取和处理
    使用FIFO队列确保事件按顺序处理
    """

    def __init__(self, maxsize: int = 0):
        """
        初始化事件队列

        Args:
            maxsize: 队列最大大小，0表示无限制
        """
        self.queue = Queue(maxsize=maxsize)
        self.event_count = {event_type: 0 for event_type in EventType}
        logger.info("EventQueue initialized")

    def put(self, event: Event) -> None:
        """
        添加事件到队列

        Args:
            event: 事件对象
        """
        self.queue.put(event)
        self.event_count[event.type] += 1
        logger.debug(f"Event added to queue: {event}")

    def get(self, block: bool = True, timeout: Optional[float] = None) -> Optional[Event]:
        """
        从队列获取事件

        Args:
            block: 是否阻塞等待
            timeout: 超时时间（秒）

        Returns:
            事件对象，如果队列为空且非阻塞则返回None
        """
        try:
            event = self.queue.get(block=block, timeout=timeout)
            logger.debug(f"Event retrieved from queue: {event}")
            return event
        except Empty:
            return None

    def empty(self) -> bool:
        """检查队列是否为空"""
        return self.queue.empty()

    def size(self) -> int:
        """获取队列大小"""
        return self.queue.qsize()

    def clear(self) -> None:
        """清空队列"""
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except Empty:
                break
        logger.info("EventQueue cleared")

    def get_statistics(self) -> Dict[str, int]:
        """
        获取事件统计信息

        Returns:
            各类型事件的数量统计
        """
        return {
            event_type.value: count
            for event_type, count in self.event_count.items()
        }

    def __repr__(self) -> str:
        return f"EventQueue(size={self.size()}, stats={self.get_statistics()})"
