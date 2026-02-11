#!/usr/bin/env python3
"""
参数优化脚本

使用方法:
python scripts/optimize_strategy.py \
  --strategy trend_following \
  --symbol BTC/USDT \
  --method grid_search \
  --params "fast_period:10-50:5,slow_period:20-100:10"
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import logging

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backtesting.optimization.grid_search import GridSearchOptimizer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='策略参数优化')

    parser.add_argument('--strategy', type=str, required=True,
                       help='策略名称')
    parser.add_argument('--symbol', type=str, required=True,
                       help='交易对符号')
    parser.add_argument('--start', type=str, required=True,
                       help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, required=True,
                       help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--method', type=str, default='grid_search',
                       choices=['grid_search', 'genetic'],
                       help='优化方法')
    parser.add_argument('--params', type=str, required=True,
                       help='参数范围 (格式: param1:min-max:step,param2:min-max:step)')
    parser.add_argument('--metric', type=str, default='sharpe_ratio',
                       help='优化目标指标')
    parser.add_argument('--n-jobs', type=int, default=1,
                       help='并行任务数')
    parser.add_argument('--output', type=str, default='optimization_results.csv',
                       help='输出文件名')

    return parser.parse_args()


def parse_param_ranges(params_str: str) -> dict:
    """解析参数范围字符串"""
    param_grid = {}

    for param_spec in params_str.split(','):
        parts = param_spec.split(':')
        if len(parts) != 3:
            raise ValueError(f"Invalid parameter specification: {param_spec}")

        param_name = parts[0]
        min_val, max_val = map(float, parts[1].split('-'))
        step = float(parts[2])

        # 生成参数值列表
        values = []
        current = min_val
        while current <= max_val:
            values.append(current)
            current += step

        param_grid[param_name] = values

    return param_grid


def main():
    """主函数"""
    args = parse_args()

    logger.info("=" * 60)
    logger.info("参数优化配置:")
    logger.info(f"  策略: {args.strategy}")
    logger.info(f"  交易对: {args.symbol}")
    logger.info(f"  优化方法: {args.method}")
    logger.info(f"  目标指标: {args.metric}")
    logger.info("=" * 60)

    # 解析参数范围
    param_grid = parse_param_ranges(args.params)
    logger.info(f"参数空间: {param_grid}")

    # 定义回测函数
    def backtest_func(**params):
        # 这里应该调用实际的回测函数
        # 简化示例
        logger.info(f"Running backtest with params: {params}")
        return {
            'metrics': {
                'risk_adjusted_metrics': {
                    'sharpe_ratio': 1.5  # 示例值
                }
            }
        }

    # 创建优化器
    if args.method == 'grid_search':
        optimizer = GridSearchOptimizer(
            backtest_func=backtest_func,
            param_grid=param_grid,
            metric=args.metric,
            n_jobs=args.n_jobs
        )

        # 执行优化
        logger.info("开始网格搜索优化...")
        results = optimizer.optimize()

        # 保存结果
        results.to_csv(args.output, index=False)
        logger.info(f"结果已保存到: {args.output}")

        # 打印最优参数
        best_params = optimizer.get_best_params()
        logger.info("=" * 60)
        logger.info("最优参数:")
        for param, value in best_params.items():
            logger.info(f"  {param}: {value}")
        logger.info(f"最优{args.metric}: {results[args.metric].iloc[0]:.4f}")
        logger.info("=" * 60)

    logger.info("优化完成!")


if __name__ == '__main__':
    main()
