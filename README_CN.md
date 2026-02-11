# LLM-Crypto-Trade：加密货币自动化分析系统

专业的加密货币市场数据分析与交易信号生成系统，采用全栈架构，集成 AI 智能分析、可配置信号监控和暗色主题交易仪表盘。

> **[English Documentation](./README.md)**

## 项目简介

LLM-Crypto-Trade 是一个全栈加密货币自动化分析系统，提供以下核心能力：

- **实时行情数据**：通过 ccxt 从交易所获取 OHLCV K线数据
- **技术指标分析**：全面的指标计算（MA、RSI、MACD、布林带、ADX、ATR 等）
- **价格行为分析**：基于 Al Brooks 价格行为理论，包含突破分析、回撤检测、交易区间识别、多空力量评估、MACD 辅助分析
- **策略引擎**：内置多种交易策略 — 趋势跟踪、均值回归、动量策略
- **AI 智能分析**：集成 AI 分析器，使用大语言模型生成结构化交易信号
- **可配置信号监控**：按交易对/周期调度策略执行，信号持久化存储并自动清理
- **回测系统**：历史数据回测，生成收益指标与策略评级
- **Web 仪表盘**：暗色主题专业交易界面，实时图表、策略管理、系统配置一体化

## 技术栈

### 后端
| 组件 | 技术 |
|------|------|
| 语言/框架 | Python 3.9+、FastAPI |
| 数据库 | TimescaleDB（时序数据）、PostgreSQL（元数据）、Redis（缓存） |
| 消息队列 | RabbitMQ |
| 数据分析 | Pandas、NumPy |
| 交易所集成 | ccxt（Binance 等） |
| AI 服务 | 可配置 AI 分析器，支持多种大语言模型 |
| 日志 | Loguru |

### 前端
| 组件 | 技术 |
|------|------|
| 框架 | React 18 + TypeScript 5 + Vite 7 |
| UI 组件库 | Ant Design 6（暗色主题） |
| 样式 | Tailwind CSS 4 |
| 状态管理 | Zustand 5（客户端）+ TanStack Query 5（服务端） |
| 图表 | TradingView Lightweight Charts 5（K线）+ ECharts 6（统计图表） |
| 路由 | React Router 7（懒加载） |
| 实时数据 | 原生 WebSocket（指数退避重连） |

### 部署
| 组件 | 技术 |
|------|------|
| 容器化 | Docker、Docker Compose |
| 反向代理 | Nginx（SPA 路由 + API 代理） |

## 功能特性

### 信号监控系统

核心功能是可配置的信号监控系统，用户可以：

1. **创建监控任务** — 选择交易对（如 BTC/USDT）、策略和K线周期
2. **自动调度执行** — 系统按配置的周期使用 asyncio 后台调度器定时执行任务
3. **手动触发** — 在仪表盘中随时手动执行任意任务
4. **信号持久化** — 生成的信号存储在 JSON 文件中，自动过期（24小时）和清理（最多500条）

**可用策略：**
| 策略 | 说明 |
|------|------|
| 趋势跟踪 | 基于 MA/EMA 交叉配合 MACD 和 ADX 确认 |
| 均值回归 | 布林带 + RSI 超买超卖检测 |
| 动量策略 | 基于变化率和动量的信号生成 |
| AI分析 | 大语言模型驱动的分析，输出结构化 JSON 信号 |

### 通知推送系统

集成多渠道信号通知，交易信号触发后自动推送到配置的通知渠道：

**支持渠道：**
| 渠道 | 配置项 | 说明 |
|------|--------|------|
| Telegram | `bot_token` + `chat_id` | 通过 Telegram Bot API 推送消息 |
| 飞书 | `webhook_url` + `secret`（可选） | 通过飞书自定义机器人 Webhook 推送 |

**核心功能：**
- **渠道管理** — 支持添加、编辑、删除和启用/禁用通知渠道
- **全局设置** — 可分别控制买入信号、卖出信号、持有信号的通知开关
- **敏感信息脱敏** — API 返回的 `bot_token`、`secret` 等字段自动脱敏显示
- **测试发送** — 配置完成后可发送测试消息验证渠道连通性
- **JSON 持久化** — 配置存储在 `data/notification_config.json`，与信号监控配置模式一致

### 登录认证

单用户 Bearer Token 认证系统，保护所有业务 API 端点：

**认证流程：**
1. 首次部署自动初始化默认凭据（用户名 `admin`，密码 `crypto2024`）
2. 使用默认凭据登录后，系统强制要求修改密码
3. 修改密码后重新登录，正常进入仪表盘

