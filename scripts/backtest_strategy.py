"""
简化版策略回测工具

使用方法:
python scripts/backtest_strategy.py --strategy trend_following --symbol BTC/USDT --start 2024-01-01 --end 2024-12-31
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import argparse
import pandas as pd
from datetime import datetime
import logging

from src.data_pipeline.adapters.binance import BinanceAdapter
from src.trading_engine.strategies import (
    TrendFollowingStrategy,
    MeanReversionStrategy,
    MomentumStrategy
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_backtest(data: pd.DataFrame, strategy, initial_balance: float = 10000):
    """运行简化回测"""
    balance = initial_balance
    position = None
    trades = []

    for i in range(50, len(data)):
        current_data = data.iloc[:i+1]

        # 分析市场
        analysis = strategy.analyze(current_data)
        signals = strategy.generate_signals(current_data, analysis)

        current_price = data['close'].iloc[i]

        # 处理信号
        if signals and not position:
            signal = signals[0]
            if signal['signal'] == 'BUY':
                position = {
                    'entry_price': current_price,
                    'stop_loss': signal['stop_loss'],
                    'take_profit': signal['take_profit'],
                    'entry_time': data.index[i]
                }
                logger.info(f"开仓: {current_price}")

        # 检查止损止盈
        if position:
            if current_price <= position['stop_loss']:
                profit = current_price - position['entry_price']
                balance += profit
                trades.append({'profit': profit, 'type': 'stop_loss'})
                logger.info(f"止损: {current_price}, 盈亏: {profit}")
                position = None
            elif current_price >= position['take_profit']:
                profit = current_price - position['entry_price']
                balance += profit
                trades.append({'profit': profit, 'type': 'take_profit'})
                logger.info(f"止盈: {current_price}, 盈亏: {profit}")
                position = None

    # 计算统计
    total_trades = len(trades)
    winning_trades = len([t for t in trades if t['profit'] > 0])
    win_rate = winning_trades / total_trades if total_trades > 0 else 0
    total_profit = sum(t['profit'] for t in trades)

    return {
        'initial_balance': initial_balance,
        'final_balance': balance,
        'total_profit': total_profit,
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'win_rate': win_rate,
        'return_pct': (balance - initial_balance) / initial_balance * 100
    }


def main():
    parser = argparse.ArgumentParser(description='策略回测工具')
    parser.add_argument('--strategy', type=str, required=True)
    parser.add_argument('--symbol', type=str, required=True)
    parser.add_argument('--start', type=str, required=True)
    parser.add_argument('--end', type=str, required=True)

    args = parser.parse_args()

    # 获取数据
    adapter = BinanceAdapter()
    data = adapter.fetch_ohlcv(args.symbol, '1h', 1000)
    df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)

    # 选择策略
    strategies = {
        'trend_following': TrendFollowingStrategy(),
        'mean_reversion': MeanReversionStrategy(),
        'momentum': MomentumStrategy()
    }
    strategy = strategies.get(args.strategy)

    # 运行回测
    results = run_backtest(df, strategy)

    # 输出结果
    print("\n" + "="*60)
    print("回测结果")
    print("="*60)
    print(f"初始资金: ${results['initial_balance']:.2f}")
    print(f"最终资金: ${results['final_balance']:.2f}")
    print(f"总盈亏: ${results['total_profit']:.2f}")
    print(f"收益率: {results['return_pct']:.2f}%")
    print(f"总交易次数: {results['total_trades']}")
    print(f"盈利次数: {results['winning_trades']}")
    print(f"胜率: {results['win_rate']:.2%}")
    print("="*60)


if __name__ == '__main__':
    main()
