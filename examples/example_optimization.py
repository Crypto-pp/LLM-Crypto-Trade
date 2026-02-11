"""
参数优化示例

演示如何使用网格搜索优化策略参数
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backtesting.optimization.grid_search import GridSearchOptimizer


def backtest_ma_strategy(symbol, start_date, end_date, fast_period, slow_period):
    """
    回测移动平均策略

    Args:
        symbol: 交易对
        start_date: 开始日期
        end_date: 结束日期
        fast_period: 快速均线周期
        slow_period: 慢速均线周期

    Returns:
        回测结果字典
    """
    # 这里应该调用实际的回测函数
    # 简化示例，返回模拟结果

    # 模拟不同参数的表现
    sharpe_ratio = 2.0 - abs(fast_period - 15) * 0.05 - abs(slow_period - 40) * 0.01

    return {
        'metrics': {
            'return_metrics': {
                'annualized_return': 45.0 + (fast_period - 10) * 0.5
            },
            'risk_metrics': {
                'max_drawdown': 15.0 + abs(slow_period - 30) * 0.2
            },
            'risk_adjusted_metrics': {
                'sharpe_ratio': max(0, sharpe_ratio)
            },
            'trading_metrics': {
                'win_rate': 55.0,
                'total_trades': 50
            }
        }
    }


def main():
    """主函数"""
    print("=" * 60)
    print("参数优化示例：移动平均策略")
    print("=" * 60)

    # 配置参数
    symbol = 'BTC/USDT'
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)

    # 定义参数网格
    param_grid = {
        'fast_period': [5, 10, 15, 20],
        'slow_period': [20, 30, 40, 50, 60]
    }

    print(f"\n配置:")
    print(f"  交易对: {symbol}")
    print(f"  参数空间: {param_grid}")
    print(f"  总组合数: {len(param_grid['fast_period']) * len(param_grid['slow_period'])}")

    # 创建回测函数
    def backtest_func(fast_period, slow_period):
        return backtest_ma_strategy(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            fast_period=fast_period,
            slow_period=slow_period
        )

    # 创建优化器
    optimizer = GridSearchOptimizer(
        backtest_func=backtest_func,
        param_grid=param_grid,
        metric='sharpe_ratio',
        n_jobs=1  # 单进程
    )

    # 执行优化
    print("\n开始网格搜索...")
    results = optimizer.optimize()

    # 显示结果
    print("\n" + "=" * 60)
    print("优化结果 (前5名):")
    print("=" * 60)

    for i, row in results.head(5).iterrows():
        params = row['params']
        print(f"\n排名 {i+1}:")
        print(f"  快速周期: {params['fast_period']}")
        print(f"  慢速周期: {params['slow_period']}")
        print(f"  夏普比率: {row['sharpe_ratio']:.3f}")
        print(f"  年化收益: {row['annualized_return']:.2f}%")
        print(f"  最大回撤: {row['max_drawdown']:.2f}%")

    # 最优参数
    best_params = optimizer.get_best_params()
    print("\n" + "=" * 60)
    print("最优参数:")
    print(f"  快速周期: {best_params['fast_period']}")
    print(f"  慢速周期: {best_params['slow_period']}")
    print("=" * 60)

    # 保存结果
    output_file = 'optimization_results.csv'
    results.to_csv(output_file, index=False)
    print(f"\n完整结果已保存到: {output_file}")

    print("\n优化完成!")


if __name__ == '__main__':
    main()