**技术实现：**
- 密码哈希：`pbkdf2_hmac(SHA-256, 100000 轮)`，随机盐值
- Token：`secrets.token_hex(32)` 生成，内存存储，24 小时过期
- 中间件拦截：所有非白名单路径自动验证 `Authorization: Bearer <token>` 头
- 白名单路径：`/`、`/health`、`/docs`、`/redoc`、`/openapi.json`、`/metrics`、登录接口
- 前端守卫：未登录自动跳转登录页，需改密码时跳转改密页
- Token 持久化：前端通过 `localStorage`（zustand persist）保存，关闭浏览器后仍有效

### 价格行为分析

基于 Al Brooks 价格行为理论：

- **突破分析** — 识别突破形态，结合成交量确认
- **回撤检测** — 基于斐波那契的回撤水平分析
- **交易区间** — 检测盘整区域和区间边界
- **多空力量** — 衡量买卖双方压力强度
- **MACD 辅助** — 增强型 MACD 分析，含背离检测

### AI 分析服务

- 可配置的大语言模型提供商和模型设置
- 6 个预置提示词模板：综合行情分析、入场时机判断、风险评估、趋势研判、支撑阻力分析、策略建议
- 信号生成提示词输出结构化 JSON（signal_type、confidence、入场/止损/目标价位）
- 与信号监控调度器无缝集成

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 20+ & pnpm（前端）
- Docker & Docker Compose（推荐）

### Docker 部署（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd LLM-Crypto-Trade

# 启动所有服务（后端 + 前端 + 基础设施）
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 手动安装

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac

# 安装 Python 依赖
pip install -r requirements.txt

# 启动后端
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# 启动前端（另开终端）
cd frontend
pnpm install
pnpm dev    # 访问 http://localhost:3000
```

### 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 | 80 | Nginx 托管 SPA + 反向代理 |
| 后端 API | 8000 | FastAPI 服务 |
| TimescaleDB | 5432 | 时序数据库 |
| Redis | 6379 | 缓存 |
| RabbitMQ | 5672 / 15672 | 消息队列 / 管理界面 |

## 项目结构

```
LLM-Crypto-Trade/
├── src/                              # 后端源代码
│   ├── api/                          # FastAPI 应用
│   │   ├── main.py                   # 应用入口，生命周期事件
│   │   └── routes/                   # API 路由模块
│   │       ├── market_data.py        # 行情数据端点
│   │       ├── strategies.py         # 策略分析与信号
│   │       ├── technical_analysis.py # 技术指标端点
│   │       ├── ai_analysis.py        # AI 分析端点
│   │       ├── settings.py           # 系统设置与信号监控
│   │       └── auth.py              # 认证（登录/登出/改密）
│   ├── config/                       # 配置管理
│   │   ├── settings.py               # 应用配置
│   │   ├── exchange_config_manager.py# 交易所配置
│   │   ├── signal_config_manager.py  # 信号监控任务 CRUD
│   │   ├── notification_config_manager.py # 通知渠道配置
│   │   └── auth_config_manager.py    # 认证凭据管理
│   ├── services/                     # 业务服务
│   │   ├── signal_scheduler.py       # 异步信号调度引擎
│   │   └── signal_store.py           # 信号持久化（JSON）
│   ├── ai_service/                   # AI 分析服务
│   │   ├── ai_analyzer.py            # 大语言模型集成
│   │   ├── config_manager.py         # AI 模型配置
│   │   └── prompts/templates.py      # 提示词模板
│   ├── trading_engine/               # 交易引擎
│   │   ├── indicators/               # 技术指标
│   │   ├── price_action/             # 价格行为分析模块
│   │   ├── signals/                  # 信号生成
│   │   └── strategies/               # 策略实现
│   ├── utils/                        # 工具类
│   ├── data_pipeline/                # 数据管道
│   ├── risk_management/              # 风险管理
│   └── backtesting/                  # 回测框架
├── frontend/                         # 前端项目
│   ├── src/
│   │   ├── api/                      # API 请求层
│   │   ├── components/               # 组件
│   │   │   ├── ui/                   #   通用 UI 组件
│   │   │   ├── layout/               #   布局组件
│   │   │   ├── business/             #   业务组件
│   │   │   └── charts/               #   图表组件
│   │   ├── hooks/                    # 自定义 Hooks
│   │   ├── pages/                    # 页面组件
│   │   ├── stores/                   # Zustand 状态
│   │   ├── styles/                   # 样式与主题
│   │   ├── types/                    # TypeScript 类型定义
│   │   └── utils/                    # 工具函数
│   ├── docker/                       # Nginx 配置
│   └── Dockerfile                    # 前端多阶段构建
├── tests/                            # 后端测试
├── data/                             # 运行时数据（JSON 配置与信号）
├── docker-compose.yml                # 开发环境编排
├── config/docker-compose.yml         # 生产环境编排
├── Dockerfile                        # 后端镜像
├── requirements.txt                  # Python 依赖
├── README.md                         # 英文文档
└── README_CN.md                      # 中文文档
```

## API 参考

启动服务后，访问以下地址查看完整 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/market/klines` | 获取K线数据 |
| GET | `/api/v1/strategies` | 获取策略列表 |
| POST | `/api/v1/strategies/{name}/analyze` | 执行策略分析 |
| GET | `/api/v1/signals` | 获取交易信号 |
| GET | `/api/v1/settings/signal-monitors` | 获取信号监控任务列表 |
| POST | `/api/v1/settings/signal-monitors` | 创建监控任务 |
| PUT | `/api/v1/settings/signal-monitors/{id}` | 更新监控任务 |
| DELETE | `/api/v1/settings/signal-monitors/{id}` | 删除监控任务 |
| POST | `/api/v1/settings/signal-monitors/{id}/run` | 手动触发执行 |
| POST | `/api/v1/ai/analyze` | 执行 AI 分析 |
| POST | `/api/v1/auth/login` | 用户登录，返回 Token |
| POST | `/api/v1/auth/logout` | 注销 Token |
| POST | `/api/v1/auth/change-password` | 修改密码（需认证） |
| GET | `/api/v1/auth/me` | 获取当前用户信息 |
| GET | `/api/v1/settings/notifications` | 获取通知配置 |
| PUT | `/api/v1/settings/notifications/settings` | 更新通知全局设置 |
| POST | `/api/v1/settings/notifications/channels` | 添加通知渠道 |
| PUT | `/api/v1/settings/notifications/channels/{id}` | 更新通知渠道 |
| DELETE | `/api/v1/settings/notifications/channels/{id}` | 删除通知渠道 |
| POST | `/api/v1/settings/notifications/channels/{id}/test` | 测试通知渠道 |

