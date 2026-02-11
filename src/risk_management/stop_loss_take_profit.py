"""
止损止盈模块
实现固定百分比、ATR、技术位、移动止盈等方法
"""

import pandas as pd
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class StopLossTakeProfit:
    """
    止损止盈管理器
    """

    def __init__(self):
        """初始化止损止盈管理器"""
        logger.info("止损止盈管理器已初始化")

    def calculate_fixed_percentage(
        self,
        entry_price: float,
        signal_type: str,
        stop_loss_pct: float = 0.05,
        take_profit_pct: float = 0.15
    ) -> Tuple[float, float]:
        """
        固定百分比止损止盈

        Args:
            entry_price: 入场价格
            signal_type: 信号类型 ('BUY' 或 'SELL')
            stop_loss_pct: 止损百分比
            take_profit_pct: 止盈百分比

        Returns:
            (止损价格, 止盈价格)
        """
        try:
            if signal_type == 'BUY':
                stop_loss = entry_price * (1 - stop_loss_pct)
                take_profit = entry_price * (1 + take_profit_pct)
            else:  # SELL
                stop_loss = entry_price * (1 + stop_loss_pct)
                take_profit = entry_price * (1 - take_profit_pct)

            logger.info(f"固定百分比止损止盈: SL={stop_loss}, TP={take_profit}")
            return stop_loss, take_profit

        except Exception as e:
            logger.error(f"计算固定百分比止损止盈失败: {e}")
            return 0, 0

    def calculate_atr_based(
        self,
        entry_price: float,
        atr: float,
        signal_type: str,
        atr_multiplier: float = 2.0
    ) -> Tuple[float, float]:
        """
        基于ATR的止损止盈

        Args:
            entry_price: 入场价格
            atr: ATR值
            signal_type: 信号类型
            atr_multiplier: ATR倍数

        Returns:
            (止损价格, 止盈价格)
        """
        try:
            stop_distance = atr * atr_multiplier

            if signal_type == 'BUY':
                stop_loss = entry_price - stop_distance
                take_profit = entry_price + (stop_distance * 3)  # 1:3风险收益比
            else:  # SELL
                stop_loss = entry_price + stop_distance
                take_profit = entry_price - (stop_distance * 3)

            logger.info(f"ATR止损止盈: SL={stop_loss}, TP={take_profit}")
            return stop_loss, take_profit

        except Exception as e:
            logger.error(f"计算ATR止损止盈失败: {e}")
            return 0, 0

    def calculate_technical_level(
        self,
        entry_price: float,
        support_level: float,
        resistance_level: float,
        signal_type: str
    ) -> Tuple[float, float]:
        """
        基于技术位的止损止盈

        Args:
            entry_price: 入场价格
            support_level: 支撑位
            resistance_level: 阻力位
            signal_type: 信号类型

        Returns:
            (止损价格, 止盈价格)
        """
        try:
            if signal_type == 'BUY':
                # 止损设在支撑位下方
                stop_loss = support_level * 0.98
                # 止盈设在阻力位
                take_profit = resistance_level
            else:  # SELL
                # 止损设在阻力位上方
                stop_loss = resistance_level * 1.02
                # 止盈设在支撑位
                take_profit = support_level

            logger.info(f"技术位止损止盈: SL={stop_loss}, TP={take_profit}")
            return stop_loss, take_profit

        except Exception as e:
            logger.error(f"计算技术位止损止盈失败: {e}")
            return 0, 0

    def calculate_trailing_stop(
        self,
        entry_price: float,
        current_price: float,
        highest_price: float,
        signal_type: str,
        trailing_pct: float = 0.05
    ) -> float:
        """
        计算移动止损

        Args:
            entry_price: 入场价格
            current_price: 当前价格
            highest_price: 最高价格（买入时）或最低价格（卖出时）
            signal_type: 信号类型
            trailing_pct: 回撤百分比

        Returns:
            移动止损价格
        """
        try:
            if signal_type == 'BUY':
                # 价格上涨时，止损跟随上移
                trailing_stop = highest_price * (1 - trailing_pct)
                # 止损不能低于入场价
                trailing_stop = max(trailing_stop, entry_price * 0.95)
            else:  # SELL
                # 价格下跌时，止损跟随下移
                trailing_stop = highest_price * (1 + trailing_pct)
                # 止损不能高于入场价
                trailing_stop = min(trailing_stop, entry_price * 1.05)

            logger.info(f"移动止损: {trailing_stop}")
            return trailing_stop

        except Exception as e:
            logger.error(f"计算移动止损失败: {e}")
            return entry_price

    def calculate_dynamic_stop_profit(
        self,
        entry_price: float,
        current_price: float,
        signal_type: str,
        initial_stop_loss_pct: float = 0.05
    ) -> Tuple[float, float]:
        """
        动态止损止盈（根据盈利情况调整）

        Args:
            entry_price: 入场价格
            current_price: 当前价格
            signal_type: 信号类型
            initial_stop_loss_pct: 初始止损百分比

        Returns:
            (止损价格, 止盈价格)
        """
        try:
            if signal_type == 'BUY':
                profit_pct = (current_price - entry_price) / entry_price
            else:  # SELL
                profit_pct = (entry_price - current_price) / entry_price

            # 根据盈利情况调整止损
            if profit_pct < 0.05:  # 盈利<5%
                stop_loss_pct = initial_stop_loss_pct
                take_profit_pct = 0.10
            elif profit_pct < 0.10:  # 盈利5-10%
                stop_loss_pct = 0  # 移至保本
                take_profit_pct = 0.15
            elif profit_pct < 0.15:  # 盈利10-15%
                stop_loss_pct = -0.05  # 锁定5%利润
                take_profit_pct = 0.20
            else:  # 盈利>15%
                stop_loss_pct = -0.10  # 锁定10%利润
                take_profit_pct = current_price * 0.95  # 使用移动止盈

            if signal_type == 'BUY':
                stop_loss = entry_price * (1 + stop_loss_pct)
                take_profit = entry_price * (1 + take_profit_pct)
            else:
                stop_loss = entry_price * (1 - stop_loss_pct)
                take_profit = entry_price * (1 - take_profit_pct)

            logger.info(f"动态止损止盈: SL={stop_loss}, TP={take_profit}")
            return stop_loss, take_profit

        except Exception as e:
            logger.error(f"计算动态止损止盈失败: {e}")
            return 0, 0
