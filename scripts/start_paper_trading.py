#!/usr/bin/env python3
"""
启动模拟交易脚本

使用方法:
python scripts/start_paper_trading.py \
  --strategy trend_following \
  --symbols BTC/USDT,ETH/USDT \
  --initial-capital 10000
"""

import sys
import argparse
from pathlib import Path
import logging

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backtesting.paper_trading.paper_trading_engine import PaperTradingEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='启动模拟交易')

    parser.add_argument('--strategy', type=str, required=True,
                       help='策略名称')
    parser.add_argument('--symbols', type=str, required=True,
                       help='交易对列表 (逗号分隔)')
    parser.add_argument('--initial-capital', type=float, default=10000,
                       help='初始资金')
    parser.add_argument('--commission', type=float, default=0.001,
                       help='手续费率')
    parser.add_argument('--slippage', type=float, default=0.0005,
                       help='滑点率')

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    symbols = args.symbols.split(',')

    logger.info("=" * 60)
    logger.info("模拟交易配置:")
    logger.info(f"  策略: {args.strategy}")
    logger.info(f"  交易对: {', '.join(symbols)}")
    logger.info(f"  初始资金: ${args.initial_capital:,.2f}")
    logger.info("=" * 60)

    logger.info("模拟交易引擎启动中...")
    logger.info("按 Ctrl+C 停止")

    # 这里应该创建实际的模拟交易引擎
    # 简化示例
    logger.info("模拟交易运行中...")

    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("模拟交易已停止")


if __name__ == '__main__':
    main()
