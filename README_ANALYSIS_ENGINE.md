# 加密货币自动化分析系统 - 技术分析和策略引擎模块

## 项目概述

本项目实现了加密货币自动化分析系统的技术分析和策略引擎模块，包括技术指标计算、价格行为识别、交易策略、信号生成和风险管理等核心功能。

## 已完成的模块

### 1. 技术指标计算模块 (`src/trading_engine/indicators/`)

#### 基础指标 (`basic.py`)
- **MA** - 简单移动平均线
- **EMA** - 指数移动平均线
- **SMA** - 简单移动平均线
- **WMA** - 加权移动平均线
- **VWAP** - 成交量加权平均价格

#### 趋势指标 (`trend.py`)
- **MACD** - 指数平滑异同移动平均线
- **ADX** - 平均趋向指数
- **Parabolic SAR** - 抛物线转向指标
- **Ichimoku Cloud** - 一目均衡表

#### 震荡指标 (`oscillators.py`)
- **RSI** - 相对强弱指数
- **Stochastic** - 随机指标
- **CCI** - 商品通道指数
- **Williams %R** - 威廉指标

#### 波动率指标 (`volatility.py`)
- **Bollinger Bands** - 布林带
- **ATR** - 真实波动幅度
- **Standard Deviation** - 标准差
- **Keltner Channels** - 肯特纳通道

#### 成交量指标 (`volume.py`)
- **OBV** - 能量潮指标
- **Volume Ratio** - 成交量比率
- **MFI** - 资金流量指数

#### 指标管理器 (`indicator_manager.py`)
- 统一的指标计算接口
- 批量计算多个指标
- 缓存计算结果
- 性能优化

### 2. 价格行为识别模块 (`src/trading_engine/price_action/`)

#### K线形态识别 (`candlestick_patterns.py`)
- **Pin Bar** - 长影线/锤子线/射击之星
- **Engulfing** - 吞没形态
- **Inside Bar** - 内包线
- **Outside Bar** - 外包线
- **Doji** - 十字星
- **Hammer** - 锤子线/上吊线

#### 图表形态识别 (`chart_patterns.py`)
- **Double Top/Bottom** - 双顶/双底
- **Head and Shoulders** - 头肩顶/头肩底
- **Triangle** - 三角形（上升/下降/对称）
- **Flag** - 旗形整理

#### 支撑阻力识别 (`support_resistance.py`)
- 历史高低点识别
- 密集成交区识别
- 心理价位识别
- 支撑阻力强度评分
- 支撑阻力转换检测

#### 趋势线识别 (`trendline.py`)
- 趋势线绘制
- 趋势线强度计算
- 趋势线突破检测
- 通道识别

#### 市场结构分析 (`market_structure.py`)
- Higher Highs/Lower Lows识别
- 趋势判断
- 结构破坏检测
- 震荡区间识别

### 3. 策略引擎 (`src/trading_engine/strategies/`)

#### 策略基类 (`base_strategy.py`)
- 抽象基类定义统一接口
- `analyze()` - 分析市场
- `generate_signals()` - 生成信号
- `calculate_position_size()` - 计算仓位
- `check_risk()` - 风险检查

#### 趋势跟踪策略 (`trend_following.py`)
- 基于MA/EMA的趋势策略
- 基于MACD的趋势策略
- 多时间框架趋势确认
- ADX趋势强度过滤

#### 均值回归策略 (`mean_reversion.py`)
- 基于布林带的均值回归
- 基于RSI的超买超卖
- 回归中轨目标

#### 动量策略 (`momentum.py`)
- 基于动量指标的策略
- 相对强度策略
- 创新高/新低确认

#### 价格行为策略 (`price_action_strategy.py`)
- 基于K线形态的策略
- 基于支撑阻力的策略
- Pin Bar和吞没形态交易

#### 策略管理器 (`strategy_manager.py`)
- 管理多个策略
- 策略组合
- 信号聚合
- 冲突处理

### 4. 信号生成模块 (`src/trading_engine/signals/`)

#### 信号类型 (`signal_types.py`)
- Signal数据类定义
- SignalType枚举（BUY/SELL/HOLD）
- SignalStrength枚举（1-5级）
- 风险收益比计算

#### 信号生成器 (`signal_generator.py`)
- 从策略生成标准信号
- 信号验证
- 信号过滤（风险过滤）
- 信号优先级排序

#### 信号聚合器 (`signal_aggregator.py`)
- 多策略信号聚合
- 信号冲突处理
- 信号权重计算
- 最终信号决策

### 5. 风险管理模块 (`src/risk_management/`)

#### 仓位管理 (`position_manager.py`)
- **固定比例法** - 基于账户风险比例
- **凯利公式法** - 基于胜率和盈亏比
- **波动率调整法** - 根据市场波动调整
- **金字塔加仓法** - 盈利后分级加仓

#### 止损止盈 (`stop_loss_take_profit.py`)
- **固定百分比止损** - 简单固定比例
- **ATR止损** - 基于波动率
- **技术位止损** - 基于支撑阻力
- **移动止盈** - 跟踪止盈
- **动态止损止盈** - 根据盈利调整

