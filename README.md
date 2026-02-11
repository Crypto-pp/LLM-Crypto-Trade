# Crypto-Trade: Cryptocurrency Automated Analysis System

A professional cryptocurrency market data analysis and trading signal generation system with a full-stack architecture, featuring AI-powered analysis, configurable signal monitoring, and a dark-themed trading dashboard.

> **[中文文档 / Chinese Documentation](./README_CN.md)**

## Overview

Crypto-Trade is a full-stack automated analysis system for cryptocurrency markets. It provides:

- **Real-time Market Data**: Fetch OHLCV candlestick data from exchanges via ccxt
- **Technical Analysis**: Comprehensive indicator calculations (MA, RSI, MACD, Bollinger Bands, ADX, ATR, etc.)
- **Price Action Analysis**: Al Brooks-inspired price action modules including breakout analysis, retracement detection, trading range identification, bull/bear power assessment, and MACD auxiliary analysis
- **Strategy Engine**: Multiple built-in strategies — Trend Following, Mean Reversion, and Momentum
- **AI-Powered Analysis**: Integrated AI analyzer that generates structured trading signals using LLM models
- **Configurable Signal Monitoring**: Schedule strategy execution per symbol/interval, with persistent signal storage and auto-cleanup
- **Backtesting**: Historical data backtesting with performance metrics and strategy rating
- **Web Dashboard**: Dark-themed professional trading interface with real-time charts, strategy management, and system configuration

## Tech Stack

### Backend
| Component | Technology |
|-----------|-----------|
| Language / Framework | Python 3.9+, FastAPI |
| Database | TimescaleDB (time-series), PostgreSQL (metadata), Redis (cache) |
| Message Queue | RabbitMQ |
| Data Analysis | Pandas, NumPy |
| Exchange Integration | ccxt (Binance and others) |
| AI Service | LLM integration via configurable AI analyzer |
| Logging | Loguru |

### Frontend
| Component | Technology |
|-----------|-----------|
| Framework | React 18 + TypeScript 5 + Vite 7 |
| UI Library | Ant Design 6 (dark theme) |
| Styling | Tailwind CSS 4 |
| State Management | Zustand 5 (client) + TanStack Query 5 (server) |
| Charts | TradingView Lightweight Charts 5 (candlestick) + ECharts 6 (statistics) |
| Routing | React Router 7 (lazy loading) |
| Real-time Data | Native WebSocket (exponential backoff reconnection) |

### Deployment
| Component | Technology |
|-----------|-----------|
| Containerization | Docker, Docker Compose |
| Reverse Proxy | Nginx (SPA routing + API proxy) |

## Features

### Signal Monitoring System

The core feature is a configurable signal monitoring system that allows users to:

1. **Create monitoring tasks** — Select a trading pair (e.g., BTC/USDT), a strategy, and a candlestick interval
2. **Automatic scheduling** — The system runs each task at the configured interval using an asyncio background scheduler
3. **Manual trigger** — Execute any task on-demand from the dashboard
4. **Signal persistence** — Generated signals are stored in JSON files with automatic expiration (24h) and cleanup (max 500 signals)

**Available Strategies:**
| Strategy | Description |
|----------|-------------|
| Trend Following | MA/EMA crossover with MACD and ADX confirmation |
| Mean Reversion | Bollinger Bands + RSI overbought/oversold detection |
| Momentum | Rate of change and momentum-based signal generation |
| AI Analysis | LLM-powered analysis with structured JSON signal output |

### Notification System

Multi-channel signal notification system that automatically pushes trading signals to configured channels:

**Supported Channels:**
| Channel | Configuration | Description |
|---------|--------------|-------------|
| Telegram | `bot_token` + `chat_id` | Push via Telegram Bot API |
| Feishu (Lark) | `webhook_url` + `secret` (optional) | Push via Feishu custom bot Webhook |

**Core Features:**
- **Channel Management** — Add, edit, delete, and enable/disable notification channels
- **Global Settings** — Independent toggle for buy, sell, and hold signal notifications
- **Sensitive Data Masking** — `bot_token`, `secret` and other sensitive fields are automatically masked in API responses
- **Test Send** — Send test messages to verify channel connectivity after configuration
- **JSON Persistence** — Configuration stored in `data/notification_config.json`, consistent with signal monitor config pattern

### Authentication

Single-user Bearer Token authentication system protecting all business API endpoints:

