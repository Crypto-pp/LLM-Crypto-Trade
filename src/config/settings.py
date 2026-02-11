"""
系统配置管理

使用 Pydantic 进行配置验证，支持从环境变量和 .env 文件加载配置。
"""

import os
from functools import lru_cache
from typing import Optional, List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """数据库配置"""
    # TimescaleDB/PostgreSQL配置
    host: str = Field(default="localhost", description="数据库主机")
    port: int = Field(default=5432, description="数据库端口")
    user: str = Field(default="postgres", description="数据库用户")
    password: str = Field(default="", description="数据库密码")
    database: str = Field(default="crypto_db", description="数据库名称")

    # 连接池配置
    pool_size: int = Field(default=20, description="连接池大小")
    max_overflow: int = Field(default=10, description="最大溢出连接数")
    pool_timeout: int = Field(default=30, description="连接超时（秒）")
    pool_recycle: int = Field(default=3600, description="连接回收时间（秒）")

    model_config = SettingsConfigDict(env_prefix="DB_")

    @property
    def url(self) -> str:
        """生成数据库连接URL"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def async_url(self) -> str:
        """生成异步数据库连接URL"""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class RedisSettings(BaseSettings):
    """Redis配置"""
    host: str = Field(default="localhost", description="Redis主机")
    port: int = Field(default=6379, description="Redis端口")
    password: Optional[str] = Field(default=None, description="Redis密码")
    db: int = Field(default=0, description="Redis数据库编号")

    # 连接池配置
    max_connections: int = Field(default=50, description="最大连接数")
    socket_timeout: int = Field(default=5, description="Socket超时（秒）")
    socket_connect_timeout: int = Field(default=5, description="连接超时（秒）")

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    @property
    def url(self) -> str:
        """生成Redis连接URL"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class RabbitMQSettings(BaseSettings):
    """RabbitMQ配置"""
    host: str = Field(default="localhost", description="RabbitMQ主机")
    port: int = Field(default=5672, description="RabbitMQ端口")
    user: str = Field(default="guest", description="RabbitMQ用户")
    password: str = Field(default="guest", description="RabbitMQ密码")
    vhost: str = Field(default="/", description="虚拟主机")

    # 连接配置
    heartbeat: int = Field(default=60, description="心跳间隔（秒）")
    connection_attempts: int = Field(default=3, description="连接重试次数")
    retry_delay: int = Field(default=2, description="重试延迟（秒）")

    model_config = SettingsConfigDict(env_prefix="RABBITMQ_")

    @property
    def url(self) -> str:
        """生成RabbitMQ连接URL"""
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}/{self.vhost}"


class LoggingSettings(BaseSettings):
    """日志配置"""
    level: str = Field(default="INFO", description="日志级别")
    format: str = Field(
        default="json",
        description="日志格式: json 或 text"
    )

    # 文件日志配置
    log_dir: str = Field(default="logs", description="日志目录")
    rotation: str = Field(default="500 MB", description="日志轮转大小")
    retention: str = Field(default="30 days", description="日志保留时间")
    compression: str = Field(default="zip", description="日志压缩格式")

    # 控制台输出
    console_output: bool = Field(default=True, description="是否输出到控制台")

    model_config = SettingsConfigDict(env_prefix="LOG_")

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """验证日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in valid_levels:
            raise ValueError(f"日志级别必须是: {', '.join(valid_levels)}")
        return v


class AISettings(BaseSettings):
    """AI模型配置"""
    default_provider: str = Field(default="deepseek", description="默认AI提供商")

    # DeepSeek
    deepseek_api_key: str = Field(default="", description="DeepSeek API Key")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", description="DeepSeek API地址")
    deepseek_model: str = Field(default="deepseek-chat", description="DeepSeek模型")

    # Gemini
    gemini_api_key: str = Field(default="", description="Gemini API Key")
    gemini_model: str = Field(default="gemini-2.0-flash", description="Gemini模型")

    # OpenAI兼容
    openai_api_key: str = Field(default="", description="OpenAI API Key")
    openai_base_url: str = Field(default="https://api.openai.com/v1", description="OpenAI API地址")
    openai_model: str = Field(default="gpt-4o", description="OpenAI模型")

    # 通用参数
    max_tokens: int = Field(default=4096, description="最大生成token数")
    temperature: float = Field(default=0.3, description="生成温度")
    timeout: int = Field(default=60, description="请求超时（秒）")

    model_config = SettingsConfigDict(env_prefix="AI_")


class ExchangeAPISettings(BaseSettings):
    """交易所API配置"""
    # Binance
    binance_api_key: Optional[str] = Field(default=None, description="Binance API Key")
    binance_api_secret: Optional[str] = Field(default=None, description="Binance API Secret")

    # OKX
    okx_api_key: Optional[str] = Field(default=None, description="OKX API Key")
    okx_api_secret: Optional[str] = Field(default=None, description="OKX API Secret")
    okx_passphrase: Optional[str] = Field(default=None, description="OKX Passphrase")

    # Coinbase
    coinbase_api_key: Optional[str] = Field(default=None, description="Coinbase API Key")
    coinbase_api_secret: Optional[str] = Field(default=None, description="Coinbase API Secret")

    model_config = SettingsConfigDict(env_prefix="EXCHANGE_")


class SystemSettings(BaseSettings):
    """系统配置"""
    # 基本信息
    app_name: str = Field(default="Crypto-Trade", description="应用名称")
    app_version: str = Field(default="1.0.0", description="应用版本")
    environment: str = Field(default="development", description="运行环境")
    debug: bool = Field(default=False, description="调试模式")

    # 时区配置
    timezone: str = Field(default="UTC", description="时区")

    # 数据目录
    data_dir: str = Field(default="data", description="数据目录")

    # API配置
    api_host: str = Field(default="0.0.0.0", description="API主机")
    api_port: int = Field(default=8000, description="API端口")
    api_workers: int = Field(default=4, description="API工作进程数")

    # CORS配置
    cors_origins: List[str] = Field(
        default=["*"],
        description="允许的CORS源"
    )

    model_config = SettingsConfigDict(env_prefix="SYSTEM_")

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """验证运行环境"""
        valid_envs = ["development", "staging", "production"]
        if v not in valid_envs:
            raise ValueError(f"环境必须是: {', '.join(valid_envs)}")
        return v


class Settings(BaseSettings):
    """主配置类"""
    # 子配置
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    rabbitmq: RabbitMQSettings = Field(default_factory=RabbitMQSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    exchange: ExchangeAPISettings = Field(default_factory=ExchangeAPISettings)
    ai: AISettings = Field(default_factory=AISettings)
    system: SystemSettings = Field(default_factory=SystemSettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def __init__(self, **kwargs):
        """初始化配置"""
        super().__init__(**kwargs)
        # 创建必要的目录
        self._create_directories()

    def _create_directories(self):
        """创建必要的目录"""
        directories = [
            self.logging.log_dir,
            self.system.data_dir,
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """
    获取配置单例

    使用 lru_cache 确保配置只加载一次
    """
    return Settings()