#### 风险检查器 (`risk_checker.py`)
- 单笔风险检查
- 账户风险检查
- 最大回撤检查
- 连续亏损检查
- 综合风险评估

#### 风险监控 (`risk_monitor.py`)
- 实时风险监控
- 风险指标计算
- 风险预警（三级预警）
- 风险报告生成

### 6. API接口扩展 (`src/api/routes/`)

#### 技术分析API (`technical_analysis.py`)
- `GET /api/v1/indicators` - 计算技术指标
- `GET /api/v1/patterns` - 识别价格行为模式
- `GET /api/v1/support-resistance` - 获取支撑阻力位

#### 策略API (`strategies.py`)
- `GET /api/v1/strategies` - 获取策略列表
- `POST /api/v1/strategies/{id}/analyze` - 执行策略分析
- `GET /api/v1/signals` - 获取交易信号

### 7. 命令行工具 (`scripts/`)

#### 市场分析脚本 (`analyze_market.py`)
```bash
python scripts/analyze_market.py --symbol BTC/USDT --strategy trend_following
```

#### 策略回测脚本 (`backtest_strategy.py`)
```bash
python scripts/backtest_strategy.py --strategy trend_following --symbol BTC/USDT --start 2024-01-01 --end 2024-12-31
```

### 8. 测试文件 (`tests/`)

- `test_indicators.py` - 技术指标测试
- `test_strategies.py` - 策略测试
- `test_risk_management.py` - 风险管理测试

## 使用示例

### 1. 计算技术指标

```python
from src.trading_engine.indicators import IndicatorManager
import pandas as pd

# 初始化指标管理器
manager = IndicatorManager()

# 准备数据
data = pd.DataFrame({
    'open': [...],
    'high': [...],
    'low': [...],
    'close': [...],
    'volume': [...]
})

# 计算单个指标
ma = manager.calculate(data, 'ma', period=20)
rsi = manager.calculate(data, 'rsi', period=14)

# 批量计算多个指标
indicators = {
    'ma': {'period': 20},
    'ema': {'period': 50},
    'rsi': {'period': 14},
    'macd': {}
}
results = manager.calculate_multiple(data, indicators)
```

### 2. 使用交易策略

```python
from src.trading_engine.strategies import TrendFollowingStrategy

# 初始化策略
strategy = TrendFollowingStrategy()

# 分析市场
analysis = strategy.analyze(data)

# 生成信号
signals = strategy.generate_signals(data, analysis)

for signal in signals:
    print(f"信号: {signal['signal']}")
    print(f"入场价: {signal['entry_price']}")
    print(f"止损: {signal['stop_loss']}")
    print(f"止盈: {signal['take_profit']}")
```

### 3. 风险管理

```python
from src.risk_management import PositionManager, RiskChecker

# 仓位管理
position_manager = PositionManager(account_balance=10000)
position_size = position_manager.calculate_fixed_ratio(
    entry_price=100,
    stop_loss=95,
    risk_per_trade=0.02
)

# 风险检查
risk_checker = RiskChecker(account_balance=10000)
risk_result = risk_checker.check_all(
    entry_price=100,
    stop_loss=95,
    position_size=position_size
)

if risk_result['passed']:
    print("风险检查通过")
else:
    print("风险检查失败")
```

### 4. 多策略组合

```python
from src.trading_engine.strategies import StrategyManager
from src.trading_engine.strategies import (
    TrendFollowingStrategy,
    MeanReversionStrategy,
    MomentumStrategy
)

# 创建策略管理器
manager = StrategyManager()

# 添加多个策略
manager.add_strategy(TrendFollowingStrategy())
manager.add_strategy(MeanReversionStrategy())
manager.add_strategy(MomentumStrategy())

# 运行所有策略
all_signals = manager.run_all_strategies(data)

# 聚合信号
aggregated_signals = manager.aggregate_signals(all_signals)
```

## 技术特点

1. **模块化设计** - 各模块独立，易于维护和扩展
2. **类型注解** - 完整的类型提示，提高代码可读性
3. **错误处理** - 完善的异常处理和日志记录
4. **性能优化** - 使用缓存和向量化计算
5. **可配置** - 所有参数可配置
6. **可测试** - 提供完整的单元测试

## 依赖库

```
pandas>=1.5.0
numpy>=1.23.0
ccxt>=4.0.0
fastapi>=0.100.0
pytest>=7.4.0
```

## 下一步计划

1. 完善回测引擎
2. 添加更多策略
3. 实现实时交易执行
4. 添加机器学习模型
5. 完善Web界面

## 文件结构

```
/opt/Crypto-Trade/
├── src/
│   ├── trading_engine/
│   │   ├── indicators/          # 技术指标
│   │   ├── price_action/        # 价格行为
│   │   ├── strategies/          # 交易策略
│   │   └── signals/             # 信号生成
│   ├── risk_management/         # 风险管理
│   └── api/
│       └── routes/              # API路由
├── scripts/                     # 命令行工具
├── tests/                       # 测试文件
└── docs/                        # 文档
```

## 贡献者

- 系统架构师
- Python开发专家

## 许可证

MIT License
