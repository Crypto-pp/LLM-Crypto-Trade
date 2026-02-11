"""
指标管理器
统一的指标计算接口，支持批量计算和缓存
"""

import pandas as pd
from typing import Dict, List, Optional, Any
import logging
from functools import lru_cache
import hashlib
import json

from .basic import calculate_ma, calculate_ema, calculate_sma, calculate_wma, calculate_vwap
from .trend import calculate_macd, calculate_adx, calculate_parabolic_sar, calculate_ichimoku
from .oscillators import calculate_rsi, calculate_stochastic, calculate_cci, calculate_williams_r
from .volatility import calculate_bollinger_bands, calculate_atr, calculate_standard_deviation, calculate_keltner_channels
from .volume import calculate_obv, calculate_volume_ratio, calculate_mfi, calculate_volume_vwap

logger = logging.getLogger(__name__)


class IndicatorManager:
    """
    指标管理器
    提供统一的指标计算接口，支持批量计算和缓存
    """

    def __init__(self, enable_cache: bool = True):
        """
        初始化指标管理器

        Args:
            enable_cache: 是否启用缓存
        """
        self.enable_cache = enable_cache
        self._cache = {}

        # 注册所有可用的指标
        self.indicators = {
            # 基础指标
            'ma': calculate_ma,
            'ema': calculate_ema,
            'sma': calculate_sma,
            'wma': calculate_wma,
            'vwap': calculate_vwap,

            # 趋势指标
            'macd': calculate_macd,
            'adx': calculate_adx,
            'parabolic_sar': calculate_parabolic_sar,
            'ichimoku': calculate_ichimoku,

            # 震荡指标
            'rsi': calculate_rsi,
            'stochastic': calculate_stochastic,
            'cci': calculate_cci,
            'williams_r': calculate_williams_r,

            # 波动率指标
            'bollinger_bands': calculate_bollinger_bands,
            'atr': calculate_atr,
            'std': calculate_standard_deviation,
            'keltner': calculate_keltner_channels,

            # 成交量指标
            'obv': calculate_obv,
            'volume_ratio': calculate_volume_ratio,
            'mfi': calculate_mfi,
        }

    def calculate(
        self,
        data: pd.DataFrame,
        indicator_name: str,
        **params
    ) -> Any:
        """
        计算单个指标

        Args:
            data: 价格数据
            indicator_name: 指标名称
            **params: 指标参数

        Returns:
            指标计算结果
        """
        if indicator_name not in self.indicators:
            raise ValueError(f"未知的指标: {indicator_name}")

        # 检查缓存
        if self.enable_cache:
            cache_key = self._generate_cache_key(data, indicator_name, params)
            if cache_key in self._cache:
                logger.debug(f"从缓存获取指标: {indicator_name}")
                return self._cache[cache_key]

        # 计算指标
        try:
            indicator_func = self.indicators[indicator_name]
            result = indicator_func(data, **params)

            # 存入缓存
            if self.enable_cache:
                self._cache[cache_key] = result

            return result
        except Exception as e:
            logger.error(f"计算指标 {indicator_name} 失败: {e}")
            raise

    def calculate_multiple(
        self,
        data: pd.DataFrame,
        indicators: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """
        批量计算多个指标

        Args:
            data: 价格数据
            indicators: 指标配置字典，格式: {指标名: {参数}}

        Returns:
            指标结果字典
        """
        results = {}

        for indicator_name, params in indicators.items():
            try:
                results[indicator_name] = self.calculate(data, indicator_name, **params)
            except Exception as e:
                logger.error(f"计算指标 {indicator_name} 失败: {e}")
                results[indicator_name] = None

        return results

    def get_available_indicators(self) -> List[str]:
        """获取所有可用的指标列表"""
        return list(self.indicators.keys())

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        logger.info("指标缓存已清空")

    def _generate_cache_key(
        self,
        data: pd.DataFrame,
        indicator_name: str,
        params: Dict
    ) -> str:
        """生成缓存键"""
        # 使用数据的哈希值和参数生成唯一键
        data_hash = hashlib.md5(
            pd.util.hash_pandas_object(data).values
        ).hexdigest()[:16]

        params_str = json.dumps(params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]

        return f"{indicator_name}_{data_hash}_{params_hash}"
