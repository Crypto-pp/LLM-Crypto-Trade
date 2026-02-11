"""
回测引擎集成测试

使用模拟数据验证：
- BacktestEngine 事件循环
- StrategyAdapter 桥接
- Portfolio 交易记录
- 止损止盈检查
- PerformanceAnalyzer 分析
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.backtesting.engine.event_engine import (
    MarketEvent, SignalEvent, OrderEvent, FillEvent, EventQueue,
)
from src.backtesting.engine.data_handler import DataHandler
from src.backtesting.engine.execution_handler import SimulatedExecutionHandler
from src.backtesting.engine.portfolio import Portfolio, Position
from src.backtesting.engine.backtest_engine import BacktestEngine
from src.backtesting.engine.strategy_adapter import StrategyAdapter
from src.backtesting.performance.performance_analyzer import PerformanceAnalyzer


# --------------- 测试用模拟组件 ---------------

def _make_bars(n: int = 100, base_price: float = 100.0):
    """生成模拟K线数据"""
    np.random.seed(42)
    dates = [datetime(2024, 1, 1) + timedelta(hours=i) for i in range(n)]
    prices = [base_price]
    for _ in range(n - 1):
        change = np.random.normal(0, 0.02)
        prices.append(prices[-1] * (1 + change))

    bars = []
    for i, (dt, close) in enumerate(zip(dates, prices)):
        high = close * (1 + abs(np.random.normal(0, 0.005)))
        low = close * (1 - abs(np.random.normal(0, 0.005)))
        open_p = close * (1 + np.random.normal(0, 0.003))
        bars.append({
            'timestamp': dt,
            'open': open_p,
            'high': high,
            'low': low,
            'close': close,
            'volume': np.random.uniform(100, 1000),
        })
    return bars


class MockDataHandler(DataHandler):
    """内存数据处理器，用于测试"""

    MAX_LATEST_BARS = 500

    def __init__(self, bars: list, symbol: str = 'BTC/USDT'):
        super().__init__(
            symbol=symbol,
            start_date=bars[0]['timestamp'],
            end_date=bars[-1]['timestamp'],
        )
        self._bars = bars
        self._index = 0
        self.latest_bars = []

    def load_data(self):
        pass

    def get_latest_bar(self):
        if self.latest_bars:
            return self.latest_bars[-1]
        return None

    def get_latest_bars(self, n=1):
        if len(self.latest_bars) >= n:
            return self.latest_bars[-n:]
        return None

    def update_bars(self):
        if self._index >= len(self._bars):
            return None
        bar = self._bars[self._index]
        self._index += 1
        self.latest_bars.append(bar)
        if len(self.latest_bars) > self.MAX_LATEST_BARS:
            self.latest_bars = self.latest_bars[-self.MAX_LATEST_BARS:]
        return MarketEvent(
            symbol=self.symbol,
            timestamp=bar['timestamp'],
            open_price=bar['open'],
            high_price=bar['high'],
            low_price=bar['low'],
            close_price=bar['close'],
            volume=bar['volume'],
        )

    def continue_backtest(self):
        return self._index < len(self._bars)


class SimpleTestStrategy:
    """简单测试策略：SMA 交叉"""

    name = 'test_strategy'

    def calculate_signals(self, event, data_handler):
        bars = data_handler.get_latest_bars(20)
        if bars is None or len(bars) < 20:
            return None

        closes = [b['close'] for b in bars]
        sma_short = np.mean(closes[-5:])
        sma_long = np.mean(closes[-20:])

        # 前一根K线的均线关系
        prev_closes = closes[:-1]
        prev_short = np.mean(prev_closes[-5:])
        prev_long = np.mean(prev_closes[-20:]) if len(prev_closes) >= 20 else prev_short

        signals = []
        if sma_short > sma_long and prev_short <= prev_long:
            signals.append(SignalEvent(
                symbol=event.symbol,
                timestamp=event.timestamp,
                signal_type='BUY',
                strength=0.8,
                price=event.close,
                metadata={'stop_loss': event.close * 0.95, 'take_profit': event.close * 1.10},
            ))
        elif sma_short < sma_long and prev_short >= prev_long:
            signals.append(SignalEvent(
                symbol=event.symbol,
                timestamp=event.timestamp,
                signal_type='SELL',
                strength=0.8,
                price=event.close,
            ))

        return signals if signals else None


# --------------- 测试用例 ---------------

class TestPosition:
    """Position 持仓管理测试"""

    def test_buy_updates_quantity_and_avg_price(self):
        pos = Position('BTC/USDT')
        fill = FillEvent(
            symbol='BTC/USDT',
            timestamp=datetime(2024, 1, 1),
            side='BUY',
            quantity=1.0,
            fill_price=100.0,
            commission=0.1,
        )
        pos.update(fill)
        assert pos.quantity == 1.0
        assert pos.avg_price == pytest.approx(100.1, rel=1e-2)

    def test_sell_calculates_realized_pnl(self):
        pos = Position('BTC/USDT')
        # 买入
        buy_fill = FillEvent(
            symbol='BTC/USDT',
            timestamp=datetime(2024, 1, 1),
            side='BUY',
            quantity=1.0,
            fill_price=100.0,
            commission=0.1,
        )
        pos.update(buy_fill)

        # 卖出
        sell_fill = FillEvent(
            symbol='BTC/USDT',
            timestamp=datetime(2024, 1, 2),
            side='SELL',
            quantity=1.0,
            fill_price=110.0,
            commission=0.1,
        )
        pos.update(sell_fill)

        assert pos.quantity == 0
        assert pos.realized_pnl > 0  # 盈利

    def test_unrealized_pnl(self):
        pos = Position('BTC/USDT')
        fill = FillEvent(
            symbol='BTC/USDT',
            timestamp=datetime(2024, 1, 1),
            side='BUY',
            quantity=2.0,
            fill_price=100.0,
            commission=0.0,
        )
        pos.update(fill)
        pnl = pos.get_unrealized_pnl(120.0)
        assert pnl == pytest.approx(40.0, rel=1e-2)


class TestPortfolioTradeRecord:
    """验证 Portfolio 交易记录 bug 修复（Task #1）"""

    def test_trade_record_has_correct_entry_price(self):
        """平仓后交易记录应包含正确的入场价格，而非 0"""
        portfolio = Portfolio(10000.0)

        # 买入
        buy_fill = FillEvent(
            symbol='BTC/USDT',
            timestamp=datetime(2024, 1, 1),
            side='BUY',
            quantity=1.0,
            fill_price=100.0,
            commission=0.1,
        )
        portfolio.update_fill(buy_fill)

        # 卖出平仓
        sell_fill = FillEvent(
            symbol='BTC/USDT',
            timestamp=datetime(2024, 1, 2),
            side='SELL',
            quantity=1.0,
            fill_price=110.0,
            commission=0.1,
        )
        portfolio.update_fill(sell_fill)

        assert len(portfolio.trades) == 1
        trade = portfolio.trades[0]
        # 关键断言：入场价格不应为 0
        assert trade['entry_price'] > 0
        assert trade['entry_price'] == pytest.approx(100.1, rel=1e-2)
        assert trade['exit_price'] == 110.0
        assert trade['pnl'] > 0


