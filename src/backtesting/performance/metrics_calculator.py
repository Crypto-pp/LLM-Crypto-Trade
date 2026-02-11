"""
指标计算器

实现所有性能指标的计算：
- 收益指标：总收益率、年化收益率、月度收益
- 风险指标：最大回撤、夏普比率、索提诺比率、卡玛比率
- 交易指标：胜率、盈亏比、平均持仓时间、交易频率
- 稳定性指标：收益波动率、月度胜率
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """
    性能指标计算器

    计算回测的所有性能指标
    """

    def __init__(
        self,
        initial_capital: float,
        equity_curve: pd.DataFrame,
        trades: List[Dict],
        risk_free_rate: float = 0.0
    ):
        """
        初始化指标计算器

        Args:
            initial_capital: 初始资金
            equity_curve: 权益曲线DataFrame (timestamp, equity)
            trades: 交易记录列表
            risk_free_rate: 无风险利率（年化）
        """
        self.initial_capital = initial_capital
        self.equity_curve = equity_curve.copy()
        self.trades = trades
        self.risk_free_rate = risk_free_rate

        # 确保时间戳是datetime类型
        if len(self.equity_curve) > 0:
            self.equity_curve['timestamp'] = pd.to_datetime(self.equity_curve['timestamp'])

        logger.info("MetricsCalculator initialized")

    def calculate_all_metrics(self) -> Dict:
        """
        计算所有性能指标

        Returns:
            包含所有指标的字典
        """
        metrics = {
            'return_metrics': self.calculate_return_metrics(),
            'risk_metrics': self.calculate_risk_metrics(),
            'risk_adjusted_metrics': self.calculate_risk_adjusted_metrics(),
            'trading_metrics': self.calculate_trading_metrics(),
            'stability_metrics': self.calculate_stability_metrics()
        }

        return metrics

    def calculate_return_metrics(self) -> Dict:
        """计算收益指标"""
        if len(self.equity_curve) == 0:
            return self._empty_return_metrics()

        final_capital = self.equity_curve['equity'].iloc[-1]

        # 总收益率
        total_return = ((final_capital / self.initial_capital) - 1) * 100

        # 交易天数
        days = (self.equity_curve['timestamp'].iloc[-1] -
                self.equity_curve['timestamp'].iloc[0]).days

        # 年化收益率
        if days > 0:
            years = days / 365.0
            annualized_return = ((final_capital / self.initial_capital) ** (1 / years) - 1) * 100
        else:
            annualized_return = 0.0

        # 日均收益率
        daily_returns = self.equity_curve['equity'].pct_change().dropna()
        avg_daily_return = daily_returns.mean() * 100

        # 月度收益率
        monthly_returns = self._calculate_monthly_returns()

        return {
            'total_return': round(total_return, 2),
            'annualized_return': round(annualized_return, 2),
            'avg_daily_return': round(avg_daily_return, 4),
            'monthly_returns': monthly_returns.to_dict() if len(monthly_returns) > 0 else {},
            'final_capital': round(final_capital, 2),
            'total_pnl': round(final_capital - self.initial_capital, 2)
        }

    def calculate_risk_metrics(self) -> Dict:
        """计算风险指标"""
        if len(self.equity_curve) == 0:
            return self._empty_risk_metrics()

        # 最大回撤
        max_dd_info = self._calculate_max_drawdown()

        # 波动率
        daily_returns = self.equity_curve['equity'].pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(365) * 100

        # 下行波动率
        downside_returns = daily_returns[daily_returns < 0]
        downside_deviation = downside_returns.std() * np.sqrt(365) * 100 if len(downside_returns) > 0 else 0.0

        return {
            'max_drawdown': round(max_dd_info['max_drawdown'], 2),
            'max_drawdown_duration_days': max_dd_info.get('duration_days'),
            'volatility': round(volatility, 2),
            'downside_deviation': round(downside_deviation, 2)
        }

    def calculate_risk_adjusted_metrics(self) -> Dict:
        """计算风险调整收益指标"""
        return_metrics = self.calculate_return_metrics()
        risk_metrics = self.calculate_risk_metrics()

        annualized_return = return_metrics['annualized_return']
        volatility = risk_metrics['volatility']
        downside_deviation = risk_metrics['downside_deviation']
        max_drawdown = risk_metrics['max_drawdown']

        # 夏普比率
        sharpe_ratio = 0.0
        if volatility > 0:
            sharpe_ratio = (annualized_return - self.risk_free_rate) / volatility

        # 索提诺比率
        sortino_ratio = 0.0
        if downside_deviation > 0:
            sortino_ratio = (annualized_return - self.risk_free_rate) / downside_deviation

        # 卡玛比率
        calmar_ratio = 0.0
        if max_drawdown > 0:
            calmar_ratio = annualized_return / max_drawdown

        return {
            'sharpe_ratio': round(sharpe_ratio, 3),
            'sortino_ratio': round(sortino_ratio, 3),
            'calmar_ratio': round(calmar_ratio, 3)
        }

    def calculate_trading_metrics(self) -> Dict:
        """计算交易指标"""
        if len(self.trades) == 0:
            return self._empty_trading_metrics()

        # 分离盈利和亏损交易
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        losing_trades = [t for t in self.trades if t['pnl'] < 0]

        # 胜率
        win_rate = (len(winning_trades) / len(self.trades)) * 100

        # 平均盈亏
        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([abs(t['pnl']) for t in losing_trades]) if losing_trades else 0

        # 盈亏比
        profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0

        # 盈利因子
        total_profit = sum([t['pnl'] for t in winning_trades])
        total_loss = sum([abs(t['pnl']) for t in losing_trades])
        profit_factor = total_profit / total_loss if total_loss > 0 else 0

        # 最大单笔盈亏
        max_win = max([t['pnl'] for t in self.trades]) if self.trades else 0
        max_loss = min([t['pnl'] for t in self.trades]) if self.trades else 0

        # 平均持仓时间
        avg_holding_hours = self._calculate_avg_holding_period()

        return {
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': round(win_rate, 2),
            'profit_loss_ratio': round(profit_loss_ratio, 2),
            'profit_factor': round(profit_factor, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'max_win': round(max_win, 2),
            'max_loss': round(max_loss, 2),
            'avg_holding_hours': round(avg_holding_hours, 2)
        }

    def calculate_stability_metrics(self) -> Dict:
        """计算稳定性指标"""
        if len(self.equity_curve) == 0:
            return self._empty_stability_metrics()

        # 月度胜率
        monthly_returns = self._calculate_monthly_returns()
        winning_months = sum(1 for ret in monthly_returns if ret > 0)
        monthly_win_rate = (winning_months / len(monthly_returns) * 100) if len(monthly_returns) > 0 else 0

        # 最大连续盈亏
        consecutive = self._calculate_consecutive_wins_losses()

        # 收益稳定性（变异系数）
        if len(monthly_returns) > 0 and monthly_returns.mean() != 0:
            stability = monthly_returns.std() / abs(monthly_returns.mean())
        else:
            stability = 0

        return {
            'monthly_win_rate': round(monthly_win_rate, 2),
            'max_consecutive_wins': consecutive['max_consecutive_wins'],
            'max_consecutive_losses': consecutive['max_consecutive_losses'],
            'return_stability': round(stability, 3)
        }

    def _calculate_monthly_returns(self) -> pd.Series:
        """计算月度收益率"""
        if len(self.equity_curve) == 0:
            return pd.Series()

        df = self.equity_curve.copy()
        df.set_index('timestamp', inplace=True)

        # 按月重采样（兼容 pandas 2.1 和 2.2+）
        try:
            monthly_equity = df['equity'].resample('ME').last()
        except ValueError:
            monthly_equity = df['equity'].resample('M').last()
        monthly_returns = monthly_equity.pct_change().dropna() * 100

        return monthly_returns

    def _calculate_max_drawdown(self) -> Dict:
        """计算最大回撤"""
        equity = self.equity_curve['equity'].values
        timestamps = self.equity_curve['timestamp'].values

        # 计算累计最大值
        cummax = pd.Series(equity).cummax()

        # 计算回撤
        drawdown = (cummax - equity) / cummax * 100

        # 最大回撤
        max_dd = drawdown.max()
        max_dd_idx = drawdown.argmax()

        # 峰值时间
        peak_idx = equity[:max_dd_idx+1].argmax()
        peak_time = timestamps[peak_idx]

        # 谷值时间
        trough_time = timestamps[max_dd_idx]

        # 恢复时间
        recovery_time = None
        peak_value = equity[peak_idx]
        for i in range(max_dd_idx + 1, len(equity)):
            if equity[i] >= peak_value:
                recovery_time = timestamps[i]
                break

        # 回撤持续时间
        duration_days = None
        if recovery_time:
            duration_days = (pd.Timestamp(recovery_time) - pd.Timestamp(peak_time)).days

        return {
            'max_drawdown': max_dd,
            'peak_time': peak_time,
            'trough_time': trough_time,
            'recovery_time': recovery_time,
            'duration_days': duration_days
        }

    def _calculate_consecutive_wins_losses(self) -> Dict:
        """计算最大连续盈亏"""
        if len(self.trades) == 0:
            return {'max_consecutive_wins': 0, 'max_consecutive_losses': 0}

        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0

        for trade in self.trades:
            if trade['pnl'] > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            elif trade['pnl'] < 0:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)
            else:
                current_wins = 0
                current_losses = 0

        return {
            'max_consecutive_wins': max_wins,
            'max_consecutive_losses': max_losses
        }

    def _calculate_avg_holding_period(self) -> float:
        """计算平均持仓时间（小时）"""
        if len(self.trades) == 0:
            return 0.0

        total_hours = 0
        for trade in self.trades:
            entry_time = trade['entry_time']
            exit_time = trade['exit_time']
            duration = (exit_time - entry_time).total_seconds() / 3600
            total_hours += duration

        return total_hours / len(self.trades)

    def _empty_return_metrics(self) -> Dict:
        """空收益指标"""
        return {
            'total_return': 0.0,
            'annualized_return': 0.0,
            'avg_daily_return': 0.0,
            'monthly_returns': {},
            'final_capital': self.initial_capital,
            'total_pnl': 0.0
        }

    def _empty_risk_metrics(self) -> Dict:
        """空风险指标"""
        return {
            'max_drawdown': 0.0,
            'max_drawdown_duration_days': None,
            'volatility': 0.0,
            'downside_deviation': 0.0
        }

    def _empty_trading_metrics(self) -> Dict:
        """空交易指标"""
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'profit_loss_ratio': 0.0,
            'profit_factor': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'max_win': 0.0,
            'max_loss': 0.0,
            'avg_holding_hours': 0.0
        }

    def _empty_stability_metrics(self) -> Dict:
        """空稳定性指标"""
        return {
            'monthly_win_rate': 0.0,
            'max_consecutive_wins': 0,
            'max_consecutive_losses': 0,
            'return_stability': 0.0
        }
