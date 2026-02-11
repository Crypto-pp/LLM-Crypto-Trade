"""
策略管理器
管理多个策略，信号聚合，冲突处理
"""

import pandas as pd
from typing import Dict, List, Optional
import logging

from .base_strategy import BaseStrategy

logger = logging.getLogger(__name__)


class StrategyManager:
    """
    策略管理器
    """

    def __init__(self):
        """初始化策略管理器"""
        self.strategies: Dict[str, BaseStrategy] = {}
        logger.info("策略管理器已初始化")

    def add_strategy(self, strategy: BaseStrategy):
        """添加策略"""
        self.strategies[strategy.name] = strategy
        logger.info(f"添加策略: {strategy.name}")

    def remove_strategy(self, strategy_name: str):
        """移除策略"""
        if strategy_name in self.strategies:
            del self.strategies[strategy_name]
            logger.info(f"移除策略: {strategy_name}")

    def get_strategy(self, strategy_name: str) -> Optional[BaseStrategy]:
        """获取策略"""
        return self.strategies.get(strategy_name)

    def list_strategies(self) -> List[str]:
        """列出所有策略"""
        return list(self.strategies.keys())

    def run_all_strategies(self, data: pd.DataFrame) -> Dict[str, List[Dict]]:
        """
        运行所有启用的策略

        Returns:
            策略名称到信号列表的映射
        """
        all_signals = {}

        for name, strategy in self.strategies.items():
            if not strategy.enabled:
                continue

            try:
                # 分析市场
                analysis = strategy.analyze(data)

                # 生成信号
                signals = strategy.generate_signals(data, analysis)

                all_signals[name] = signals

                logger.info(f"策略 {name} 生成 {len(signals)} 个信号")

            except Exception as e:
                logger.error(f"运行策略 {name} 失败: {e}")
                all_signals[name] = []

        return all_signals

    def aggregate_signals(self, all_signals: Dict[str, List[Dict]]) -> List[Dict]:
        """
        聚合多个策略的信号

        Args:
            all_signals: 策略名称到信号列表的映射

        Returns:
            聚合后的信号列表
        """
        aggregated = []

        # 收集所有信号
        all_signal_list = []
        for strategy_name, signals in all_signals.items():
            for signal in signals:
                signal['source_strategy'] = strategy_name
                all_signal_list.append(signal)

        # 按信号类型分组
        buy_signals = [s for s in all_signal_list if s['signal'] == 'BUY']
        sell_signals = [s for s in all_signal_list if s['signal'] == 'SELL']

        # 处理买入信号
        if buy_signals:
            # 计算平均置信度和强度
            avg_confidence = sum(s['confidence'] for s in buy_signals) / len(buy_signals)
            avg_strength = sum(s['strength'] for s in buy_signals) / len(buy_signals)

            aggregated_buy = {
                'signal': 'BUY',
                'entry_price': buy_signals[0]['entry_price'],
                'stop_loss': buy_signals[0]['stop_loss'],
                'take_profit': buy_signals[0]['take_profit'],
                'confidence': avg_confidence,
                'strength': avg_strength,
                'supporting_strategies': len(buy_signals),
                'strategies': [s['source_strategy'] for s in buy_signals],
                'reason': f"{len(buy_signals)}个策略支持买入"
            }
            aggregated.append(aggregated_buy)

        # 处理卖出信号
        if sell_signals:
            avg_confidence = sum(s['confidence'] for s in sell_signals) / len(sell_signals)
            avg_strength = sum(s['strength'] for s in sell_signals) / len(sell_signals)

            aggregated_sell = {
                'signal': 'SELL',
                'entry_price': sell_signals[0]['entry_price'],
                'stop_loss': sell_signals[0]['stop_loss'],
                'take_profit': sell_signals[0]['take_profit'],
                'confidence': avg_confidence,
                'strength': avg_strength,
                'supporting_strategies': len(sell_signals),
                'strategies': [s['source_strategy'] for s in sell_signals],
                'reason': f"{len(sell_signals)}个策略支持卖出"
            }
            aggregated.append(aggregated_sell)

        # 处理冲突（同时有买入和卖出信号）
        if buy_signals and sell_signals:
            logger.warning("检测到信号冲突：同时存在买入和卖出信号")
            # 保留置信度更高的信号
            if avg_confidence > sum(s['confidence'] for s in sell_signals) / len(sell_signals):
                aggregated = [aggregated[0]]  # 保留买入
            else:
                aggregated = [aggregated[1]]  # 保留卖出

        return aggregated
