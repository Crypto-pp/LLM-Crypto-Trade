"""
实时性能监控器

监控模拟交易的实时性能
"""

import logging
from typing import Dict, List
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    实时性能监控器

    实时计算和监控性能指标
    """

    def __init__(self, initial_capital: float):
        """
        初始化性能监控器

        Args:
            initial_capital: 初始资金
        """
        self.initial_capital = initial_capital
        self.equity_history = []
        self.trade_history = []

        logger.info("PerformanceMonitor initialized")

    def update(self, equity: float, timestamp: datetime) -> None:
        """
        更新权益数据

        Args:
            equity: 当前权益
            timestamp: 时间戳
        """
        self.equity_history.append({
            'timestamp': timestamp,
            'equity': equity
        })

    def add_trade(self, trade: Dict) -> None:
        """
        添加交易记录

        Args:
            trade: 交易信息
        """
        self.trade_history.append(trade)

    def get_current_metrics(self) -> Dict:
        """
        获取当前性能指标

        Returns:
            性能指标字典
        """
        if len(self.equity_history) == 0:
            return {}

        df = pd.DataFrame(self.equity_history)
        current_equity = df['equity'].iloc[-1]

        # 计算收益率
        total_return = (current_equity / self.initial_capital - 1) * 100

        # 计算最大回撤
        cummax = df['equity'].cummax()
        drawdown = (cummax - df['equity']) / cummax * 100
        max_drawdown = drawdown.max()

        # 计算胜率
        if len(self.trade_history) > 0:
            winning_trades = sum(1 for t in self.trade_history if t.get('pnl', 0) > 0)
            win_rate = (winning_trades / len(self.trade_history)) * 100
        else:
            win_rate = 0.0

        return {
            'current_equity': current_equity,
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'total_trades': len(self.trade_history),
            'win_rate': win_rate
        }

    def check_alerts(self) -> List[str]:
        """
        检查告警条件

        Returns:
            告警信息列表
        """
        alerts = []
        metrics = self.get_current_metrics()

        # 检查回撤
        if metrics.get('max_drawdown', 0) > 20:
            alerts.append(f"WARNING: 最大回撤超过20%: {metrics['max_drawdown']:.2f}%")

        # 检查亏损
        if metrics.get('total_return', 0) < -10:
            alerts.append(f"WARNING: 总亏损超过10%: {metrics['total_return']:.2f}%")

        return alerts
