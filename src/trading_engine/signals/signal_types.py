"""
信号类型定义
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class SignalType(Enum):
    """信号类型"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class SignalStrength(Enum):
    """信号强度"""
    VERY_WEAK = 1
    WEAK = 2
    MODERATE = 3
    STRONG = 4
    VERY_STRONG = 5


@dataclass
class Signal:
    """
    交易信号数据类
    """
    signal_id: str
    symbol: str
    exchange: str
    signal_type: SignalType
    entry_price: float
    stop_loss: float
    take_profit: float
    timestamp: datetime
    strategy: str
    confidence: float
    strength: SignalStrength
    valid_until: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None

    def __post_init__(self):
        """初始化后处理"""
        if not self.signal_id:
            self.signal_id = str(uuid.uuid4())

        if not self.timestamp:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'signal_id': self.signal_id,
            'symbol': self.symbol,
            'exchange': self.exchange,
            'signal_type': self.signal_type.value,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'timestamp': self.timestamp.isoformat(),
            'strategy': self.strategy,
            'confidence': self.confidence,
            'strength': self.strength.value,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'metadata': self.metadata,
            'reason': self.reason
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Signal':
        """从字典创建信号"""
        return cls(
            signal_id=data.get('signal_id', ''),
            symbol=data['symbol'],
            exchange=data['exchange'],
            signal_type=SignalType(data['signal_type']),
            entry_price=data['entry_price'],
            stop_loss=data['stop_loss'],
            take_profit=data['take_profit'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            strategy=data['strategy'],
            confidence=data['confidence'],
            strength=SignalStrength(data['strength']),
            valid_until=datetime.fromisoformat(data['valid_until']) if data.get('valid_until') else None,
            metadata=data.get('metadata'),
            reason=data.get('reason')
        )

    def is_valid(self) -> bool:
        """检查信号是否仍然有效"""
        if self.valid_until:
            return datetime.now() < self.valid_until
        return True

    def calculate_risk_reward_ratio(self) -> float:
        """计算风险收益比"""
        risk = abs(self.entry_price - self.stop_loss)
        reward = abs(self.take_profit - self.entry_price)

        if risk == 0:
            return 0

        return reward / risk