## 测试

```bash
# 运行信号配置测试
.venv/bin/python -m pytest tests/test_signal_config.py -v --noconftest

# 运行信号存储测试
.venv/bin/python -m pytest tests/test_signal_store.py -v --noconftest

# 运行价格行为测试
.venv/bin/python -m pytest tests/test_price_action_new.py -v --noconftest

# 运行全部测试
.venv/bin/python -m pytest tests/ -v
```

## 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 项目
2. 创建特性分支（`git checkout -b feature/YourFeature`）
3. 提交更改（`git commit -m '添加 YourFeature'`）
4. 推送到分支（`git push origin feature/YourFeature`）
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证。

## 致谢

**后端**：[FastAPI](https://fastapi.tiangolo.com/) · [TimescaleDB](https://www.timescale.com/) · [ccxt](https://github.com/ccxt/ccxt) · [Pandas](https://pandas.pydata.org/) · [Loguru](https://github.com/Delgan/loguru)

**前端**：[React](https://react.dev/) · [Ant Design](https://ant.design/) · [TradingView Lightweight Charts](https://tradingview.github.io/lightweight-charts/) · [ECharts](https://echarts.apache.org/) · [Zustand](https://zustand-demo.pmnd.rs/) · [TanStack Query](https://tanstack.com/query)

---

# 项目合规声明与免责条款

## 1. 项目定位

本项目（LLM-Crypto-Trade）仅为**加密货币相关技术的学术研究、AI算法演示与开源技术交流**使用，不构成任何金融产品、投资建议、理财服务或募资行为。

本项目**不面向任何虚拟货币/加密货币相关交易、炒作、发行、兑付等业务提供支持**，代码中不包含任何虚拟货币钱包、交易接口或金融功能。

## 2. 虚拟货币相关风险提示

- 虚拟货币不具有法定货币地位，其相关业务活动属于**非法金融活动**；
- 任何虚拟货币交易、炒作、融资、中介、代理等行为均不受法律保护。

本项目**严格拒绝**任何与虚拟货币、代币发行融资、虚拟货币交易相关的用途。

**任何人不得将本项目用于虚拟货币相关非法金融活动，否则后果自行承担**。
