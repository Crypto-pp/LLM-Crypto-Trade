"""
市场分析命令行工具
用于分析指定交易对的市场状况和生成交易信号

使用方法:
python scripts/analyze_market.py --symbol BTC/USDT --strategy trend_following
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import argparse
import pandas as pd
from datetime import datetime, timedelta
import logging

from src.data_pipeline.adapters.binance import BinanceAdapter
from src.trading_engine.strategies import (
    TrendFollowingStrategy,
    MeanReversionStrategy,
    MomentumStrategy,
    PriceActionStrategy,
    StrategyManager
)
from src.trading_engine.signals import SignalGenerator, SignalAggregator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_market_data(symbol: str, interval: str = '1h', limit: int = 200):
    """获取市场数据"""
    try:
        adapter = BinanceAdapter()
        data = adapter.fetch_ohlcv(symbol, interval, limit)

        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)

        logger.info(f"获取到 {len(df)} 条数据")
        return df
    except Exception as e:
        logger.error(f"获取市场数据失败: {e}")
        return None


def analyze_with_strategy(data: pd.DataFrame, strategy_name: str):
    """使用指定策略分析"""
    strategies = {
        'trend_following': TrendFollowingStrategy(),
        'mean_reversion': MeanReversionStrategy(),
        'momentum': MomentumStrategy(),
        'price_action': PriceActionStrategy()
    }

    if strategy_name not in strategies:
        logger.error(f"未知策略: {strategy_name}")
        return None

    strategy = strategies[strategy_name]

    # 分析市场
    analysis = strategy.analyze(data)

    # 生成信号
    signals = strategy.generate_signals(data, analysis)

    return analysis, signals


def main():
    parser = argparse.ArgumentParser(description='市场分析工具')
    parser.add_argument('--symbol', type=str, required=True, help='交易对，如 BTC/USDT')
    parser.add_argument('--strategy', type=str, default='trend_following',
                       choices=['trend_following', 'mean_reversion', 'momentum', 'price_action'],
                       help='策略名称')
    parser.add_argument('--interval', type=str, default='1h', help='时间周期')
    parser.add_argument('--limit', type=int, default=200, help='数据条数')

    args = parser.parse_args()

    logger.info(f"开始分析 {args.symbol}")
    logger.info(f"策略: {args.strategy}")

    # 获取数据
    data = fetch_market_data(args.symbol, args.interval, args.limit)
    if data is None:
        return

    # 分析
    analysis, signals = analyze_with_strategy(data, args.strategy)

    # 输出结果
    print("\n" + "="*60)
    print(f"市场分析报告 - {args.symbol}")
    print("="*60)
    print(f"\n当前价格: {data['close'].iloc[-1]:.2f}")
    print(f"24h 涨跌幅: {((data['close'].iloc[-1] / data['close'].iloc[-24] - 1) * 100):.2f}%")

    print("\n分析结果:")
    for key, value in analysis.items():
        if isinstance(value, (int, float)):
            print(f"  {key}: {value:.4f}")

    print(f"\n生成信号数量: {len(signals)}")
    if signals:
        print("\n交易信号:")
        for i, signal in enumerate(signals, 1):
            print(f"\n信号 {i}:")
            print(f"  类型: {signal['signal']}")
            print(f"  入场价: {signal['entry_price']:.2f}")
            print(f"  止损: {signal['stop_loss']:.2f}")
            print(f"  止盈: {signal['take_profit']:.2f}")
            print(f"  置信度: {signal['confidence']:.2%}")
            print(f"  原因: {signal['reason']}")
    else:
        print("  无交易信号")

    print("\n" + "="*60)


if __name__ == '__main__':
    main()
