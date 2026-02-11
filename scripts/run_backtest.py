#!/usr/bin/env python3
"""
回测运行脚本

使用方法:
python scripts/run_backtest.py \
  --strategy trend_following \
  --symbol BTC/USDT \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --initial-capital 10000 \
  --output report.html
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import logging

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backtesting.engine.backtest_engine import BacktestEngine
from src.backtesting.engine.data_handler import CSVDataHandler
from src.backtesting.engine.execution_handler import SimulatedExecutionHandler
from src.backtesting.performance.performance_analyzer import PerformanceAnalyzer
from src.backtesting.performance.report_generator import ReportGenerator
from src.backtesting.visualization.charts import ChartGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='运行回测')

    parser.add_argument('--strategy', type=str, required=True,
                       help='策略名称')
    parser.add_argument('--symbol', type=str, required=True,
                       help='交易对符号 (例如: BTC/USDT)')
    parser.add_argument('--start', type=str, required=True,
                       help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, required=True,
                       help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--initial-capital', type=float, default=10000,
                       help='初始资金 (默认: 10000)')
    parser.add_argument('--csv-dir', type=str, default='data/historical',
                       help='CSV数据目录')
    parser.add_argument('--commission', type=float, default=0.001,
                       help='手续费率 (默认: 0.001)')
    parser.add_argument('--slippage', type=float, default=0.0005,
                       help='滑点率 (默认: 0.0005)')
    parser.add_argument('--output', type=str, default='backtest_report.html',
                       help='输出报告文件名')
    parser.add_argument('--charts', action='store_true',
                       help='生成图表')

    return parser.parse_args()


def load_strategy(strategy_name: str):
    """加载策略"""
    # 这里需要根据策略名称加载对应的策略类
    # 简化示例，实际应该从策略模块动态加载
    logger.info(f"Loading strategy: {strategy_name}")

    # 示例：返回一个简单的策略对象
    class SimpleStrategy:
        def calculate_signals(self, market_event, data_handler):
            # 简单的示例策略
            return []

    return SimpleStrategy()


def main():
    """主函数"""
    args = parse_args()

    logger.info("=" * 60)
    logger.info("回测配置:")
    logger.info(f"  策略: {args.strategy}")
    logger.info(f"  交易对: {args.symbol}")
    logger.info(f"  时间范围: {args.start} 到 {args.end}")
    logger.info(f"  初始资金: ${args.initial_capital:,.2f}")
    logger.info("=" * 60)

    # 解析日期
    start_date = datetime.strptime(args.start, '%Y-%m-%d')
    end_date = datetime.strptime(args.end, '%Y-%m-%d')

    # 加载策略
    strategy = load_strategy(args.strategy)

    # 创建数据处理器
    data_handler = CSVDataHandler(
        symbol=args.symbol,
        start_date=start_date,
        end_date=end_date,
        csv_dir=args.csv_dir
    )

    # 创建执行处理器
    execution_handler = SimulatedExecutionHandler(
        commission_rate=args.commission,
        slippage_rate=args.slippage
    )

    # 创建回测引擎
    engine = BacktestEngine(
        initial_capital=args.initial_capital,
        data_handler=data_handler,
        execution_handler=execution_handler,
        strategy=strategy
    )

    # 运行回测
    logger.info("开始回测...")
    results = engine.run()

    # 性能分析
    logger.info("分析性能...")
    analyzer = PerformanceAnalyzer(
        initial_capital=args.initial_capital,
        equity_curve=results['equity_curve'],
        trades=results['trades'].to_dict('records') if len(results['trades']) > 0 else []
    )

    analysis = analyzer.analyze()

    # 打印摘要
    logger.info("=" * 60)
    logger.info("回测结果摘要:")
    summary = analysis['summary']
    logger.info(f"  最终资金: ${summary['final_capital']:,.2f}")
    logger.info(f"  总收益率: {summary['total_return']:.2f}%")
    logger.info(f"  年化收益率: {summary['annualized_return']:.2f}%")
    logger.info(f"  最大回撤: {summary['max_drawdown']:.2f}%")
    logger.info(f"  夏普比率: {summary['sharpe_ratio']:.2f}")
    logger.info(f"  胜率: {summary['win_rate']:.2f}%")
    logger.info(f"  交易次数: {summary['total_trades']}")
    logger.info(f"  策略评级: {analysis['rating']['rating']} ({analysis['rating']['total_score']:.1f}/100)")
    logger.info("=" * 60)

    # 生成报告
    logger.info(f"生成报告: {args.output}")
    report_gen = ReportGenerator(analysis)
    report_path = report_gen.generate_html_report(args.output)
    logger.info(f"报告已保存到: {report_path}")

    # 生成图表
    if args.charts:
        logger.info("生成图表...")
        chart_gen = ChartGenerator()

        if len(results['equity_curve']) > 0:
            chart_gen.plot_equity_curve(results['equity_curve'])
            chart_gen.plot_drawdown_curve(results['equity_curve'])
            chart_gen.plot_performance_summary(analysis['metrics'])

        logger.info("图表已生成")

    logger.info("回测完成!")


if __name__ == '__main__':
    main()
