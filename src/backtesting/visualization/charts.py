"""
图表生成器

生成各种回测分析图表
"""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import pandas as pd
import numpy as np
from typing import Optional, Dict, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ChartGenerator:
    """
    图表生成器

    生成回测分析所需的各种图表
    """

    def __init__(self, output_dir: str = "charts"):
        """
        初始化图表生成器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        logger.info(f"ChartGenerator initialized, output_dir: {self.output_dir}")

    def plot_equity_curve(
        self,
        equity_curve: pd.DataFrame,
        title: str = "Equity Curve",
        filename: str = "equity_curve.png"
    ) -> str:
        """
        绘制权益曲线

        Args:
            equity_curve: 权益曲线DataFrame
            title: 图表标题
            filename: 文件名

        Returns:
            保存的文件路径
        """
        plt.figure(figsize=(12, 6))

        plt.plot(equity_curve['timestamp'], equity_curve['equity'],
                label='Equity', linewidth=2, color='#2E86AB')

        # 添加初始资金线
        initial_capital = equity_curve['equity'].iloc[0]
        plt.axhline(y=initial_capital, color='red', linestyle='--',
                   label='Initial Capital', alpha=0.5)

        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Equity (USDT)', fontsize=12)
        plt.title(title, fontsize=14, fontweight='bold')
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Equity curve saved to {filepath}")
        return str(filepath)

    def plot_drawdown_curve(
        self,
        equity_curve: pd.DataFrame,
        filename: str = "drawdown_curve.png"
    ) -> str:
        """
        绘制回撤曲线

        Args:
            equity_curve: 权益曲线DataFrame
            filename: 文件名

        Returns:
            保存的文件路径
        """
        # 计算回撤
        equity = equity_curve['equity']
        cummax = equity.cummax()
        drawdown = (cummax - equity) / cummax * 100

        plt.figure(figsize=(12, 6))

        plt.fill_between(equity_curve['timestamp'], 0, drawdown,
                        color='red', alpha=0.3, label='Drawdown')
        plt.plot(equity_curve['timestamp'], drawdown,
                color='red', linewidth=1)

        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Drawdown (%)', fontsize=12)
        plt.title('Drawdown Curve', fontsize=14, fontweight='bold')
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Drawdown curve saved to {filepath}")
        return str(filepath)

    def plot_monthly_returns(
        self,
        monthly_returns: pd.Series,
        filename: str = "monthly_returns.png"
    ) -> str:
        """
        绘制月度收益柱状图

        Args:
            monthly_returns: 月度收益率Series
            filename: 文件名

        Returns:
            保存的文件路径
        """
        plt.figure(figsize=(14, 6))

        colors = ['green' if x > 0 else 'red' for x in monthly_returns]
        plt.bar(range(len(monthly_returns)), monthly_returns, color=colors, alpha=0.7)

        plt.xlabel('Month', fontsize=12)
        plt.ylabel('Return (%)', fontsize=12)
        plt.title('Monthly Returns', fontsize=14, fontweight='bold')
        plt.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()

        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Monthly returns chart saved to {filepath}")
        return str(filepath)

    def plot_trades(
        self,
        price_data: pd.DataFrame,
        trades: List[Dict],
        filename: str = "trades.png"
    ) -> str:
        """
        绘制交易标记图

        Args:
            price_data: 价格数据DataFrame
            trades: 交易记录列表
            filename: 文件名

        Returns:
            保存的文件路径
        """
        plt.figure(figsize=(14, 8))

        # 绘制价格曲线
        plt.plot(price_data['timestamp'], price_data['close'],
                label='Price', linewidth=1, color='blue', alpha=0.7)

        # 标记买入点
        for trade in trades:
            entry_time = trade['entry_time']
            exit_time = trade['exit_time']

            # 找到对应的价格
            entry_price = trade.get('entry_price', 0)
            exit_price = trade.get('exit_price', 0)

            # 买入标记
            plt.scatter(entry_time, entry_price, color='green',
                       marker='^', s=100, alpha=0.8, zorder=5)

            # 卖出标记
            plt.scatter(exit_time, exit_price, color='red',
                       marker='v', s=100, alpha=0.8, zorder=5)

        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Price', fontsize=12)
        plt.title('Trading Signals', fontsize=14, fontweight='bold')
        plt.legend(['Price', 'Buy', 'Sell'], fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Trades chart saved to {filepath}")
        return str(filepath)

    def plot_performance_summary(
        self,
        metrics: Dict,
        filename: str = "performance_summary.png"
    ) -> str:
        """
        绘制性能摘要图

        Args:
            metrics: 性能指标字典
            filename: 文件名

        Returns:
            保存的文件路径
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # 1. 收益指标
        ax1 = axes[0, 0]
        return_metrics = metrics.get('return_metrics', {})
        labels = ['Total\nReturn', 'Annualized\nReturn']
        values = [
            return_metrics.get('total_return', 0),
            return_metrics.get('annualized_return', 0)
        ]
        colors = ['green' if v > 0 else 'red' for v in values]
        ax1.bar(labels, values, color=colors, alpha=0.7)
        ax1.set_title('Return Metrics', fontweight='bold')
        ax1.set_ylabel('Return (%)')
        ax1.grid(True, alpha=0.3, axis='y')

        # 2. 风险指标
        ax2 = axes[0, 1]
        risk_metrics = metrics.get('risk_metrics', {})
        labels = ['Max\nDrawdown', 'Volatility']
        values = [
            risk_metrics.get('max_drawdown', 0),
            risk_metrics.get('volatility', 0)
        ]
        ax2.bar(labels, values, color='orange', alpha=0.7)
        ax2.set_title('Risk Metrics', fontweight='bold')
        ax2.set_ylabel('Percentage (%)')
        ax2.grid(True, alpha=0.3, axis='y')

        # 3. 风险调整收益
        ax3 = axes[1, 0]
        risk_adj_metrics = metrics.get('risk_adjusted_metrics', {})
        labels = ['Sharpe', 'Sortino', 'Calmar']
        values = [
            risk_adj_metrics.get('sharpe_ratio', 0),
            risk_adj_metrics.get('sortino_ratio', 0),
            risk_adj_metrics.get('calmar_ratio', 0)
        ]
        ax3.bar(labels, values, color='purple', alpha=0.7)
        ax3.set_title('Risk-Adjusted Returns', fontweight='bold')
        ax3.set_ylabel('Ratio')
        ax3.grid(True, alpha=0.3, axis='y')

        # 4. 交易指标
        ax4 = axes[1, 1]
        trading_metrics = metrics.get('trading_metrics', {})
        labels = ['Win Rate', 'P/L Ratio']
        values = [
            trading_metrics.get('win_rate', 0),
            trading_metrics.get('profit_loss_ratio', 0) * 10  # 缩放以便显示
        ]
        ax4.bar(labels, values, color='teal', alpha=0.7)
        ax4.set_title('Trading Metrics', fontweight='bold')
        ax4.set_ylabel('Value')
        ax4.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()

        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        logger.info(f"Performance summary saved to {filepath}")
        return str(filepath)
