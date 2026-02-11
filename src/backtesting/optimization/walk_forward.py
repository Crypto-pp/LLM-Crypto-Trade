"""
Walk-Forward分析器

滚动窗口优化和验证，防止过拟合
"""

import logging
from typing import Dict, List, Callable, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class WalkForwardAnalyzer:
    """
    Walk-Forward分析器

    使用滚动窗口进行样本内优化和样本外验证
    """

    def __init__(
        self,
        backtest_func: Callable,
        optimize_func: Callable,
        start_date: datetime,
        end_date: datetime,
        train_period_days: int = 180,
        test_period_days: int = 60,
        metric: str = 'sharpe_ratio'
    ):
        """
        初始化Walk-Forward分析器

        Args:
            backtest_func: 回测函数
            optimize_func: 优化函数
            start_date: 开始日期
            end_date: 结束日期
            train_period_days: 训练期天数
            test_period_days: 测试期天数
            metric: 评估指标
        """
        self.backtest_func = backtest_func
        self.optimize_func = optimize_func
        self.start_date = start_date
        self.end_date = end_date
        self.train_period_days = train_period_days
        self.test_period_days = test_period_days
        self.metric = metric

        self.results = []

        logger.info(f"WalkForwardAnalyzer initialized: "
                   f"train={train_period_days}d, test={test_period_days}d")

    def analyze(self) -> pd.DataFrame:
        """
        执行Walk-Forward分析

        Returns:
            分析结果DataFrame
        """
        logger.info("Starting Walk-Forward analysis...")

        # 生成时间窗口
        windows = self._generate_windows()

        logger.info(f"Generated {len(windows)} windows")

        # 对每个窗口进行优化和测试
        for i, (train_start, train_end, test_start, test_end) in enumerate(windows):
            logger.info(f"Window {i+1}/{len(windows)}: "
                       f"Train [{train_start.date()} to {train_end.date()}], "
                       f"Test [{test_start.date()} to {test_end.date()}]")

            # 样本内优化
            best_params = self.optimize_func(
                start_date=train_start,
                end_date=train_end
            )

            # 样本外测试
            test_result = self.backtest_func(
                start_date=test_start,
                end_date=test_end,
                **best_params
            )

            # 记录结果
            self.results.append({
                'window': i + 1,
                'train_start': train_start,
                'train_end': train_end,
                'test_start': test_start,
                'test_end': test_end,
                'best_params': best_params,
                'test_metrics': test_result.get('metrics', {})
            })

        # 生成汇总报告
        summary = self._generate_summary()

        logger.info("Walk-Forward analysis completed")
        return summary

    def _generate_windows(self) -> List[Tuple]:
        """生成时间窗口"""
        windows = []
        current_date = self.start_date

        while current_date + timedelta(days=self.train_period_days + self.test_period_days) <= self.end_date:
            train_start = current_date
            train_end = current_date + timedelta(days=self.train_period_days)
            test_start = train_end
            test_end = test_start + timedelta(days=self.test_period_days)

            windows.append((train_start, train_end, test_start, test_end))

            # 移动到下一个窗口
            current_date = test_start

        return windows

    def _generate_summary(self) -> pd.DataFrame:
        """生成汇总报告"""
        summary_data = []

        for result in self.results:
            metrics = result['test_metrics']
            row = {
                'window': result['window'],
                'test_start': result['test_start'],
                'test_end': result['test_end']
            }

            # 提取关键指标
            for category in ['return_metrics', 'risk_metrics', 'risk_adjusted_metrics', 'trading_metrics']:
                if category in metrics:
                    for key, value in metrics[category].items():
                        if isinstance(value, (int, float)):
                            row[key] = value

            summary_data.append(row)

        return pd.DataFrame(summary_data)

    def get_overall_performance(self) -> Dict:
        """获取整体表现"""
        summary = self._generate_summary()

        if len(summary) == 0:
            return {}

        return {
            'avg_return': summary['annualized_return'].mean(),
            'avg_sharpe': summary['sharpe_ratio'].mean(),
            'avg_max_drawdown': summary['max_drawdown'].mean(),
            'win_rate': (summary['annualized_return'] > 0).sum() / len(summary) * 100,
            'total_windows': len(summary)
        }
