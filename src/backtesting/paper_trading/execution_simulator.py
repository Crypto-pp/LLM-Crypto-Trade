"""
执行模拟器

模拟真实的订单执行过程
"""

import logging
from typing import Dict, Optional
import random

logger = logging.getLogger(__name__)


class ExecutionSimulator:
    """
    执行模拟器

    模拟订单簿、成交延迟、滑点、部分成交等
    """

    def __init__(
        self,
        latency_ms: int = 100,
        partial_fill_prob: float = 0.1
    ):
        """
        初始化执行模拟器

        Args:
            latency_ms: 成交延迟（毫秒）
            partial_fill_prob: 部分成交概率
        """
        self.latency_ms = latency_ms
        self.partial_fill_prob = partial_fill_prob

        logger.info(f"ExecutionSimulator initialized: latency={latency_ms}ms")

    def simulate_execution(self, order: Dict, market_data: Dict) -> Dict:
        """
        模拟订单执行

        Args:
            order: 订单信息
            market_data: 市场数据

        Returns:
            成交信息
        """
        # 模拟延迟
        # time.sleep(self.latency_ms / 1000.0)

        # 检查是否部分成交
        if random.random() < self.partial_fill_prob:
            fill_quantity = order['quantity'] * random.uniform(0.5, 0.9)
        else:
            fill_quantity = order['quantity']

        # 计算成交价格（考虑滑点）
        fill_price = self._calculate_fill_price(order, market_data)

        return {
            'filled_quantity': fill_quantity,
            'fill_price': fill_price,
            'status': 'partial' if fill_quantity < order['quantity'] else 'filled'
        }

    def _calculate_fill_price(self, order: Dict, market_data: Dict) -> float:
        """计算成交价格"""
        base_price = market_data['close']

        # 简单的滑点模拟
        if order['side'] == 'BUY':
            return base_price * 1.0005
        else:
            return base_price * 0.9995
