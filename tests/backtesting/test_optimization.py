"""
参数优化测试
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.backtesting.optimization.grid_search import GridSearchOptimizer


class TestOptimization(unittest.TestCase):
    """测试参数优化"""

    def setUp(self):
        """设置测试数据"""
        # 定义简单的回测函数
        def simple_backtest(param1, param2):
            # 模拟回测结果
            sharpe = 2.0 - abs(param1 - 15) * 0.1 - abs(param2 - 30) * 0.05
            return {
                'metrics': {
                    'risk_adjusted_metrics': {
                        'sharpe_ratio': max(0, sharpe)
                    },
                    'return_metrics': {
                        'annualized_return': 50.0
                    }
                }
            }

        self.backtest_func = simple_backtest

    def test_grid_search(self):
        """测试网格搜索"""
        param_grid = {
            'param1': [10, 15, 20],
            'param2': [20, 30, 40]
        }

        optimizer = GridSearchOptimizer(
            backtest_func=self.backtest_func,
            param_grid=param_grid,
            metric='sharpe_ratio',
            n_jobs=1
        )

        results = optimizer.optimize()

        # 验证结果
        self.assertEqual(len(results), 9)  # 3 * 3 = 9 组合
        self.assertIn('sharpe_ratio', results.columns)

        # 验证最优参数
        best_params = optimizer.get_best_params()
        self.assertIn('param1', best_params)
        self.assertIn('param2', best_params)


if __name__ == '__main__':
    unittest.main()