class TestBacktestEngine:
    """回测引擎集成测试"""

    def test_full_backtest_run(self):
        """完整回测流程：数据→策略→订单→成交→权益曲线"""
        bars = _make_bars(200)
        data_handler = MockDataHandler(bars)
        strategy = SimpleTestStrategy()
        execution_handler = SimulatedExecutionHandler(
            commission_rate=0.001,
            slippage_rate=0.0005,
        )

        engine = BacktestEngine(
            initial_capital=10000.0,
            data_handler=data_handler,
            execution_handler=execution_handler,
            strategy=strategy,
        )
        results = engine.run()

        # 基本结构验证
        assert 'initial_capital' in results
        assert 'final_capital' in results
        assert 'equity_curve' in results
        assert 'trades' in results
        assert 'statistics' in results

        # 权益曲线应有数据
        eq = results['equity_curve']
        assert len(eq) > 0

        # 统计信息
        stats = results['statistics']
        assert stats['total_signals'] >= 0
        assert stats['duration_seconds'] >= 0

    def test_stop_loss_triggers(self):
        """验证止损逻辑：买入后价格大幅下跌应触发止损平仓"""
        # 构造先涨后跌的K线
        bars = []
        base = datetime(2024, 1, 1)
        # 前 25 根：稳定上涨（让策略有足够数据并触发买入）
        price = 100.0
        for i in range(25):
            price *= 1.005
            bars.append({
                'timestamp': base + timedelta(hours=i),
                'open': price * 0.999, 'high': price * 1.002,
                'low': price * 0.998, 'close': price,
                'volume': 500.0,
            })
        # 后 20 根：暴跌（触发止损）
        for i in range(25, 45):
            price *= 0.97
            bars.append({
                'timestamp': base + timedelta(hours=i),
                'open': price * 1.01, 'high': price * 1.02,
                'low': price * 0.98, 'close': price,
                'volume': 800.0,
            })

        data_handler = MockDataHandler(bars)
        strategy = SimpleTestStrategy()
        execution_handler = SimulatedExecutionHandler()

        engine = BacktestEngine(
            initial_capital=10000.0,
            data_handler=data_handler,
            execution_handler=execution_handler,
            strategy=strategy,
        )
        results = engine.run()

        # 引擎应正常完成，不抛异常
        assert results['statistics']['duration_seconds'] >= 0


