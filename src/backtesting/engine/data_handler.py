"""
数据处理器

负责：
- 历史数据加载
- K线数据迭代
- 多时间周期支持
- 数据预处理
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Generator
from datetime import datetime
import logging
from pathlib import Path

from .event_engine import MarketEvent

logger = logging.getLogger(__name__)


class DataHandler:
    """
    数据处理器基类

    提供历史数据的迭代访问接口
    """

    # 最新K线缓存的最大长度，避免无限增长
    MAX_LATEST_BARS = 500

    def __init__(self, symbol: str, start_date: datetime, end_date: datetime):
        """
        初始化数据处理器

        Args:
            symbol: 交易对符号
            start_date: 开始日期
            end_date: 结束日期
        """
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.data = None
        self.current_index = 0

    def load_data(self) -> None:
        """加载数据（子类实现）"""
        raise NotImplementedError("Must implement load_data()")

    def get_latest_bar(self) -> Optional[Dict]:
        """获取最新的K线数据"""
        raise NotImplementedError("Must implement get_latest_bar()")

    def get_latest_bars(self, n: int = 1) -> Optional[List[Dict]]:
        """获取最新的N根K线"""
        raise NotImplementedError("Must implement get_latest_bars()")

    def update_bars(self) -> Optional[MarketEvent]:
        """更新K线数据，返回市场事件"""
        raise NotImplementedError("Must implement update_bars()")

    def continue_backtest(self) -> bool:
        """检查是否还有数据可以回测"""
        raise NotImplementedError("Must implement continue_backtest()")


class CSVDataHandler(DataHandler):
    """
    CSV文件数据处理器

    从CSV文件加载历史数据
    """

    def __init__(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        csv_dir: str
    ):
        """
        初始化CSV数据处理器

        Args:
            symbol: 交易对符号
            start_date: 开始日期
            end_date: 结束日期
            csv_dir: CSV文件目录
        """
        super().__init__(symbol, start_date, end_date)
        self.csv_dir = Path(csv_dir)
        self.bar_generator = None
        self.latest_bars = []
        self.load_data()

    def load_data(self) -> None:
        """从CSV文件加载数据"""
        csv_file = self.csv_dir / f"{self.symbol.replace('/', '_')}.csv"

        if not csv_file.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_file}")

        logger.info(f"Loading data from {csv_file}")

        # 读取CSV文件
        df = pd.read_csv(csv_file)

        # 确保有必要的列
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"CSV must contain columns: {required_columns}")

        # 转换时间戳
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # 过滤日期范围
        df = df[(df['timestamp'] >= self.start_date) & (df['timestamp'] <= self.end_date)]

        # 排序
        df = df.sort_values('timestamp').reset_index(drop=True)

        self.data = df
        self.bar_generator = self._generate_bars()

        logger.info(f"Loaded {len(df)} bars for {self.symbol}")

    def _generate_bars(self) -> Generator:
        """生成K线数据的生成器"""
        for _, row in self.data.iterrows():
            yield row.to_dict()

    def get_latest_bar(self) -> Optional[Dict]:
        """获取最新的K线数据"""
        if len(self.latest_bars) > 0:
            return self.latest_bars[-1]
        return None

    def get_latest_bars(self, n: int = 1) -> Optional[List[Dict]]:
        """获取最新的N根K线"""
        if len(self.latest_bars) >= n:
            return self.latest_bars[-n:]
        return None

    def update_bars(self) -> Optional[MarketEvent]:
        """
        更新K线数据，返回市场事件

        Returns:
            MarketEvent对象，如果没有更多数据则返回None
        """
        try:
            bar = next(self.bar_generator)
        except StopIteration:
            return None

        # 添加到最新K线列表，超出上限时裁剪
        self.latest_bars.append(bar)
        if len(self.latest_bars) > self.MAX_LATEST_BARS:
            self.latest_bars = self.latest_bars[-self.MAX_LATEST_BARS:]

        # 创建市场事件
        event = MarketEvent(
            symbol=self.symbol,
            timestamp=bar['timestamp'],
            open_price=bar['open'],
            high_price=bar['high'],
            low_price=bar['low'],
            close_price=bar['close'],
            volume=bar['volume']
        )

        return event

    def continue_backtest(self) -> bool:
        """检查是否还有数据可以回测"""
        return self.current_index < len(self.data)


class DatabaseDataHandler(DataHandler):
    """
    数据库数据处理器

    从数据库加载历史数据
    """

    def __init__(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        db_connection
    ):
        """
        初始化数据库数据处理器

        Args:
            symbol: 交易对符号
            start_date: 开始日期
            end_date: 结束日期
            db_connection: 数据库连接对象
        """
        super().__init__(symbol, start_date, end_date)
        self.db_connection = db_connection
        self.bar_generator = None
        self.latest_bars = []
        self.load_data()

    def load_data(self) -> None:
        """从数据库加载数据"""
        logger.info(f"Loading data from database for {self.symbol}")

        query = """
        SELECT timestamp, open, high, low, close, volume
        FROM klines
        WHERE symbol = %s AND timestamp >= %s AND timestamp <= %s
        ORDER BY timestamp ASC
        """

        df = pd.read_sql(
            query,
            self.db_connection,
            params=(self.symbol, self.start_date, self.end_date)
        )

        df['timestamp'] = pd.to_datetime(df['timestamp'])

        self.data = df
        self.bar_generator = self._generate_bars()

        logger.info(f"Loaded {len(df)} bars for {self.symbol}")

    def _generate_bars(self) -> Generator:
        """生成K线数据的生成器"""
        for _, row in self.data.iterrows():
            yield row.to_dict()

    def get_latest_bar(self) -> Optional[Dict]:
        """获取最新的K线数据"""
        if len(self.latest_bars) > 0:
            return self.latest_bars[-1]
        return None

    def get_latest_bars(self, n: int = 1) -> Optional[List[Dict]]:
        """获取最新的N根K线"""
        if len(self.latest_bars) >= n:
            return self.latest_bars[-n:]
        return None

    def update_bars(self) -> Optional[MarketEvent]:
        """更新K线数据，返回市场事件"""
        try:
            bar = next(self.bar_generator)
        except StopIteration:
            return None

        self.latest_bars.append(bar)
        if len(self.latest_bars) > self.MAX_LATEST_BARS:
            self.latest_bars = self.latest_bars[-self.MAX_LATEST_BARS:]

        event = MarketEvent(
            symbol=self.symbol,
            timestamp=bar['timestamp'],
            open_price=bar['open'],
            high_price=bar['high'],
            low_price=bar['low'],
            close_price=bar['close'],
            volume=bar['volume']
        )

        return event

    def continue_backtest(self) -> bool:
        """检查是否还有数据可以回测"""
        return self.current_index < len(self.data)


class ExchangeDataHandler(DataHandler):
    """
    交易所数据处理器

    通过 ccxt 从交易所获取历史K线数据，用于 API 触发的回测
    """

    def __init__(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        exchange_id: str = 'binance',
        interval: str = '1h',
    ):
        super().__init__(symbol, start_date, end_date)
        self.exchange_id = exchange_id
        self.interval = interval
        self.bar_generator = None
        self.latest_bars = []
        self.load_data()

    def load_data(self) -> None:
        """通过 ccxt 从交易所获取历史K线数据"""
        import ccxt

        logger.info(
            f"从 {self.exchange_id} 获取 {self.symbol} "
            f"({self.interval}) K线数据..."
        )

        exchange_cls = getattr(ccxt, self.exchange_id, None)
        if exchange_cls is None:
            raise ValueError(f"不支持的交易所: {self.exchange_id}")

        exchange = exchange_cls({
            'enableRateLimit': True,
            'timeout': 15000,
        })

        since_ms = int(self.start_date.timestamp() * 1000)
        end_ms = int(self.end_date.timestamp() * 1000)
        all_ohlcv = []
        current_since = since_ms

        while current_since < end_ms:
            ohlcv = exchange.fetch_ohlcv(
                self.symbol,
                timeframe=self.interval,
                since=current_since,
                limit=1000,
            )
            if not ohlcv:
                break
            for bar in ohlcv:
                if bar[0] <= end_ms:
                    all_ohlcv.append(bar)
            last_ts = ohlcv[-1][0]
            if last_ts <= current_since:
                break
            current_since = last_ts + 1

        if not all_ohlcv:
            raise ValueError(
                f"未获取到 {self.symbol} 在指定时间范围内的K线数据"
            )

        df = pd.DataFrame(
            all_ohlcv,
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'],
        )
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df = df.sort_values('timestamp').reset_index(drop=True)
        self.data = df
        self.bar_generator = self._generate_bars()
        logger.info(f"已获取 {len(df)} 根K线: {self.symbol}")

    def _generate_bars(self) -> Generator:
        for _, row in self.data.iterrows():
            yield row.to_dict()

    def get_latest_bar(self) -> Optional[Dict]:
        if self.latest_bars:
            return self.latest_bars[-1]
        return None

    def get_latest_bars(self, n: int = 1) -> Optional[List[Dict]]:
        if len(self.latest_bars) >= n:
            return self.latest_bars[-n:]
        return None

    def update_bars(self) -> Optional[MarketEvent]:
        try:
            bar = next(self.bar_generator)
        except StopIteration:
            return None

        self.latest_bars.append(bar)
        if len(self.latest_bars) > self.MAX_LATEST_BARS:
            self.latest_bars = self.latest_bars[-self.MAX_LATEST_BARS:]

        return MarketEvent(
            symbol=self.symbol,
            timestamp=bar['timestamp'],
            open_price=bar['open'],
            high_price=bar['high'],
            low_price=bar['low'],
            close_price=bar['close'],
            volume=bar['volume'],
        )

    def continue_backtest(self) -> bool:
        return self.current_index < len(self.data)

    def get_dataframe(self) -> pd.DataFrame:
        """获取已迭代过的K线数据作为 DataFrame（供策略分析使用）"""
        if not self.latest_bars:
            return pd.DataFrame()
        return pd.DataFrame(self.latest_bars)
