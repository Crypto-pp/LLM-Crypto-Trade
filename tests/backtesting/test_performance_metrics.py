"""
性能指标测试
"""

import unittest
from datetime import datetime, timedelta
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.backtesting.performance.metrics_calculator import MetricsCalculator


class TestMetricsCalculator(unittest.TestCase):
    """测试性能指标计算器"""

    def setUp(self):
        """设置测试数据"""
        # 创建模拟权益曲线
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
        equity = [10000 + i * 10 + (i % 10) * 5 for i in range(len(dates))]

        self.equity_curve = pd.DataFrame({
            'timestamp': dates,
            'equity': equity
        })

        # 创建模拟交易记录
        self.trades = [
            {
                'entry_time': datetime(2024, 1, 1),
                'exit_time': datetime(2024, 1, 5),
                'pnl': 100,
                'pnl_pct': 1.0
            },
            {
                'entry_time': datetime(2024, 1, 10),
                'exit_time': datetime(2024, 1, 15),
                'pnl': -50,
                'pnl_pct': -0.5
            },
            {
                'entry_time': datetime(2024, 1, 20),
                'exit_time': datetime(2024, 1, 25),
                'pnl': 150,
                'pnl_pct': 1.5
            }
        ]

        self.calculator = MetricsCalculator(
            initial_capital=10000,
            equity_curve=self.equity_curve,
            trades=self.trades
        )

    def test_return_metrics(self):
        """测试收益指标"""
        metrics = self.calculator.calculate_return_metrics()

        self.assertIn('total_return', metrics)
        self.assertIn('annualized_return', metrics)
        self.assertIn('final_capital', metrics)

        # 验证最终资金
        expected_final = self.equity_curve['equity'].iloc[-1]
        self.assertEqual(metrics['final_capital'], expected_final)

    def test_risk_metrics(self):
        """测试风险指标"""
        metrics = self.calculator.calculate_risk_metrics()

        self.assertIn('max_drawdown', metrics)
        self.assertIn('volatility', metrics)
        self.assertIn('downside_deviation', metrics)

        # 最大回撤应该大于等于0
        self.assertGreaterEqual(metrics['max_drawdown'], 0)

    def test_risk_adjusted_metrics(self):
        """测试风险调整收益指标"""
        metrics = self.calculator.calculate_risk_adjusted_metrics()

        self.assertIn('sharpe_ratio', metrics)
        self.assertIn('sortino_ratio', metrics)
        self.assertIn('calmar_ratio', metrics)

    def test_trading_metrics(self):
        """测试交易指标"""
        metrics = self.calculator.calculate_trading_metrics()

        self.assertIn('total_trades', metrics)
        self.assertIn('win_rate', metrics)
        self.assertIn('profit_loss_ratio', metrics)

        # 验证交易次数
        self.assertEqual(metrics['total_trades'], 3)

        # 验证胜率
        expected_win_rate = (2 / 3) * 100  # 2胜1负
        self.assertAlmostEqual(metrics['win_rate'], expected_win_rate, places=1)

    def test_stability_metrics(self):
        """测试稳定性指标"""
        metrics = self.calculator.calculate_stability_metrics()

        self.assertIn('monthly_win_rate', metrics)
        self.assertIn('max_consecutive_wins', metrics)
        self.assertIn('max_consecutive_losses', metrics)


if __name__ == '__main__':
    unittest.main()