**Authentication Flow:**
1. Default credentials are auto-initialized on first deployment (username `admin`, password `crypto2024`)
2. After logging in with default credentials, the system enforces a mandatory password change
3. After changing the password, re-login to access the dashboard normally

**Technical Details:**
- Password hashing: `pbkdf2_hmac(SHA-256, 100,000 iterations)` with random salt
- Token: Generated via `secrets.token_hex(32)`, stored in memory, 24-hour expiry
- Middleware interception: All non-whitelisted paths require `Authorization: Bearer <token>` header
- Whitelisted paths: `/`, `/health`, `/docs`, `/redoc`, `/openapi.json`, `/metrics`, login endpoint
- Frontend guard: Unauthenticated users redirected to login page; users requiring password change redirected to change-password page
- Token persistence: Frontend stores token in `localStorage` (zustand persist), survives browser close

### Price Action Analysis

Built on Al Brooks price action theory:

- **Breakout Analysis** — Identifies breakout patterns with volume confirmation
- **Retracement Detection** — Fibonacci-based retracement level analysis
- **Trading Range** — Detects consolidation zones and range boundaries
- **Bull/Bear Power** — Measures buying/selling pressure strength
- **MACD Auxiliary** — Enhanced MACD analysis with divergence detection

### AI Analysis Service

- Configurable LLM provider and model settings
- 6 pre-built prompt templates: Comprehensive Analysis, Entry Timing, Risk Assessment, Trend Analysis, Support/Resistance, Strategy Advice
- Signal generation prompt that outputs structured JSON (signal_type, confidence, entry/stop/target prices)
- Seamless integration with the signal monitoring scheduler

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 20+ & pnpm (frontend)
- Docker & Docker Compose (recommended)

### Docker Deployment (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd Crypto-Trade

# Start all services (backend + frontend + infrastructure)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac

# Install Python dependencies
pip install -r requirements.txt

# Start backend
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend (in another terminal)
cd frontend
pnpm install
pnpm dev    # http://localhost:3000
```

### Service Ports

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 80 | Nginx-hosted SPA + reverse proxy |
| Backend API | 8000 | FastAPI service |
| TimescaleDB | 5432 | Time-series database |
| Redis | 6379 | Cache |
| RabbitMQ | 5672 / 15672 | Message queue / Management UI |

## Project Structure

```
Crypto-Trade/
├── src/                              # Backend source code
│   ├── api/                          # FastAPI application
│   │   ├── main.py                   # App entry, lifespan events
│   │   └── routes/                   # API route modules
│   │       ├── market_data.py        # Market data endpoints
│   │       ├── strategies.py         # Strategy analysis & signals
│   │       ├── technical_analysis.py # Technical indicator endpoints
│   │       ├── ai_analysis.py        # AI analysis endpoints
│   │       ├── settings.py           # System settings & signal monitors
│   │       └── auth.py              # Authentication (login/logout/change-password)
│   ├── config/                       # Configuration management
│   │   ├── settings.py               # Application settings
│   │   ├── exchange_config_manager.py# Exchange configuration
│   │   ├── signal_config_manager.py  # Signal monitor task CRUD
│   │   ├── notification_config_manager.py # Notification channel config
│   │   └── auth_config_manager.py    # Authentication credential management
│   ├── services/                     # Business services
│   │   ├── signal_scheduler.py       # Async signal scheduling engine
│   │   └── signal_store.py           # Signal persistence (JSON)
│   ├── ai_service/                   # AI analysis service
│   │   ├── ai_analyzer.py            # LLM integration
│   │   ├── config_manager.py         # AI model configuration
│   │   └── prompts/templates.py      # Prompt templates
│   ├── trading_engine/               # Trading engine
│   │   ├── indicators/               # Technical indicators
│   │   ├── price_action/             # Price action analysis modules
│   │   ├── signals/                  # Signal generation
│   │   └── strategies/               # Strategy implementations
│   ├── utils/                        # Utilities
│   ├── data_pipeline/                # Data pipeline
│   ├── risk_management/              # Risk management
│   └── backtesting/                  # Backtesting framework
├── frontend/                         # Frontend project
│   ├── src/
│   │   ├── api/                      # API request layer
│   │   ├── components/               # Components
│   │   │   ├── ui/                   #   Reusable UI components
│   │   │   ├── layout/               #   Layout components
│   │   │   ├── business/             #   Business components
│   │   │   └── charts/               #   Chart components
│   │   ├── hooks/                    # Custom React hooks
│   │   ├── pages/                    # Page components
│   │   ├── stores/                   # Zustand state stores
│   │   ├── styles/                   # Styles & theme
│   │   ├── types/                    # TypeScript type definitions
│   │   └── utils/                    # Utility functions
│   ├── docker/                       # Nginx configuration
│   └── Dockerfile                    # Frontend multi-stage build
├── tests/                            # Backend tests
├── data/                             # Runtime data (JSON configs & signals)
├── docker-compose.yml                # Development environment
├── config/docker-compose.yml         # Production environment
├── Dockerfile                        # Backend image
├── requirements.txt                  # Python dependencies
├── README.md                         # English documentation
└── README_CN.md                      # Chinese documentation
```

## API Reference

After starting the service, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/market/klines` | Fetch candlestick data |
| GET | `/api/v1/strategies` | List available strategies |
| POST | `/api/v1/strategies/{name}/analyze` | Run strategy analysis |
| GET | `/api/v1/signals` | Get trading signals |
| GET | `/api/v1/settings/signal-monitors` | List signal monitor tasks |
| POST | `/api/v1/settings/signal-monitors` | Create monitor task |
| PUT | `/api/v1/settings/signal-monitors/{id}` | Update monitor task |
| DELETE | `/api/v1/settings/signal-monitors/{id}` | Delete monitor task |
| POST | `/api/v1/settings/signal-monitors/{id}/run` | Trigger task execution |
| POST | `/api/v1/ai/analyze` | Run AI analysis |
| POST | `/api/v1/auth/login` | User login, returns Token |
| POST | `/api/v1/auth/logout` | Invalidate Token |
| POST | `/api/v1/auth/change-password` | Change password (authenticated) |
| GET | `/api/v1/auth/me` | Get current user info |
| GET | `/api/v1/settings/notifications` | Get notification config |
| PUT | `/api/v1/settings/notifications/settings` | Update notification settings |
| POST | `/api/v1/settings/notifications/channels` | Add notification channel |
| PUT | `/api/v1/settings/notifications/channels/{id}` | Update notification channel |
| DELETE | `/api/v1/settings/notifications/channels/{id}` | Delete notification channel |
| POST | `/api/v1/settings/notifications/channels/{id}/test` | Test notification channel |

