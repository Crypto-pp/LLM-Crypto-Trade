"""
策略基类
定义所有策略的统一接口
"""

from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class BaseStrategy(ABC):
    """
    策略抽象基类
    所有策略必须继承此类并实现抽象方法
    """

    def __init__(self, name: str, parameters: Dict[str, Any]):
        """
        初始化策略

        Args:
            name: 策略名称
            parameters: 策略参数
        """
        self.name = name
        self.parameters = parameters
        self.enabled = True
        self.state = {}  # 策略状态
        logger.info(f"初始化策略: {name}")

    @abstractmethod
    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        分析市场数据

        Args:
            data: 市场数据

        Returns:
            分析结果字典
        """
        pass

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame, analysis: Dict) -> List[Dict]:
        """
        生成交易信号

        Args:
            data: 市场数据
            analysis: 分析结果

        Returns:
            信号列表
        """
        pass

    def calculate_position_size(
        self,
        signal: Dict,
        account_balance: float,
        risk_per_trade: float = 0.02
    ) -> float:
        """
        计算仓位大小

        Args:
            signal: 交易信号
            account_balance: 账户余额
            risk_per_trade: 单笔风险比例

        Returns:
            仓位大小
        """
        try:
            risk_amount = account_balance * risk_per_trade
            entry_price = signal.get('entry_price', 0)
            stop_loss = signal.get('stop_loss', 0)

            if entry_price == 0 or stop_loss == 0:
                return 0

            risk_per_unit = abs(entry_price - stop_loss)
            position_size = risk_amount / risk_per_unit

            return position_size

        except Exception as e:
            logger.error(f"计算仓位失败: {e}")
            return 0

    def check_risk(self, signal: Dict) -> bool:
        """
        风险检查

        Args:
            signal: 交易信号

        Returns:
            是否通过风险检查
        """
        try:
            # 检查风险收益比
            entry_price = signal.get('entry_price', 0)
            stop_loss = signal.get('stop_loss', 0)
            take_profit = signal.get('take_profit', 0)

            if entry_price == 0 or stop_loss == 0 or take_profit == 0:
                return False

            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)

            risk_reward_ratio = reward / risk if risk > 0 else 0

            # 最小风险收益比为1:2
            if risk_reward_ratio < 2.0:
                logger.warning(f"风险收益比不足: {risk_reward_ratio:.2f}")
                return False

            return True

        except Exception as e:
            logger.error(f"风险检查失败: {e}")
            return False

    def enable(self):
        """启用策略"""
        self.enabled = True
        logger.info(f"策略 {self.name} 已启用")

    def disable(self):
        """禁用策略"""
        self.enabled = False
        logger.info(f"策略 {self.name} 已禁用")

    def update_parameters(self, parameters: Dict[str, Any]):
        """更新策略参数"""
        self.parameters.update(parameters)
        logger.info(f"策略 {self.name} 参数已更新")

    def get_state(self) -> Dict:
        """获取策略状态"""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'parameters': self.parameters,
            'state': self.state
        }
