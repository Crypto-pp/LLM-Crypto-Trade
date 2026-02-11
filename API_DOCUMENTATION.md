# Crypto-Trade API 文档

## API概述

Crypto-Trade提供RESTful API用于访问市场数据、技术分析、策略管理和回测功能。

**Base URL**: `http://localhost:8000/api/v1`

**认证**: 目前不需要认证（开发环境）

## 通用响应格式

### 成功响应
```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

### 错误响应
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述"
  }
}
```

## 市场数据 API

### 获取K线数据

**端点**: `GET /market/klines`

**参数**:
- `symbol` (string, required): 交易对，如 "BTC/USDT"
- `interval` (string, required): 时间间隔，如 "1m", "5m", "1h"
- `limit` (integer, optional): 返回数量，默认100

**示例请求**:
```bash
curl "http://localhost:8000/api/v1/market/klines?symbol=BTC/USDT&interval=1h&limit=100"
```

**示例响应**:
```json
{
  "success": true,
  "data": [
    {
      "timestamp": "2026-02-08T12:00:00Z",
      "open": 50000.0,
      "high": 50500.0,
      "low": 49800.0,
      "close": 50200.0,
      "volume": 1234.56
    }
  ]
}
```

### 获取实时行情

**端点**: `GET /market/ticker`

**参数**:
- `symbol` (string, required): 交易对

**示例请求**:
```bash
curl "http://localhost:8000/api/v1/market/ticker?symbol=BTC/USDT"
```

## 技术分析 API

### 计算技术指标

**端点**: `POST /analysis/indicators`

**请求体**:
```json
{
  "symbol": "BTC/USDT",
  "interval": "1h",
  "indicators": ["SMA", "RSI", "MACD"],
  "params": {
    "SMA": {"period": 20},
    "RSI": {"period": 14}
  }
}
```

**示例响应**:
```json
{
  "success": true,
  "data": {
    "SMA": [50100.0, 50150.0, ...],
    "RSI": [65.5, 64.2, ...],
    "MACD": {
      "macd": [120.5, ...],
      "signal": [115.3, ...],
      "histogram": [5.2, ...]
    }
  }
}
```

## 策略 API

### 获取策略列表

**端点**: `GET /strategies`

**示例响应**:
```json
{
  "success": true,
  "data": [
    {
      "id": "trend_following",
      "name": "趋势跟踪策略",
      "description": "基于移动平均线的趋势跟踪",
      "status": "active"
    }
  ]
}
```

### 执行策略

**端点**: `POST /strategies/execute`

**请求体**:
```json
{
  "strategy_id": "trend_following",
  "symbol": "BTC/USDT",
  "params": {
    "fast_period": 10,
    "slow_period": 20
  }
}
```

## 回测 API

### 创建回测任务

**端点**: `POST /backtest`

**请求体**:
```json
{
  "strategy_id": "trend_following",
  "symbol": "BTC/USDT",
  "start_date": "2026-01-01",
  "end_date": "2026-02-01",
  "initial_capital": 10000,
  "params": {
    "fast_period": 10,
    "slow_period": 20
  }
}
```

**示例响应**:
```json
{
  "success": true,
  "data": {
    "task_id": "bt_123456",
    "status": "pending"
  }
}
```

### 获取回测结果

**端点**: `GET /backtest/{task_id}`

**示例响应**:
```json
{
  "success": true,
  "data": {
    "task_id": "bt_123456",
    "status": "completed",
    "results": {
      "total_return": 15.5,
      "sharpe_ratio": 1.8,
      "max_drawdown": -8.2,
      "win_rate": 0.65,
      "total_trades": 45
    }
  }
}
```

## 健康检查 API

### 系统健康状态

**端点**: `GET /health`

**示例响应**:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-08T12:00:00Z",
  "checks": {
    "database": {
      "status": "healthy",
      "message": "Database connection successful"
    },
    "redis": {
      "status": "healthy",
      "message": "Redis connection successful"
    },
    "rabbitmq": {
      "status": "healthy",
      "message": "RabbitMQ connection successful"
    }
  }
}
```

## 错误码

| 错误码 | 描述 |
|--------|------|
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |
| 503 | 服务暂时不可用 |

## 限流

API限流规则：
- 默认: 60请求/分钟
- 响应头包含限流信息:
  - `X-RateLimit-Limit`: 限制数量
  - `X-RateLimit-Remaining`: 剩余数量

## WebSocket API

### 实时行情订阅

**端点**: `ws://localhost:8000/ws/ticker`

**订阅消息**:
```json
{
  "action": "subscribe",
  "symbols": ["BTC/USDT", "ETH/USDT"]
}
```

**推送消息**:
```json
{
  "symbol": "BTC/USDT",
  "price": 50200.0,
  "timestamp": "2026-02-08T12:00:00Z"
}
```

## SDK示例

### Python SDK

```python
import requests

class CryptoTradeAPI:
    def __init__(self, base_url="http://localhost:8000/api/v1"):
        self.base_url = base_url

    def get_klines(self, symbol, interval, limit=100):
        response = requests.get(
            f"{self.base_url}/market/klines",
            params={
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
        )
        return response.json()

# 使用示例
api = CryptoTradeAPI()
klines = api.get_klines("BTC/USDT", "1h")
print(klines)
```

## 更多信息

- 完整API文档: http://localhost:8000/docs
- ReDoc文档: http://localhost:8000/redoc
