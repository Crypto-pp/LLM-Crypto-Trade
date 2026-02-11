"""
信号调度器

负责定时执行监控任务：获取K线数据→运行策略→保存信号。
使用 asyncio 后台任务实现定时循环。
"""

import asyncio
import json
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from loguru import logger
import pandas as pd
import numpy as np
import ccxt

from src.config.signal_config_manager import SignalConfigManager
from src.config import get_settings
from src.services.signal_store import SignalStore
from src.services.signal_notification import SignalNotificationService
from src.trading_engine.strategies import (
    TrendFollowingStrategy,
    MeanReversionStrategy,
    MomentumStrategy,
)
from src.ai_service.ai_analyzer import AIAnalyzer
from src.ai_service.config_manager import AIConfigManager
from src.utils.math_utils import smart_round


# 周期到秒数的映射（用于判断任务是否到期）
INTERVAL_SECONDS = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
}

# 策略名称到类的映射
STRATEGY_MAP = {
    "趋势跟踪": TrendFollowingStrategy,
    "均值回归": MeanReversionStrategy,
    "动量策略": MomentumStrategy,
}


def _sanitize(obj):
    """递归将 numpy/pandas 类型转为原生 Python 类型"""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(item) for item in obj]
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        val = float(obj)
        return smart_round(val) if not np.isnan(val) else 0.0
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    return obj


