"""
完整回测示例

演示如何使用回测框架进行完整的策略回测
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backtesting.engine.backtest_engine import BacktestEngine
from src.backtesting.engine.data_handler import CSVDataHandler
from src.backtesting.engine.execution_handler import SimulatedExecutionHandler
from src.backtesting.engine.event_engine import SignalEvent
from src.backtesting.performance.performance_analyzer import PerformanceAnalyzer
from src.backtesting.performance.report_generator import ReportGenerator


class SimpleMAStrategy:
    """简单的移动平均策略"""

    def __init__(self, fast_period=10, slow_period=30):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.ma_fast = []
        self.ma_slow = []

    def calculate_signals(self, market_event, data_handler):
        """计算交易信号"""
        signals = []

        # 获取最新的K线数据
        bars = data_handler.get_latest_bars(self.slow_period)

        if bars is None or len(bars) < self.slow_period:
            return signals

        # 计算移动平均
        closes = [bar['close'] for bar in bars]
        ma_fast = sum(closes[-self.fast_period:]) / self.fast_period
        ma_slow = sum(closes[-self.slow_period:]) / self.slow_period

        # 生成信号
        if len(self.ma_fast) > 0:
            # 金叉：买入信号
            if self.ma_fast[-1] <= self.ma_slow[-1] and ma_fast > ma_slow:
                signal = SignalEvent(
                    symbol=market_event.symbol,
                    timestamp=market_event.timestamp,
                    signal_type='BUY',
                    strength=1.0,
                    price=market_event.close
                )
                signals.append(signal)

            # 死叉：卖出信号
            elif self.ma_fast[-1] >= self.ma_slow[-1] and ma_fast < ma_slow:
                signal = SignalEvent(
                    symbol=market_event.symbol,
                    timestamp=market_event.timestamp,
                    signal_type='SELL',
                    strength=1.0,
                    price=market_event.close
                )
                signals.append(signal)

        # 更新移动平均
        self.ma_fast.append(ma_fast)
        self.ma_slow.append(ma_slow)

        return signals


def main():
    """主函数"""
    print("=" * 60)
    print("回测示例：简单移动平均策略")
    print("=" * 60)

    # 配置参数
    symbol = 'BTC/USDT'
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    initial_capital = 10000.0

    print(f"\n配置:")
    print(f"  交易对: {symbol}")
    print(f"  时间范围: {start_date.date()} 到 {end_date.date()}")
    print(f"  初始资金: ${initial_capital:,.2f}")

    # 创建策略
    strategy = SimpleMAStrategy(fast_period=10, slow_period=30)

    # 创建数据处理器
    data_handler = CSVDataHandler(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        csv_dir='data/historical'
    )

    # 创建执行处理器
    execution_handler = SimulatedExecutionHandler(
        commission_rate=0.001,
        slippage_rate=0.0005
    )

    # 创建回测引擎
    engine = BacktestEngine(
        initial_capital=initial_capital,
        data_handler=data_handler,
        execution_handler=execution_handler,
        strategy=strategy
    )

    # 运行回测
    print("\n开始回测...")
    results = engine.run()

    # 性能分析
    print("\n分析性能...")
    analyzer = PerformanceAnalyzer(
        initial_capital=initial_capital,
        equity_curve=results['equity_curve'],
        trades=results['trades'].to_dict('records') if len(results['trades']) > 0 else []
    )

    analysis = analyzer.analyze()

    # 打印结果
    print("\n" + "=" * 60)
    print("回测结果:")
    print("=" * 60)

    summary = analysis['summary']
    print(f"\n核心指标:")
    print(f"  最终资金: ${summary['final_capital']:,.2f}")
    print(f"  总收益率: {summary['total_return']:.2f}%")
    print(f"  年化收益率: {summary['annualized_return']:.2f}%")
    print(f"  最大回撤: {summary['max_drawdown']:.2f}%")
    print(f"  夏普比率: {summary['sharpe_ratio']:.2f}")
    print(f"  胜率: {summary['win_rate']:.2f}%")
    print(f"  交易次数: {summary['total_trades']}")

    rating = analysis['rating']
    print(f"\n策略评级: {rating['rating']} (得分: {rating['total_score']:.1f}/100)")

    # 生成报告
    print("\n生成HTML报告...")
    report_gen = ReportGenerator(analysis, output_dir='reports')
    report_path = report_gen.generate_html_report('example_backtest_report.html')
    print(f"报告已保存到: {report_path}")

    print("\n回测完成!")


if __name__ == '__main__':
    main()
