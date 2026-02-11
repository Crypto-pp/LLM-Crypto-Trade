"""
数据库初始化脚本

读取数据库架构文档，创建所有表结构、索引和初始数据。
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from src.utils.database import get_db_manager
from src.utils.logger import setup_logging, get_logger

# 设置日志
setup_logging()
logger = get_logger(__name__)


# TimescaleDB表DDL
TIMESCALE_TABLES = [
    # K线数据表
    """
    CREATE TABLE IF NOT EXISTS klines (
        time TIMESTAMPTZ NOT NULL,
        exchange VARCHAR(20) NOT NULL,
        symbol VARCHAR(20) NOT NULL,
        interval VARCHAR(10) NOT NULL,
        open DECIMAL(20, 8) NOT NULL,
        high DECIMAL(20, 8) NOT NULL,
        low DECIMAL(20, 8) NOT NULL,
        close DECIMAL(20, 8) NOT NULL,
        volume DECIMAL(20, 8) NOT NULL,
        quote_volume DECIMAL(20, 8),
        trades_count INTEGER,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        PRIMARY KEY (time, exchange, symbol, interval)
    );
    """,

    # Tick数据表
    """
    CREATE TABLE IF NOT EXISTS ticks (
        time TIMESTAMPTZ NOT NULL,
        exchange VARCHAR(20) NOT NULL,
        symbol VARCHAR(20) NOT NULL,
        price DECIMAL(20, 8) NOT NULL,
        quantity DECIMAL(20, 8) NOT NULL,
        side VARCHAR(4),
        trade_id BIGINT,
        is_buyer_maker BOOLEAN,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        PRIMARY KEY (time, exchange, symbol, trade_id)
    );
    """,

    # 订单簿快照表
    """
    CREATE TABLE IF NOT EXISTS orderbook_snapshots (
        time TIMESTAMPTZ NOT NULL,
        exchange VARCHAR(20) NOT NULL,
        symbol VARCHAR(20) NOT NULL,
        bids JSONB NOT NULL,
        asks JSONB NOT NULL,
        checksum BIGINT,
        depth_level INTEGER DEFAULT 20,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        PRIMARY KEY (time, exchange, symbol)
    );
    """,

    # 技术指标表
    """
    CREATE TABLE IF NOT EXISTS indicators (
        time TIMESTAMPTZ NOT NULL,
        symbol VARCHAR(20) NOT NULL,
        interval VARCHAR(10) NOT NULL,
        indicator_name VARCHAR(50) NOT NULL,
        indicator_value JSONB NOT NULL,
        parameters JSONB,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        PRIMARY KEY (time, symbol, interval, indicator_name)
    );
    """,

    # 交易信号表
    """
    CREATE TABLE IF NOT EXISTS signals (
        signal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        time TIMESTAMPTZ NOT NULL,
        symbol VARCHAR(20) NOT NULL,
        exchange VARCHAR(20) NOT NULL,
        strategy VARCHAR(50) NOT NULL,
        action VARCHAR(10) NOT NULL,
        price DECIMAL(20, 8) NOT NULL,
        confidence DECIMAL(3, 2),
        priority VARCHAR(10),
        valid_until TIMESTAMPTZ,
        status VARCHAR(20) DEFAULT 'PENDING',
        metadata JSONB,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    """,
]


# PostgreSQL关系表DDL
POSTGRES_TABLES = [
    # 交易所配置表
    """
    CREATE TABLE IF NOT EXISTS exchanges (
        exchange_id VARCHAR(20) PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        website VARCHAR(255),
        api_url VARCHAR(255),
        ws_url VARCHAR(255),
        rate_limit_config JSONB,
        api_key TEXT,
        api_secret TEXT,
        enabled BOOLEAN DEFAULT true,
        priority INTEGER DEFAULT 100,
        notes TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    """,

    # 交易对配置表
    """
    CREATE TABLE IF NOT EXISTS symbols (
        symbol_id SERIAL PRIMARY KEY,
        exchange_id VARCHAR(20) NOT NULL REFERENCES exchanges(exchange_id) ON DELETE CASCADE,
        symbol VARCHAR(20) NOT NULL,
        base_currency VARCHAR(10) NOT NULL,
        quote_currency VARCHAR(10) NOT NULL,
        price_precision INTEGER DEFAULT 8,
        volume_precision INTEGER DEFAULT 8,
        min_order_size DECIMAL(20, 8),
        max_order_size DECIMAL(20, 8),
        enabled BOOLEAN DEFAULT true,
        priority INTEGER DEFAULT 100,
        tags TEXT[],
        notes TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        UNIQUE(exchange_id, symbol)
    );
    """,

    # 策略配置表
    """
    CREATE TABLE IF NOT EXISTS strategies (
        strategy_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(100) NOT NULL,
        strategy_type VARCHAR(50) NOT NULL,
        description TEXT,
        parameters JSONB NOT NULL,
        symbols TEXT[],
        intervals TEXT[],
        enabled BOOLEAN DEFAULT true,
        risk_level INTEGER DEFAULT 3,
        max_positions INTEGER DEFAULT 1,
        stop_loss_pct DECIMAL(5, 2),
        take_profit_pct DECIMAL(5, 2),
        created_by VARCHAR(50),
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    """,

    # 数据采集任务表
    """
    CREATE TABLE IF NOT EXISTS collection_tasks (
        task_id SERIAL PRIMARY KEY,
        exchange_id VARCHAR(20) NOT NULL,
        symbol VARCHAR(20) NOT NULL,
        interval VARCHAR(10) NOT NULL,
        task_type VARCHAR(20) NOT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        start_time TIMESTAMPTZ,
        end_time TIMESTAMPTZ,
        progress INTEGER DEFAULT 0,
        processed_count INTEGER DEFAULT 0,
        error_message TEXT,
        retry_count INTEGER DEFAULT 0,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    """,

    # 数据质量指标表
    """
    CREATE TABLE IF NOT EXISTS data_quality_metrics (
        metric_id SERIAL PRIMARY KEY,
        exchange_id VARCHAR(20) NOT NULL,
        symbol VARCHAR(20) NOT NULL,
        interval VARCHAR(10) NOT NULL,
        metric_date DATE NOT NULL,
        total_records INTEGER DEFAULT 0,
        missing_records INTEGER DEFAULT 0,
        duplicate_records INTEGER DEFAULT 0,
        invalid_records INTEGER DEFAULT 0,
        completeness_rate DECIMAL(5, 2),
        accuracy_rate DECIMAL(5, 2),
        avg_latency_seconds DECIMAL(10, 3),
        created_at TIMESTAMPTZ DEFAULT NOW(),
        UNIQUE(exchange_id, symbol, interval, metric_date)
    );
    """,

    # 告警规则表
    """
    CREATE TABLE IF NOT EXISTS alert_rules (
        rule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name VARCHAR(100) NOT NULL,
        rule_type VARCHAR(50) NOT NULL,
        description TEXT,
        conditions JSONB NOT NULL,
        channels TEXT[] NOT NULL,
        priority VARCHAR(10) DEFAULT 'MEDIUM',
        cooldown_seconds INTEGER DEFAULT 300,
        enabled BOOLEAN DEFAULT true,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
    """,

    # 告警历史表
    """
    CREATE TABLE IF NOT EXISTS alert_history (
        alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        rule_id UUID REFERENCES alert_rules(rule_id) ON DELETE CASCADE,
        triggered_at TIMESTAMPTZ NOT NULL,
        message TEXT NOT NULL,
        channels TEXT[],
        status VARCHAR(20) DEFAULT 'pending',
        error_message TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    """,
]


def create_timescale_extension(db_manager):
    """创建TimescaleDB扩展"""
    logger.info("创建TimescaleDB扩展...")
    try:
        with db_manager.get_session() as session:
            session.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"))
            logger.info("✓ TimescaleDB扩展创建成功")
    except Exception as e:
        logger.error(f"✗ TimescaleDB扩展创建失败: {e}")
        raise


def create_tables(db_manager):
    """创建所有表"""
    logger.info("开始创建数据库表...")

    # 创建PostgreSQL关系表
    logger.info("创建PostgreSQL关系表...")
    for i, ddl in enumerate(POSTGRES_TABLES, 1):
        try:
            with db_manager.get_session() as session:
                session.execute(text(ddl))
            logger.info(f"✓ 关系表 {i}/{len(POSTGRES_TABLES)} 创建成功")
        except Exception as e:
            logger.error(f"✗ 关系表 {i} 创建失败: {e}")
            raise

    # 创建TimescaleDB时序表
    logger.info("创建TimescaleDB时序表...")
    for i, ddl in enumerate(TIMESCALE_TABLES, 1):
        try:
            with db_manager.get_session() as session:
                session.execute(text(ddl))
            logger.info(f"✓ 时序表 {i}/{len(TIMESCALE_TABLES)} 创建成功")
        except Exception as e:
            logger.error(f"✗ 时序表 {i} 创建失败: {e}")
            raise


def create_hypertables(db_manager):
    """创建TimescaleDB超表"""
    logger.info("创建TimescaleDB超表...")

    hypertables = [
        ("klines", "1 day"),
        ("ticks", "1 hour"),
        ("orderbook_snapshots", "1 hour"),
        ("indicators", "1 day"),
        ("signals", "1 day"),
    ]

    for table_name, chunk_interval in hypertables:
        try:
            with db_manager.get_session() as session:
                session.execute(text(f"""
                    SELECT create_hypertable(
                        '{table_name}',
                        'time',
                        chunk_time_interval => INTERVAL '{chunk_interval}',
                        if_not_exists => TRUE
                    );
                """))
            logger.info(f"✓ 超表 {table_name} 创建成功 (分区: {chunk_interval})")
        except Exception as e:
            logger.warning(f"⚠ 超表 {table_name} 可能已存在: {e}")


def create_indexes(db_manager):
    """创建索引"""
    logger.info("创建索引...")

    indexes = [
        # klines索引
        "CREATE INDEX IF NOT EXISTS idx_klines_symbol_time ON klines (symbol, time DESC);",
        "CREATE INDEX IF NOT EXISTS idx_klines_exchange_symbol ON klines (exchange, symbol, time DESC);",
        "CREATE INDEX IF NOT EXISTS idx_klines_interval ON klines (interval, time DESC);",
        "CREATE INDEX IF NOT EXISTS idx_klines_lookup ON klines (exchange, symbol, interval, time DESC);",

        # ticks索引
        "CREATE INDEX IF NOT EXISTS idx_ticks_symbol_time ON ticks (symbol, time DESC);",
        "CREATE INDEX IF NOT EXISTS idx_ticks_exchange_symbol ON ticks (exchange, symbol, time DESC);",

        # signals索引
        "CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals (symbol, time DESC);",
        "CREATE INDEX IF NOT EXISTS idx_signals_strategy ON signals (strategy, time DESC);",
        "CREATE INDEX IF NOT EXISTS idx_signals_status ON signals (status, time DESC);",

        # exchanges索引
        "CREATE INDEX IF NOT EXISTS idx_exchanges_enabled ON exchanges(enabled);",

        # symbols索引
        "CREATE INDEX IF NOT EXISTS idx_symbols_exchange ON symbols(exchange_id);",
        "CREATE INDEX IF NOT EXISTS idx_symbols_enabled ON symbols(enabled);",

        # strategies索引
        "CREATE INDEX IF NOT EXISTS idx_strategies_type ON strategies(strategy_type);",
        "CREATE INDEX IF NOT EXISTS idx_strategies_enabled ON strategies(enabled);",

        # collection_tasks索引
        "CREATE INDEX IF NOT EXISTS idx_tasks_status ON collection_tasks(status);",
        "CREATE INDEX IF NOT EXISTS idx_tasks_type ON collection_tasks(task_type);",
    ]

    for i, index_sql in enumerate(indexes, 1):
        try:
            with db_manager.get_session() as session:
                session.execute(text(index_sql))
            logger.info(f"✓ 索引 {i}/{len(indexes)} 创建成功")
        except Exception as e:
            logger.warning(f"⚠ 索引 {i} 可能已存在: {e}")


def insert_initial_data(db_manager):
    """插入初始数据"""
    logger.info("插入初始数据...")

    # 插入交易所配置
    exchanges_data = """
    INSERT INTO exchanges (exchange_id, name, api_url, ws_url, rate_limit_config, enabled)
    VALUES
        ('binance', 'Binance', 'https://api.binance.com', 'wss://stream.binance.com:9443/ws',
         '{"requests_per_minute": 1200, "weight_per_minute": 6000}'::jsonb, true),
        ('okx', 'OKX', 'https://www.okx.com', 'wss://ws.okx.com:8443/ws/v5/public',
         '{"requests_per_second": 20}'::jsonb, true),
        ('coinbase', 'Coinbase', 'https://api.coinbase.com', 'wss://ws-feed.exchange.coinbase.com',
         '{"requests_per_hour": 10000}'::jsonb, true)
    ON CONFLICT (exchange_id) DO NOTHING;
    """

    # 插入交易对配置
    symbols_data = """
    INSERT INTO symbols (exchange_id, symbol, base_currency, quote_currency, enabled, priority, tags)
    VALUES
        ('binance', 'BTC/USDT', 'BTC', 'USDT', true, 1, ARRAY['major', 'spot']),
        ('binance', 'ETH/USDT', 'ETH', 'USDT', true, 2, ARRAY['major', 'spot']),
        ('binance', 'BNB/USDT', 'BNB', 'USDT', true, 3, ARRAY['exchange-token', 'spot']),
        ('okx', 'BTC/USDT', 'BTC', 'USDT', true, 1, ARRAY['major', 'spot']),
        ('okx', 'ETH/USDT', 'ETH', 'USDT', true, 2, ARRAY['major', 'spot'])
    ON CONFLICT (exchange_id, symbol) DO NOTHING;
    """

    try:
        with db_manager.get_session() as session:
            session.execute(text(exchanges_data))
            session.execute(text(symbols_data))
        logger.info("✓ 初始数据插入成功")
    except Exception as e:
        logger.error(f"✗ 初始数据插入失败: {e}")
        raise


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("开始初始化数据库")
    logger.info("=" * 60)

    try:
        # 获取数据库管理器
        db_manager = get_db_manager()

        # 检查数据库连接
        if not db_manager.health_check():
            logger.error("数据库连接失败，请检查配置")
            sys.exit(1)

        # 创建TimescaleDB扩展
        create_timescale_extension(db_manager)

        # 创建表
        create_tables(db_manager)

        # 创建超表
        create_hypertables(db_manager)

        # 创建索引
        create_indexes(db_manager)

        # 插入初始数据
        insert_initial_data(db_manager)

        logger.info("=" * 60)
        logger.info("✓ 数据库初始化完成")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"✗ 数据库初始化失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
