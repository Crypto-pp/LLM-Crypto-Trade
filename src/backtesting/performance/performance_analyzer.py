"""
性能分析器

提供完整的性能分析功能：
- 生成权益曲线
- 生成回撤曲线
- 月度收益分析
- 交易记录分析
- 风险分析
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

from .metrics_calculator import MetricsCalculator

logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """
    性能分析器

    分析回测结果并生成详细报告
    """

    def __init__(
        self,
        initial_capital: float,
        equity_curve: pd.DataFrame,
        trades: List[Dict],
        risk_free_rate: float = 0.0
    ):
        """
        初始化性能分析器

        Args:
            initial_capital: 初始资金
            equity_curve: 权益曲线DataFrame
            trades: 交易记录列表
            risk_free_rate: 无风险利率
        """
        self.initial_capital = initial_capital
        self.equity_curve = equity_curve
        self.trades = trades
        self.risk_free_rate = risk_free_rate

        # 创建指标计算器
        self.calculator = MetricsCalculator(
            initial_capital, equity_curve, trades, risk_free_rate
        )

        logger.info("PerformanceAnalyzer initialized")

    def analyze(self) -> Dict:
        """
        执行完整分析

        Returns:
            分析结果字典
        """
        # 计算所有指标
        metrics = self.calculator.calculate_all_metrics()

        # 生成分析报告
        report = {
            'summary': self._generate_summary(metrics),
            'metrics': metrics,
            'rating': self._calculate_rating(metrics),
            'analysis': self._generate_analysis(metrics)
        }

        return report

    def _generate_summary(self, metrics: Dict) -> Dict:
        """生成摘要"""
        return {
            'initial_capital': self.initial_capital,
            'final_capital': metrics['return_metrics']['final_capital'],
            'total_return': metrics['return_metrics']['total_return'],
            'annualized_return': metrics['return_metrics']['annualized_return'],
            'max_drawdown': metrics['risk_metrics']['max_drawdown'],
            'sharpe_ratio': metrics['risk_adjusted_metrics']['sharpe_ratio'],
            'win_rate': metrics['trading_metrics']['win_rate'],
            'total_trades': metrics['trading_metrics']['total_trades']
        }

    def _calculate_rating(self, metrics: Dict) -> Dict:
        """
        计算策略评分

        Returns:
            评分结果
        """
        # 收益评分
        annualized_return = metrics['return_metrics']['annualized_return']
        return_score = self._score_return(annualized_return)

        # 风险评分
        max_drawdown = metrics['risk_metrics']['max_drawdown']
        risk_score = self._score_risk(max_drawdown)

        # 稳定性评分
        sharpe_ratio = metrics['risk_adjusted_metrics']['sharpe_ratio']
        stability_score = self._score_stability(sharpe_ratio)

        # 交易评分
        win_rate = metrics['trading_metrics']['win_rate']
        pl_ratio = metrics['trading_metrics']['profit_loss_ratio']
        trading_score = self._score_trading(win_rate, pl_ratio)

        # 综合评分
        weights = {'return': 0.30, 'risk': 0.30, 'stability': 0.25, 'trading': 0.15}
        total_score = (
            return_score * weights['return'] +
            risk_score * weights['risk'] +
            stability_score * weights['stability'] +
            trading_score * weights['trading']
        )

        # 评级
        rating = self._get_rating(total_score)

        return {
            'total_score': round(total_score, 2),
            'rating': rating,
            'component_scores': {
                'return': round(return_score, 2),
                'risk': round(risk_score, 2),
                'stability': round(stability_score, 2),
                'trading': round(trading_score, 2)
            }
        }

    def _score_return(self, annualized_return: float) -> float:
        """收益评分 (0-100)"""
        if annualized_return >= 100:
            return 100
        elif annualized_return >= 50:
            return 80 + (annualized_return - 50) / 50 * 20
        elif annualized_return >= 20:
            return 60 + (annualized_return - 20) / 30 * 20
        elif annualized_return >= 0:
            return 40 + annualized_return / 20 * 20
        else:
            return max(0, 40 + annualized_return / 50 * 40)

    def _score_risk(self, max_drawdown: float) -> float:
        """风险评分 (0-100)"""
        if max_drawdown < 10:
            return 100
        elif max_drawdown < 20:
            return 100 - (max_drawdown - 10) / 10 * 20
        elif max_drawdown < 30:
            return 80 - (max_drawdown - 20) / 10 * 20
        elif max_drawdown < 50:
            return 60 - (max_drawdown - 30) / 20 * 20
        else:
            return max(0, 40 - (max_drawdown - 50) / 50 * 40)

    def _score_stability(self, sharpe_ratio: float) -> float:
        """稳定性评分 (0-100)"""
        if sharpe_ratio >= 2.0:
            return 100
        elif sharpe_ratio >= 1.5:
            return 80 + (sharpe_ratio - 1.5) / 0.5 * 20
        elif sharpe_ratio >= 1.0:
            return 60 + (sharpe_ratio - 1.0) / 0.5 * 20
        elif sharpe_ratio >= 0.5:
            return 40 + (sharpe_ratio - 0.5) / 0.5 * 20
        else:
            return max(0, sharpe_ratio / 0.5 * 40)

    def _score_trading(self, win_rate: float, pl_ratio: float) -> float:
        """交易评分 (0-100)"""
        # 胜率评分
        if win_rate >= 60:
            win_score = 100
        elif win_rate >= 50:
            win_score = 80 + (win_rate - 50) / 10 * 20
        elif win_rate >= 40:
            win_score = 60 + (win_rate - 40) / 10 * 20
        else:
            win_score = max(0, win_rate / 40 * 60)

        # 盈亏比评分
        if pl_ratio >= 3.0:
            pl_score = 100
        elif pl_ratio >= 2.0:
            pl_score = 80 + (pl_ratio - 2.0) / 1.0 * 20
        elif pl_ratio >= 1.5:
            pl_score = 60 + (pl_ratio - 1.5) / 0.5 * 20
        elif pl_ratio >= 1.0:
            pl_score = 40 + (pl_ratio - 1.0) / 0.5 * 20
        else:
            pl_score = max(0, pl_ratio / 1.0 * 40)

        return win_score * 0.5 + pl_score * 0.5

    def _get_rating(self, score: float) -> str:
        """获取评级"""
        if score >= 80:
            return 'A'
        elif score >= 60:
            return 'B'
        elif score >= 40:
            return 'C'
        elif score >= 20:
            return 'D'
        else:
            return 'F'

    def _generate_analysis(self, metrics: Dict) -> Dict:
        """生成分析建议"""
        analysis = {
            'strengths': [],
            'weaknesses': [],
            'recommendations': []
        }

        # 分析收益
        annualized_return = metrics['return_metrics']['annualized_return']
        if annualized_return > 50:
            analysis['strengths'].append(f"优秀的年化收益率: {annualized_return:.2f}%")
        elif annualized_return < 10:
            analysis['weaknesses'].append(f"较低的年化收益率: {annualized_return:.2f}%")
            analysis['recommendations'].append("考虑优化策略参数以提高收益")

        # 分析风险
        max_drawdown = metrics['risk_metrics']['max_drawdown']
        if max_drawdown < 15:
            analysis['strengths'].append(f"良好的风险控制，最大回撤仅 {max_drawdown:.2f}%")
        elif max_drawdown > 30:
            analysis['weaknesses'].append(f"较大的最大回撤: {max_drawdown:.2f}%")
            analysis['recommendations'].append("建议加强止损管理，降低单笔风险")

        # 分析夏普比率
        sharpe_ratio = metrics['risk_adjusted_metrics']['sharpe_ratio']
        if sharpe_ratio > 1.5:
            analysis['strengths'].append(f"优秀的风险调整收益，夏普比率: {sharpe_ratio:.2f}")
        elif sharpe_ratio < 1.0:
            analysis['weaknesses'].append(f"较低的夏普比率: {sharpe_ratio:.2f}")
            analysis['recommendations'].append("需要提高收益或降低波动率")

        # 分析交易
        win_rate = metrics['trading_metrics']['win_rate']
        pl_ratio = metrics['trading_metrics']['profit_loss_ratio']

        if win_rate > 55 and pl_ratio > 2.0:
            analysis['strengths'].append(f"优秀的交易表现: 胜率 {win_rate:.1f}%, 盈亏比 {pl_ratio:.2f}")
        elif win_rate < 40:
            analysis['weaknesses'].append(f"较低的胜率: {win_rate:.1f}%")
            if pl_ratio < 2.0:
                analysis['recommendations'].append("胜率和盈亏比都需要改进")
        elif pl_ratio < 1.5:
            analysis['weaknesses'].append(f"较低的盈亏比: {pl_ratio:.2f}")
            analysis['recommendations'].append("需要提高止盈目标或收紧止损")

        return analysis
