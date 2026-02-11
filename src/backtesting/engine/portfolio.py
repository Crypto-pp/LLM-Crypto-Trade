"""
投资组合管理

负责：
- 持仓管理
- 资金管理
- 盈亏计算
- 权益曲线生成
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

from .event_engine import FillEvent, SignalEvent, OrderEvent

logger = logging.getLogger(__name__)


class Position:
    """持仓信息"""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.quantity = 0.0
        self.avg_price = 0.0
        self.total_cost = 0.0
        self.realized_pnl = 0.0
        self.entry_time = None

    def update(self, fill: FillEvent) -> None:
        """更新持仓"""
        if fill.side == 'BUY':
            # 买入
            new_quantity = self.quantity + fill.quantity
            self.total_cost += fill.total_cost
            if new_quantity > 0:
                self.avg_price = self.total_cost / new_quantity
            self.quantity = new_quantity
            if self.entry_time is None:
                self.entry_time = fill.timestamp
        else:
            # 卖出
            if self.quantity > 0:
                # 计算已实现盈亏
                pnl = (fill.fill_price - self.avg_price) * fill.quantity - fill.commission
                self.realized_pnl += pnl
            self.quantity -= fill.quantity
            if self.quantity <= 0:
                self.quantity = 0
                self.avg_price = 0
                self.total_cost = 0
                self.entry_time = None

    def get_unrealized_pnl(self, current_price: float) -> float:
        """计算未实现盈亏"""
        if self.quantity > 0:
            return (current_price - self.avg_price) * self.quantity
        return 0.0

    def get_market_value(self, current_price: float) -> float:
        """计算市值"""
        return self.quantity * current_price


class Portfolio:
    """
    投资组合管理器

    管理账户资金、持仓、交易记录等
    """

    def __init__(self, initial_capital: float):
        """
        初始化投资组合

        Args:
            initial_capital: 初始资金
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Dict] = []
        self.equity_curve: List[Dict] = []

        logger.info(f"Portfolio initialized with capital: {initial_capital}")

    def update_fill(self, fill: FillEvent) -> None:
        """
        更新成交信息

        Args:
            fill: 成交事件
        """
        # 获取或创建持仓
        if fill.symbol not in self.positions:
            self.positions[fill.symbol] = Position(fill.symbol)

        position = self.positions[fill.symbol]
        old_quantity = position.quantity
        # 平仓前保存入场数据，因为 position.update 会重置这些字段
        entry_price = position.avg_price
        entry_time = position.entry_time

        # 更新持仓
        position.update(fill)

        # 更新现金
        if fill.side == 'BUY':
            self.cash -= fill.total_cost
        else:
            self.cash += fill.fill_cost - fill.commission

        # 记录交易
        if old_quantity > 0 and position.quantity == 0:
            # 平仓交易，使用保存的入场数据
            self._record_trade(fill, entry_price, entry_time, old_quantity)

        logger.debug(f"Portfolio updated: cash={self.cash:.2f}, "
                    f"position={position.quantity}")

    def _record_trade(
        self, fill: FillEvent,
        entry_price: float, entry_time, quantity: float,
    ) -> None:
        """
        记录完整交易

        Args:
            fill: 平仓成交事件
            entry_price: 入场均价（update 前保存）
            entry_time: 入场时间（update 前保存）
            quantity: 平仓数量
        """
        pnl = (fill.fill_price - entry_price) * quantity - fill.commission
        cost = entry_price * quantity
        pnl_pct = (pnl / cost * 100) if cost > 0 else 0.0

        trade = {
            'symbol': fill.symbol,
            'entry_time': entry_time,
            'exit_time': fill.timestamp,
            'quantity': quantity,
            'entry_price': entry_price,
            'exit_price': fill.fill_price,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
        }
        self.trades.append(trade)
        logger.info(f"Trade recorded: {trade}")

    def update_equity(self, timestamp: datetime, prices: Dict[str, float]) -> None:
        """
        更新权益曲线

        Args:
            timestamp: 时间戳
            prices: 当前价格字典 {symbol: price}
        """
        # 计算持仓市值
        holdings_value = sum(
            pos.get_market_value(prices.get(symbol, 0))
            for symbol, pos in self.positions.items()
        )

        # 计算总权益
        total_equity = self.cash + holdings_value

        # 记录权益曲线
        self.equity_curve.append({
            'timestamp': timestamp,
            'equity': total_equity,
            'cash': self.cash,
            'holdings': holdings_value
        })

    def get_current_equity(self, prices: Dict[str, float]) -> float:
        """获取当前权益"""
        holdings_value = sum(
            pos.get_market_value(prices.get(symbol, 0))
            for symbol, pos in self.positions.items()
        )
        return self.cash + holdings_value

    def get_position(self, symbol: str) -> Optional[Position]:
        """获取持仓"""
        return self.positions.get(symbol)

    def has_position(self, symbol: str) -> bool:
        """检查是否有持仓"""
        pos = self.positions.get(symbol)
        return pos is not None and pos.quantity > 0

    def get_equity_curve_df(self) -> pd.DataFrame:
        """获取权益曲线DataFrame"""
        return pd.DataFrame(self.equity_curve)

    def get_trades_df(self) -> pd.DataFrame:
        """获取交易记录DataFrame"""
        return pd.DataFrame(self.trades)

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            'initial_capital': self.initial_capital,
            'current_cash': self.cash,
            'total_trades': len(self.trades),
            'positions_count': len([p for p in self.positions.values() if p.quantity > 0])
        }
