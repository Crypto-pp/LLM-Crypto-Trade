"""
风险监控模块
实时风险监控、风险指标计算、风险预警、风险报告
"""

from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RiskMonitor:
    """
    风险监控器
    """

    def __init__(self):
        """初始化风险监控器"""
        self.alerts = []
        logger.info("风险监控器已初始化")

    def calculate_risk_metrics(
        self,
        account_balance: float,
        peak_balance: float,
        positions: List[Dict]
    ) -> Dict[str, float]:
        """
        计算风险指标

        Returns:
            风险指标字典
        """
        try:
            # 计算回撤
            drawdown = (peak_balance - account_balance) / peak_balance if peak_balance > 0 else 0

            # 计算持仓集中度
            total_position_value = sum(p.get('value', 0) for p in positions)
            max_position = max([p.get('value', 0) for p in positions]) if positions else 0
            concentration = max_position / total_position_value if total_position_value > 0 else 0

            # 计算风险敞口
            total_exposure = sum(p.get('value', 0) * p.get('leverage', 1) for p in positions)
            exposure_ratio = total_exposure / account_balance if account_balance > 0 else 0

            metrics = {
                'drawdown': drawdown,
                'concentration': concentration,
                'exposure_ratio': exposure_ratio,
                'position_count': len(positions),
                'total_position_value': total_position_value
            }

            return metrics

        except Exception as e:
            logger.error(f"计算风险指标失败: {e}")
            return {}

    def check_alerts(self, metrics: Dict[str, float]) -> List[Dict]:
        """
        检查风险预警

        Returns:
            预警列表
        """
        alerts = []

        # 回撤预警
        if metrics.get('drawdown', 0) > 0.15:
            alerts.append({
                'level': 'CRITICAL',
                'type': 'drawdown',
                'message': f"严重回撤: {metrics['drawdown']:.2%}",
                'timestamp': datetime.now()
            })
        elif metrics.get('drawdown', 0) > 0.10:
            alerts.append({
                'level': 'WARNING',
                'type': 'drawdown',
                'message': f"回撤警告: {metrics['drawdown']:.2%}",
                'timestamp': datetime.now()
            })

        # 集中度预警
        if metrics.get('concentration', 0) > 0.50:
            alerts.append({
                'level': 'CRITICAL',
                'type': 'concentration',
                'message': f"持仓过度集中: {metrics['concentration']:.2%}",
                'timestamp': datetime.now()
            })
        elif metrics.get('concentration', 0) > 0.30:
            alerts.append({
                'level': 'WARNING',
                'type': 'concentration',
                'message': f"持仓集中度较高: {metrics['concentration']:.2%}",
                'timestamp': datetime.now()
            })

        # 风险敞口预警
        if metrics.get('exposure_ratio', 0) > 2.0:
            alerts.append({
                'level': 'CRITICAL',
                'type': 'exposure',
                'message': f"风险敞口过高: {metrics['exposure_ratio']:.2f}x",
                'timestamp': datetime.now()
            })

        self.alerts.extend(alerts)
        return alerts

    def generate_risk_report(
        self,
        account_balance: float,
        peak_balance: float,
        positions: List[Dict],
        trade_history: List[Dict]
    ) -> Dict:
        """
        生成风险报告

        Returns:
            风险报告字典
        """
        try:
            metrics = self.calculate_risk_metrics(account_balance, peak_balance, positions)
            alerts = self.check_alerts(metrics)

            # 计算交易统计
            total_trades = len(trade_history)
            winning_trades = len([t for t in trade_history if t.get('profit', 0) > 0])
            win_rate = winning_trades / total_trades if total_trades > 0 else 0

            report = {
                'timestamp': datetime.now().isoformat(),
                'account_balance': account_balance,
                'peak_balance': peak_balance,
                'metrics': metrics,
                'alerts': alerts,
                'statistics': {
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'win_rate': win_rate
                }
            }

            return report

        except Exception as e:
            logger.error(f"生成风险报告失败: {e}")
            return {}

    def get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        """获取最近的预警"""
        return self.alerts[-limit:]

    def clear_alerts(self):
        """清空预警"""
        self.alerts.clear()
        logger.info("预警已清空")