def _fetch_ohlcv_df(symbol: str, interval: str, limit: int = 200) -> pd.DataFrame:
    """从 Binance 获取K线数据并转为 DataFrame"""
    exchange = ccxt.binance({"enableRateLimit": True, "timeout": 15000})
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=interval, limit=limit)
    if not ohlcv:
        raise ValueError(f"未获取到 {symbol} 的K线数据")
    df = pd.DataFrame(
        ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    return df


class SignalScheduler:
    """
    信号调度器

    在 FastAPI 启动时创建 asyncio 后台任务，
    每60秒检查一次所有启用的监控任务，到期则执行。
    """

    def __init__(self):
        self._config_manager = SignalConfigManager()
        self._signal_store = SignalStore()
        self._notification_service = SignalNotificationService()
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """启动调度循环"""
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("信号调度器已启动")

    async def stop(self):
        """停止调度"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("信号调度器已停止")

    async def _run_loop(self):
        """主循环：每60秒检查一次，执行到期的任务"""
        while self._running:
            try:
                await self._execute_due_tasks()
            except Exception as e:
                logger.error(f"调度循环异常: {e}")
            await asyncio.sleep(60)

    async def _execute_due_tasks(self):
        """执行所有到期的启用任务"""
        tasks = self._config_manager.get_tasks()
        for task in tasks:
            if not task.get("enabled"):
                continue
            if self._is_due(task):
                try:
                    await self._run_single_task(task)
                except Exception as e:
                    logger.error(
                        f"执行监控任务失败 [{task.get('symbol')}]: {e}"
                    )

    def _is_due(self, task: Dict[str, Any]) -> bool:
        """判断任务是否到执行时间"""
        last_run = task.get("last_run")
        if not last_run:
            return True

        try:
            last_run_dt = datetime.fromisoformat(last_run)
            interval = task.get("interval", "1h")
            interval_secs = INTERVAL_SECONDS.get(interval, 3600)
            next_run = last_run_dt + timedelta(seconds=interval_secs)
            return datetime.now(timezone.utc) >= next_run
        except (ValueError, TypeError):
            return True

    async def _run_single_task(self, task: Dict[str, Any]):
        """
        执行单个监控任务

        流程：获取K线数据 → 运行策略分析 → 保存信号
        AI策略走独立分支，调用 AIAnalyzer 并解析结构化输出。
        """
        symbol = task["symbol"]
        strategy_name = task["strategy"]
        interval = task["interval"]
        task_id = task["id"]

        logger.info(f"执行监控任务: {symbol} {strategy_name} {interval}")

        # 在线程池中执行阻塞的 ccxt 调用
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(
            None, _fetch_ohlcv_df, symbol, interval
        )

        now = datetime.now(timezone.utc)
        current_price = float(df["close"].iloc[-1])

        # AI策略走独立分支
        if strategy_name == "AI分析":
            store_signals = await self._run_ai_analysis(
                symbol, interval, df, task_id, now, current_price
            )
        else:
            store_signals = self._run_traditional_strategy(
                symbol, strategy_name, interval, df, task_id, now, current_price
            )

        self._signal_store.add_signals(store_signals)

        # 发送通知（异步，不阻塞主流程）
        try:
            result = await self._notification_service.notify_signals(store_signals)
            if result["sent"] > 0:
                logger.info(f"信号通知已发送: {result}")
        except Exception as e:
            logger.warning(f"信号通知发送失败（不影响主流程）: {e}")

        # 更新任务的 last_run 和 last_signal
        last_signal_type = store_signals[0]["signal_type"] if store_signals else "HOLD"
        self._config_manager.update_task(task_id, {
            "last_run": now.isoformat(),
            "last_signal": last_signal_type,
        })

        logger.info(
            f"监控任务完成: {symbol} → {last_signal_type} "
            f"(共 {len(store_signals)} 条信号)"
        )

    async def run_task_now(self, task_id: str) -> List[Dict[str, Any]]:
        """
        手动触发执行指定任务

        Returns:
            生成的信号列表
        """
        task = self._config_manager.get_task(task_id)
        if not task:
            raise ValueError(f"任务不存在: {task_id}")

        await self._run_single_task(task)

        # 返回该任务最新生成的信号
        latest = self._signal_store.get_signals(
            symbol=task["symbol"],
            strategy=task["strategy"],
            limit=5,
        )
        return [s for s in latest if s.get("task_id") == task_id]

    def _run_traditional_strategy(
        self, symbol: str, strategy_name: str, interval: str,
        df: pd.DataFrame, task_id: str, now: datetime, current_price: float,
    ) -> List[Dict[str, Any]]:
        """执行传统策略（趋势跟踪/均值回归/动量）"""
        strategy_cls = STRATEGY_MAP.get(strategy_name)
        if not strategy_cls:
            logger.error(f"未知策略: {strategy_name}")
            return [self._hold_signal(symbol, strategy_name, interval, task_id, now, current_price)]

        strategy = strategy_cls()
        analysis = strategy.analyze(df)
        raw_signals = strategy.generate_signals(df, analysis)
        raw_signals = _sanitize(raw_signals)

        store_signals = []
        for sig in raw_signals:
            signal_type = sig.get("type", "HOLD").upper()
            confidence = sig.get("confidence", 0.5)
            store_signals.append({
                "symbol": symbol,
                "signal_type": signal_type,
                "entry_price": smart_round(current_price),
                "stop_loss": smart_round(sig.get("stop_loss", current_price * 0.96)),
                "take_profit": smart_round(sig.get("take_profit", current_price * 1.1)),
                "strategy": strategy_name,
                "interval": interval,
                "confidence": smart_round(confidence) if isinstance(confidence, float) else confidence,
                "timestamp": now.isoformat(),
                "task_id": task_id,
            })

        if not store_signals:
            store_signals.append(self._hold_signal(symbol, strategy_name, interval, task_id, now, current_price))

        return store_signals

    async def _run_ai_analysis(
        self, symbol: str, interval: str, df: pd.DataFrame,
        task_id: str, now: datetime, current_price: float,
    ) -> List[Dict[str, Any]]:
        """
        执行AI策略分析

        调用 AIAnalyzer 使用 signal_generation 提示词，
        从AI响应中解析JSON格式的交易信号。
        """
        try:
            settings = get_settings()
            config_manager = AIConfigManager()
            effective = config_manager.get_effective_settings(settings.ai)
            analyzer = AIAnalyzer(effective)

            result = await analyzer.analyze(
                symbol=symbol,
                interval=interval,
                prompt_id="signal_generation",
                df=df,
            )

            analysis_text = result.get("analysis", "")
            parsed = self._parse_ai_signal(analysis_text)

            signal_type = parsed.get("signal_type", "HOLD").upper()
            if signal_type not in ("BUY", "SELL", "HOLD"):
                signal_type = "HOLD"

            confidence = parsed.get("confidence", 0.5)
            if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
                confidence = 0.5

            entry = parsed.get("entry_price", current_price)
            stop_loss = parsed.get("stop_loss")
            take_profit = parsed.get("take_profit")

            return [{
                "symbol": symbol,
                "signal_type": signal_type,
                "entry_price": smart_round(float(entry)),
                "stop_loss": smart_round(float(stop_loss)) if stop_loss else None,
                "take_profit": smart_round(float(take_profit)) if take_profit else None,
                "strategy": "AI分析",
                "interval": interval,
                "confidence": smart_round(float(confidence)),
                "timestamp": now.isoformat(),
                "task_id": task_id,
            }]

        except Exception as e:
            logger.error(f"AI分析失败 [{symbol}]: {e}")
            return [self._hold_signal(
                symbol, "AI分析", interval, task_id, now, current_price
            )]

    @staticmethod
    def _parse_ai_signal(text: str) -> Dict[str, Any]:
        """
        从AI响应文本中解析JSON格式的交易信号

        查找 ```json ... ``` 代码块并解析。
        """
        # 匹配 ```json ... ``` 代码块
        pattern = r"```json\s*(\{.*?\})\s*```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                logger.warning("AI响应中的JSON解析失败")

        # 回退：尝试匹配任意 { ... } JSON块
        pattern2 = r"\{[^{}]*\"signal_type\"[^{}]*\}"
        match2 = re.search(pattern2, text, re.DOTALL)
        if match2:
            try:
                return json.loads(match2.group(0))
            except json.JSONDecodeError:
                pass

        logger.warning("未能从AI响应中解析出信号JSON")
        return {"signal_type": "HOLD", "confidence": 0.5}

    @staticmethod
    def _hold_signal(
        symbol: str, strategy: str, interval: str,
        task_id: str, now: datetime, current_price: float,
    ) -> Dict[str, Any]:
        """生成默认的 HOLD 信号"""
        return {
            "symbol": symbol,
            "signal_type": "HOLD",
            "entry_price": smart_round(current_price),
            "stop_loss": None,
            "take_profit": None,
            "strategy": strategy,
            "interval": interval,
            "confidence": 0.5,
            "timestamp": now.isoformat(),
            "task_id": task_id,
        }
