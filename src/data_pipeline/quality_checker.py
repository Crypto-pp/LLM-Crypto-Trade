"""
数据质量检查模块

提供数据完整性、有效性、异常值检测功能
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
from loguru import logger

from .adapters.base import KlineData


class DataQualityChecker:
    """数据质量检查器"""

    def __init__(self):
        self.validation_rules = {
            'price_range': (Decimal('0.0'), Decimal('1e10')),  # 价格范围
            'volume_range': (Decimal('0.0'), Decimal('1e15')),  # 成交量范围
            'price_change_threshold': Decimal('0.5'),  # 价格变化阈值（50%）
        }

    def check_completeness(
        self,
        klines: List[KlineData],
        interval: str,
        expected_count: Optional[int] = None
    ) -> Tuple[bool, str, float]:
        """检查数据完整性

        Returns:
            (is_complete, message, completeness_rate)
        """
        if not klines:
            return False, "No data", 0.0

        # 计算实际数据点数
        actual_count = len(klines)

        # 如果没有指定期望数量，根据时间范围计算
        if expected_count is None:
            if len(klines) >= 2:
                time_range = (klines[-1].timestamp - klines[0].timestamp).total_seconds()
                interval_seconds = self._parse_interval_seconds(interval)
                expected_count = int(time_range / interval_seconds) + 1
            else:
                expected_count = actual_count

        # 计算完整性
        completeness_rate = (actual_count / expected_count * 100) if expected_count > 0 else 0

        is_complete = completeness_rate >= 99.0

        message = f"Completeness: {completeness_rate:.2f}% ({actual_count}/{expected_count})"

        return is_complete, message, completeness_rate

    def check_validity(
        self,
        kline: KlineData,
        prev_kline: Optional[KlineData] = None
    ) -> Tuple[bool, str]:
        """检查数据有效性

        Returns:
            (is_valid, error_message)
        """
        # 1. 检查必填字段
        if not all([kline.open, kline.high, kline.low, kline.close, kline.volume]):
            return False, "Missing required fields"

        # 2. 检查价格范围
        prices = [kline.open, kline.high, kline.low, kline.close]
        min_price, max_price = self.validation_rules['price_range']

        if not all(min_price <= p <= max_price for p in prices):
            return False, f"Price out of range: {prices}"

        # 3. 检查OHLC逻辑
        if not (kline.low <= kline.open <= kline.high and
                kline.low <= kline.close <= kline.high):
            return False, f"Invalid OHLC: O={kline.open}, H={kline.high}, L={kline.low}, C={kline.close}"

        # 4. 检查成交量
        min_vol, max_vol = self.validation_rules['volume_range']
        if not (min_vol <= kline.volume <= max_vol):
            return False, f"Volume out of range: {kline.volume}"

        # 5. 检查价格突变（闪崩检测）
        if prev_kline:
            price_change = abs(kline.close - prev_kline.close) / prev_kline.close
            if price_change > self.validation_rules['price_change_threshold']:
                return False, f"Abnormal price change: {price_change:.2%}"

        # 6. 检查时间戳
        if kline.timestamp > datetime.now(kline.timestamp.tzinfo) + timedelta(minutes=5):
            return False, f"Future timestamp: {kline.timestamp}"

        return True, ""

    def detect_anomaly(
        self,
        klines: List[KlineData],
        method: str = 'zscore',
        threshold: float = 3.0
    ) -> List[int]:
        """检测异常值

        Args:
            klines: K线列表
            method: 检测方法 ('zscore' 或 'iqr')
            threshold: 阈值

        Returns:
            异常值索引列表
        """
        if len(klines) < 10:
            return []

        if method == 'zscore':
            return self._detect_outliers_zscore(klines, threshold)
        elif method == 'iqr':
            return self._detect_outliers_iqr(klines)
        else:
            logger.warning(f"Unknown anomaly detection method: {method}")
            return []

    def check_timestamp(
        self,
        klines: List[KlineData],
        interval: str
    ) -> Tuple[bool, List[int]]:
        """检查时间戳连续性

        Returns:
            (is_continuous, missing_indices)
        """
        if len(klines) < 2:
            return True, []

        interval_seconds = self._parse_interval_seconds(interval)
        missing_indices = []

        for i in range(1, len(klines)):
            expected_time = klines[i-1].timestamp + timedelta(seconds=interval_seconds)
            actual_time = klines[i].timestamp

            time_diff = abs((actual_time - expected_time).total_seconds())

            # 允许1秒的误差
            if time_diff > 1:
                missing_indices.append(i)

        is_continuous = len(missing_indices) == 0

        return is_continuous, missing_indices

    def generate_quality_report(
        self,
        klines: List[KlineData],
        interval: str,
        symbol: str
    ) -> dict:
        """生成质量报告"""

        report = {
            'symbol': symbol,
            'interval': interval,
            'total_records': len(klines),
            'time_range': None,
            'completeness': None,
            'validity': None,
            'continuity': None,
            'anomalies': None
        }

        if not klines:
            return report

        # 时间范围
        report['time_range'] = {
            'start': klines[0].timestamp.isoformat(),
            'end': klines[-1].timestamp.isoformat()
        }

        # 完整性检查
        is_complete, msg, rate = self.check_completeness(klines, interval)
        report['completeness'] = {
            'is_complete': is_complete,
            'rate': rate,
            'message': msg
        }

        # 有效性检查
        invalid_count = 0
        for i, kline in enumerate(klines):
            prev_kline = klines[i-1] if i > 0 else None
            is_valid, _ = self.check_validity(kline, prev_kline)
            if not is_valid:
                invalid_count += 1

        report['validity'] = {
            'valid_records': len(klines) - invalid_count,
            'invalid_records': invalid_count,
            'validity_rate': (len(klines) - invalid_count) / len(klines) * 100
        }

        # 连续性检查
        is_continuous, missing = self.check_timestamp(klines, interval)
        report['continuity'] = {
            'is_continuous': is_continuous,
            'missing_count': len(missing),
            'missing_indices': missing[:10]  # 只显示前10个
        }

        # 异常值检测
        anomalies = self.detect_anomaly(klines)
        report['anomalies'] = {
            'count': len(anomalies),
            'indices': anomalies[:10]  # 只显示前10个
        }

        return report

    def _detect_outliers_zscore(
        self,
        klines: List[KlineData],
        threshold: float = 3.0
    ) -> List[int]:
        """使用Z-score检测异常值"""

        # 提取收盘价
        closes = [float(k.close) for k in klines]

        # 计算均值和标准差
        mean = sum(closes) / len(closes)
        variance = sum((x - mean) ** 2 for x in closes) / len(closes)
        std = variance ** 0.5

        if std == 0:
            return []

        # 计算Z-score
        outlier_indices = []
        for i, close in enumerate(closes):
            z_score = abs((close - mean) / std)
            if z_score > threshold:
                outlier_indices.append(i)

        return outlier_indices

    def _detect_outliers_iqr(self, klines: List[KlineData]) -> List[int]:
        """使用IQR方法检测异常值"""

        closes = sorted([float(k.close) for k in klines])
        n = len(closes)

        # 计算四分位数
        q1_idx = n // 4
        q3_idx = 3 * n // 4
        q1 = closes[q1_idx]
        q3 = closes[q3_idx]
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outlier_indices = []
        for i, kline in enumerate(klines):
            close = float(kline.close)
            if close < lower_bound or close > upper_bound:
                outlier_indices.append(i)

        return outlier_indices

    def _parse_interval_seconds(self, interval: str) -> int:
        """解析时间间隔为秒数"""
        unit = interval[-1]
        value = int(interval[:-1])

        multipliers = {
            'm': 60,
            'h': 3600,
            'd': 86400,
            'w': 604800
        }

        return value * multipliers.get(unit, 60)
