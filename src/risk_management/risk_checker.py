"""
风险检查器
实现单笔风险、账户风险、最大回撤、连续亏损检查
"""

from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RiskChecker:
    """
    风险检查器
    """

    def __init__(
        self,
        account_balance: float,
        max_risk_per_trade: float = 0.03,
        max_daily_loss: float = 0.05,
        max_drawdown: float = 0.20,
        max_consecutive_losses: int = 5
    ):
        """
        初始化风险检查器

        Args:
            account_balance: 账户余额
            max_risk_per_trade: 单笔最大风险
            max_daily_loss: 单日最大亏损
            max_drawdown: 最大回撤
            max_consecutive_losses: 最大连续亏损次数
        """
        self.account_balance = account_balance
        self.peak_balance = account_balance
        self.max_risk_per_trade = max_risk_per_trade
        self.max_daily_loss = max_daily_loss
        self.max_drawdown = max_drawdown
        self.max_consecutive_losses = max_consecutive_losses

        self.daily_loss = 0
        self.consecutive_losses = 0
        self.trade_history = []

        logger.info("风险检查器已初始化")

    def check_single_trade_risk(
        self,
        entry_price: float,
        stop_loss: float,
        position_size: float
    ) -> Dict[str, any]:
        """
        检查单笔交易风险

        Returns:
            检查结果字典
        """
        try:
            risk_per_unit = abs(entry_price - stop_loss)
            total_risk = risk_per_unit * position_size
            risk_pct = total_risk / self.account_balance

            passed = risk_pct <= self.max_risk_per_trade

            result = {
                'passed': passed,
                'risk_amount': total_risk,
                'risk_percentage': risk_pct,
                'max_allowed': self.max_risk_per_trade,
                'message': 'OK' if passed else f'单笔风险过高: {risk_pct:.2%}'
            }

            if not passed:
                logger.warning(result['message'])

            return result

        except Exception as e:
            logger.error(f"检查单笔风险失败: {e}")
            return {'passed': False, 'message': str(e)}

    def check_daily_loss(self) -> Dict[str, any]:
        """
        检查单日亏损

        Returns:
            检查结果字典
        """
        try:
            daily_loss_pct = self.daily_loss / self.account_balance
            passed = daily_loss_pct <= self.max_daily_loss

            result = {
                'passed': passed,
                'daily_loss': self.daily_loss,
                'daily_loss_pct': daily_loss_pct,
                'max_allowed': self.max_daily_loss,
                'message': 'OK' if passed else f'单日亏损超限: {daily_loss_pct:.2%}'
            }

            if not passed:
                logger.warning(result['message'])

            return result

        except Exception as e:
            logger.error(f"检查单日亏损失败: {e}")
            return {'passed': False, 'message': str(e)}

    def check_drawdown(self) -> Dict[str, any]:
        """
        检查最大回撤

        Returns:
            检查结果字典
        """
        try:
            current_drawdown = (self.peak_balance - self.account_balance) / self.peak_balance
            passed = current_drawdown <= self.max_drawdown

            # 确定风险等级
            if current_drawdown < 0.10:
                level = 'NORMAL'
            elif current_drawdown < 0.15:
                level = 'WARNING'
            elif current_drawdown < 0.20:
                level = 'DANGER'
            else:
                level = 'CRITICAL'

            result = {
                'passed': passed,
                'current_drawdown': current_drawdown,
                'max_allowed': self.max_drawdown,
                'level': level,
                'message': f'回撤: {current_drawdown:.2%} ({level})'
            }

            if not passed:
                logger.error(result['message'])
            elif level != 'NORMAL':
                logger.warning(result['message'])

            return result

        except Exception as e:
            logger.error(f"检查回撤失败: {e}")
            return {'passed': False, 'message': str(e)}

    def check_consecutive_losses(self) -> Dict[str, any]:
        """
        检查连续亏损

        Returns:
            检查结果字典
        """
        try:
            passed = self.consecutive_losses < self.max_consecutive_losses

            result = {
                'passed': passed,
                'consecutive_losses': self.consecutive_losses,
                'max_allowed': self.max_consecutive_losses,
                'message': 'OK' if passed else f'连续亏损{self.consecutive_losses}次'
            }

            if not passed:
                logger.error(result['message'])

            return result

        except Exception as e:
            logger.error(f"检查连续亏损失败: {e}")
            return {'passed': False, 'message': str(e)}

    def check_all(
        self,
        entry_price: float = None,
        stop_loss: float = None,
        position_size: float = None
    ) -> Dict[str, any]:
        """
        执行所有风险检查

        Returns:
            综合检查结果
        """
        results = {
            'passed': True,
            'checks': {}
        }

        # 检查单笔风险
        if entry_price and stop_loss and position_size:
            trade_risk = self.check_single_trade_risk(entry_price, stop_loss, position_size)
            results['checks']['trade_risk'] = trade_risk
            if not trade_risk['passed']:
                results['passed'] = False

        # 检查单日亏损
        daily_loss_check = self.check_daily_loss()
        results['checks']['daily_loss'] = daily_loss_check
        if not daily_loss_check['passed']:
            results['passed'] = False

        # 检查回撤
        drawdown_check = self.check_drawdown()
        results['checks']['drawdown'] = drawdown_check
        if not drawdown_check['passed']:
            results['passed'] = False

        # 检查连续亏损
        consecutive_check = self.check_consecutive_losses()
        results['checks']['consecutive_losses'] = consecutive_check
        if not consecutive_check['passed']:
            results['passed'] = False

        return results

    def record_trade(self, profit: float):
        """
        记录交易结果

        Args:
            profit: 盈亏金额
        """
        self.trade_history.append({
            'timestamp': datetime.now(),
            'profit': profit
        })

        # 更新账户余额
        self.account_balance += profit

        # 更新峰值
        if self.account_balance > self.peak_balance:
            self.peak_balance = self.account_balance

        # 更新单日亏损
        if profit < 0:
            self.daily_loss += abs(profit)
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

        logger.info(f"记录交易: 盈亏={profit}, 余额={self.account_balance}")

    def reset_daily_loss(self):
        """重置单日亏损（每日开始时调用）"""
        self.daily_loss = 0
        logger.info("单日亏损已重置")

    def update_balance(self, new_balance: float):
        """更新账户余额"""
        self.account_balance = new_balance
        if new_balance > self.peak_balance:
            self.peak_balance = new_balance
        logger.info(f"账户余额已更新: {new_balance}")
