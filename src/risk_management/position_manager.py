"""
仓位管理模块
实现固定比例法、凯利公式法、波动率调整法等仓位计算方法
"""

import pandas as pd
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PositionManager:
    """
    仓位管理器
    """

    def __init__(self, account_balance: float):
        """
        初始化仓位管理器

        Args:
            account_balance: 账户余额
        """
        self.account_balance = account_balance
        logger.info(f"仓位管理器已初始化，账户余额: {account_balance}")

    def calculate_fixed_ratio(
        self,
        entry_price: float,
        stop_loss: float,
        risk_per_trade: float = 0.02
    ) -> float:
        """
        固定比例法计算仓位

        Args:
            entry_price: 入场价格
            stop_loss: 止损价格
            risk_per_trade: 单笔风险比例（默认2%）

        Returns:
            仓位大小
        """
        try:
            risk_amount = self.account_balance * risk_per_trade
            risk_per_unit = abs(entry_price - stop_loss)

            if risk_per_unit == 0:
                return 0

            position_size = risk_amount / risk_per_unit

            logger.info(f"固定比例法计算仓位: {position_size}")
            return position_size

        except Exception as e:
            logger.error(f"计算仓位失败: {e}")
            return 0

    def calculate_kelly(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        kelly_fraction: float = 0.25
    ) -> float:
        """
        凯利公式法计算仓位比例

        Args:
            win_rate: 胜率
            avg_win: 平均盈利
            avg_loss: 平均亏损
            kelly_fraction: 凯利分数（默认1/4凯利）

        Returns:
            仓位比例（0-1）
        """
        try:
            if avg_loss == 0:
                return 0

            win_loss_ratio = avg_win / avg_loss
            kelly_pct = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio

            # 使用分数凯利更保守
            kelly_pct = max(0, min(kelly_pct * kelly_fraction, 0.25))

            logger.info(f"凯利公式计算仓位比例: {kelly_pct:.2%}")
            return kelly_pct

        except Exception as e:
            logger.error(f"凯利公式计算失败: {e}")
            return 0

    def calculate_volatility_adjusted(
        self,
        base_position_pct: float,
        current_volatility: float,
        standard_volatility: float = 0.05
    ) -> float:
        """
        波动率调整法计算仓位

        Args:
            base_position_pct: 基础仓位比例
            current_volatility: 当前波动率
            standard_volatility: 标准波动率

        Returns:
            调整后的仓位比例
        """
        try:
            if current_volatility == 0:
                return base_position_pct

            volatility_ratio = standard_volatility / current_volatility
            adjusted_pct = base_position_pct * volatility_ratio

            # 限制在合理范围内
            adjusted_pct = max(0.05, min(adjusted_pct, 0.50))

            logger.info(f"波动率调整后仓位比例: {adjusted_pct:.2%}")
            return adjusted_pct

        except Exception as e:
            logger.error(f"波动率调整计算失败: {e}")
            return base_position_pct

    def calculate_pyramid_position(
        self,
        initial_position: float,
        profit_pct: float,
        max_additions: int = 3
    ) -> Optional[float]:
        """
        金字塔加仓计算

        Args:
            initial_position: 初始仓位
            profit_pct: 当前盈利百分比
            max_additions: 最大加仓次数

        Returns:
            加仓大小，如果不应加仓则返回None
        """
        try:
            # 加仓阈值
            thresholds = [0.05, 0.10, 0.15]  # 5%, 10%, 15%盈利时加仓
            additions = [0.25, 0.20, 0.15]  # 加仓比例递减

            for i, threshold in enumerate(thresholds):
                if i >= max_additions:
                    break

                if profit_pct >= threshold:
                    add_size = initial_position * additions[i]
                    logger.info(f"触发加仓: 盈利{profit_pct:.2%}, 加仓{add_size}")
                    return add_size

            return None

        except Exception as e:
            logger.error(f"金字塔加仓计算失败: {e}")
            return None

    def update_balance(self, new_balance: float):
        """更新账户余额"""
        self.account_balance = new_balance
        logger.info(f"账户余额已更新: {new_balance}")
