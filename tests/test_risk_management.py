"""
风险管理测试
"""

import pytest
from src.risk_management import (
    PositionManager,
    StopLossTakeProfit,
    RiskChecker,
    RiskMonitor
)


def test_position_manager():
    """测试仓位管理器"""
    manager = PositionManager(account_balance=10000)

    # 测试固定比例法
    position = manager.calculate_fixed_ratio(
        entry_price=100,
        stop_loss=95,
        risk_per_trade=0.02
    )
    assert position > 0

    # 测试凯利公式
    kelly_pct = manager.calculate_kelly(
        win_rate=0.45,
        avg_win=300,
        avg_loss=100,
        kelly_fraction=0.25
    )
    assert 0 <= kelly_pct <= 0.25


def test_stop_loss_take_profit():
    """测试止损止盈"""
    sltp = StopLossTakeProfit()

    # 测试固定百分比
    stop_loss, take_profit = sltp.calculate_fixed_percentage(
        entry_price=100,
        signal_type='BUY',
        stop_loss_pct=0.05,
        take_profit_pct=0.15
    )
    assert stop_loss < 100 < take_profit

    # 测试ATR止损
    stop_loss, take_profit = sltp.calculate_atr_based(
        entry_price=100,
        atr=5,
        signal_type='BUY',
        atr_multiplier=2.0
    )
    assert stop_loss < 100 < take_profit


def test_risk_checker():
    """测试风险检查器"""
    checker = RiskChecker(account_balance=10000)

    # 测试单笔风险检查
    result = checker.check_single_trade_risk(
        entry_price=100,
        stop_loss=95,
        position_size=40
    )
    assert 'passed' in result
    assert 'risk_percentage' in result

    # 测试回撤检查
    checker.account_balance = 8500
    result = checker.check_drawdown()
    assert 'current_drawdown' in result


def test_risk_monitor():
    """测试风险监控器"""
    monitor = RiskMonitor()

    # 测试风险指标计算
    metrics = monitor.calculate_risk_metrics(
        account_balance=10000,
        peak_balance=12000,
        positions=[
            {'value': 3000, 'leverage': 1},
            {'value': 2000, 'leverage': 1}
        ]
    )
    assert 'drawdown' in metrics
    assert 'concentration' in metrics


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