## Testing

```bash
# Run signal config tests
.venv/bin/python -m pytest tests/test_signal_config.py -v --noconftest

# Run signal store tests
.venv/bin/python -m pytest tests/test_signal_store.py -v --noconftest

# Run price action tests
.venv/bin/python -m pytest tests/test_price_action_new.py -v --noconftest

# Run all tests
.venv/bin/python -m pytest tests/ -v
```

## Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/YourFeature`)
3. Commit your changes (`git commit -m 'Add YourFeature'`)
4. Push to the branch (`git push origin feature/YourFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Acknowledgements

**Backend**: [FastAPI](https://fastapi.tiangolo.com/) · [TimescaleDB](https://www.timescale.com/) · [ccxt](https://github.com/ccxt/ccxt) · [Pandas](https://pandas.pydata.org/) · [Loguru](https://github.com/Delgan/loguru)

**Frontend**: [React](https://react.dev/) · [Ant Design](https://ant.design/) · [TradingView Lightweight Charts](https://tradingview.github.io/lightweight-charts/) · [ECharts](https://echarts.apache.org/) · [Zustand](https://zustand-demo.pmnd.rs/) · [TanStack Query](https://tanstack.com/query)

---

# Compliance Disclaimer

## 1. Project Purpose

This project (Crypto-Trade) is intended solely for **academic research on cryptocurrency-related technologies, AI algorithm demonstration, and open-source technical exchange**. It does not constitute any financial product, investment advice, financial service, or fundraising activity.

This project **does not provide support for any virtual currency / cryptocurrency trading, speculation, issuance, or redemption business**. The codebase does not contain any virtual currency wallet, trading interface, or financial functionality.

## 2. Virtual Currency Risk Warning

- Virtual currencies do not have legal tender status; related business activities constitute **illegal financial activities**;
- Any virtual currency trading, speculation, financing, intermediary, or agency activities are **not protected by law**.

This project **strictly rejects** any use related to virtual currencies, token issuance financing, or virtual currency trading.

**No person shall use this project for illegal financial activities related to virtual currencies; violators bear all consequences.**

**Donation Address(TRC20) : THZiJYfHGV27XvMAidYT1nBGB1cSBGLJiq**
<img width="477" height="459" alt="image" src="https://github.com/user-attachments/assets/21f27011-8bc0-456a-9501-987e8e2e2c06" />