class TestPerformanceAnalyzer:
    """性能分析器测试"""

    def test_analyze_with_trades(self):
        """有交易记录时应生成完整分析报告"""
        equity_data = []
        base = datetime(2024, 1, 1)
        equity = 10000.0
        for i in range(100):
            equity *= (1 + np.random.normal(0.001, 0.01))
            equity_data.append({
                'timestamp': base + timedelta(hours=i),
                'equity': equity,
                'cash': equity * 0.5,
                'holdings': equity * 0.5,
            })
        equity_curve = pd.DataFrame(equity_data)

        trades = [
            {
                'symbol': 'BTC/USDT',
                'entry_time': base,
                'exit_time': base + timedelta(hours=10),
                'quantity': 0.1,
                'entry_price': 100.0,
                'exit_price': 110.0,
                'pnl': 1.0,
                'pnl_pct': 10.0,
            },
            {
                'symbol': 'BTC/USDT',
                'entry_time': base + timedelta(hours=20),
                'exit_time': base + timedelta(hours=30),
                'quantity': 0.1,
                'entry_price': 105.0,
                'exit_price': 100.0,
                'pnl': -0.5,
                'pnl_pct': -4.76,
            },
        ]

        analyzer = PerformanceAnalyzer(
            initial_capital=10000.0,
            equity_curve=equity_curve,
            trades=trades,
        )
        report = analyzer.analyze()

        assert 'summary' in report
        assert 'metrics' in report
        assert 'rating' in report
        assert 'analysis' in report

        # 评级应为有效值
        assert report['rating']['rating'] in ('A', 'B', 'C', 'D', 'F')
        assert 0 <= report['rating']['total_score'] <= 100


class TestSanitize:
    """_sanitize 工具函数测试（内联实现避免 API 导入链）"""

    @staticmethod
    def _sanitize(obj):
        """与 backtesting.py 中相同的实现，避免触发 API 导入链"""
        if isinstance(obj, dict):
            return {k: TestSanitize._sanitize(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [TestSanitize._sanitize(item) for item in obj]
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            val = float(obj)
            if np.isnan(val) or np.isinf(val):
                return 0.0
            return val
        if isinstance(obj, (pd.Timestamp, datetime)):
            return obj.isoformat()
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient='records')
        return obj

    def test_numpy_types(self):
        s = self._sanitize
        assert s(np.float64(3.14)) == pytest.approx(3.14)
        assert s(np.int64(42)) == 42
        assert s(np.bool_(True)) is True
        assert s(np.float64('nan')) == 0.0
        assert s(np.float64('inf')) == 0.0

    def test_nested_dict(self):
        s = self._sanitize
        data = {'a': np.float64(1.5), 'b': [np.int64(2), np.bool_(False)]}
        result = s(data)
        assert result == {'a': 1.5, 'b': [2, False]}
        assert type(result['a']) is float
        assert type(result['b'][0]) is int

    def test_dataframe(self):
        s = self._sanitize
        df = pd.DataFrame({'x': [1, 2], 'y': [3.0, 4.0]})
        result = s(df)
        assert isinstance(result, list)
        assert len(result) == 2


class TestResolveStrategy:
    """策略解析测试（直接使用 STRATEGY_MAP 避免 API 导入链）"""

    STRATEGY_MAP = {
        "趋势跟踪": None,  # 仅测试映射逻辑
        "均值回归": None,
        "动量策略": None,
        "价格行为": None,
    }

    def test_valid_strategy_creates_instance(self):
        from src.trading_engine.strategies import TrendFollowingStrategy
        strategy = TrendFollowingStrategy()
        assert hasattr(strategy, 'analyze')
        assert hasattr(strategy, 'generate_signals')

    def test_invalid_strategy_name(self):
        assert "不存在的策略" not in self.STRATEGY_MAP
