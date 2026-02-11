"""
执行处理器

负责：
- 订单撮合模拟
- 滑点模拟
- 手续费计算
- 成交价格模拟
"""

import logging
from typing import Optional
from datetime import datetime

from .event_engine import OrderEvent, FillEvent

logger = logging.getLogger(__name__)


class ExecutionHandler:
    """
    执行处理器基类

    模拟订单的执行过程
    """

    def __init__(self, commission_rate: float = 0.001):
        """
        初始化执行处理器

        Args:
            commission_rate: 手续费率（默认0.1%）
        """
        self.commission_rate = commission_rate

    def execute_order(self, order: OrderEvent) -> FillEvent:
        """
        执行订单

        Args:
            order: 订单事件

        Returns:
            成交事件
        """
        raise NotImplementedError("Must implement execute_order()")


class SimulatedExecutionHandler(ExecutionHandler):
    """
    模拟执行处理器

    模拟真实的订单执行，包括滑点和手续费
    """

    def __init__(
        self,
        commission_rate: float = 0.001,
        slippage_rate: float = 0.0005
    ):
        """
        初始化模拟执行处理器

        Args:
            commission_rate: 手续费率（默认0.1%）
            slippage_rate: 滑点率（默认0.05%）
        """
        super().__init__(commission_rate)
        self.slippage_rate = slippage_rate
        logger.info(f"SimulatedExecutionHandler initialized: "
                   f"commission={commission_rate}, slippage={slippage_rate}")

    def execute_order(self, order: OrderEvent, current_price: float) -> FillEvent:
        """
        执行订单

        Args:
            order: 订单事件
            current_price: 当前市场价格

        Returns:
            成交事件
        """
        # 计算成交价格（考虑滑点）
        fill_price = self._calculate_fill_price(order, current_price)

        # 计算手续费
        commission = self._calculate_commission(order.quantity, fill_price)

        # 创建成交事件
        fill = FillEvent(
            symbol=order.symbol,
            timestamp=order.timestamp,
            side=order.side,
            quantity=order.quantity,
            fill_price=fill_price,
            commission=commission,
            order_id=order.order_id
        )

        logger.info(f"Order executed: {fill}")
        return fill

    def _calculate_fill_price(self, order: OrderEvent, current_price: float) -> float:
        """
        计算成交价格（考虑滑点）

        Args:
            order: 订单事件
            current_price: 当前市场价格

        Returns:
            成交价格
        """
        if order.order_type == 'MARKET':
            # 市价单：考虑滑点
            if order.side == 'BUY':
                # 买入时价格上滑
                fill_price = current_price * (1 + self.slippage_rate)
            else:
                # 卖出时价格下滑
                fill_price = current_price * (1 - self.slippage_rate)
        elif order.order_type == 'LIMIT':
            # 限价单：使用指定价格
            fill_price = order.price
        else:
            # 其他类型：使用当前价格
            fill_price = current_price

        return fill_price

    def _calculate_commission(self, quantity: float, price: float) -> float:
        """
        计算手续费

        Args:
            quantity: 数量
            price: 价格

        Returns:
            手续费金额
        """
        return quantity * price * self.commission_rate
