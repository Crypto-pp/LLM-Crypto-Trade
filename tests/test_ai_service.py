"""
AI服务模块测试

测试上下文构建器、提示词管理器、适配器工厂等核心组件。
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import AsyncMock, patch, MagicMock


def _make_ohlcv_df(rows: int = 50) -> pd.DataFrame:
    """生成模拟K线数据"""
    np.random.seed(42)
    base_price = 50000.0
    data = []
    for i in range(rows):
        o = base_price + np.random.randn() * 500
        h = o + abs(np.random.randn() * 300)
        l = o - abs(np.random.randn() * 300)
        c = l + np.random.random() * (h - l)
        v = np.random.random() * 1000 + 100
        data.append({
            "timestamp": pd.Timestamp("2025-01-01") + pd.Timedelta(hours=i),
            "open": o,
            "high": h,
            "low": l,
            "close": c,
            "volume": v,
        })
        base_price = c
    return pd.DataFrame(data)


# ============================================================
# 适配器工厂测试
# ============================================================

class TestAdapterFactory:
    """适配器工厂测试"""

    def _make_settings(self, **overrides):
        """构造模拟AISettings"""
        defaults = {
            "default_provider": "deepseek",
            "deepseek_api_key": "",
            "deepseek_base_url": "https://api.deepseek.com",
            "deepseek_model": "deepseek-chat",
            "gemini_api_key": "",
            "gemini_model": "gemini-2.0-flash",
            "openai_api_key": "",
            "openai_base_url": "https://api.openai.com/v1",
            "openai_model": "gpt-4o",
            "max_tokens": 4096,
            "temperature": 0.3,
            "timeout": 60,
        }
        defaults.update(overrides)
        return MagicMock(**defaults)

    def test_get_adapter_deepseek(self):
        """测试创建DeepSeek适配器"""
        from src.ai_service.adapters.adapter_factory import get_adapter
        from src.ai_service.adapters.deepseek import DeepSeekAdapter

        settings = self._make_settings(deepseek_api_key="test-key-123")
        adapter = get_adapter("deepseek", settings)
        assert isinstance(adapter, DeepSeekAdapter)
        assert adapter.get_provider_name() == "deepseek"
        assert adapter.get_model_name() == "deepseek-chat"

    def test_get_adapter_gemini(self):
        """测试创建Gemini适配器"""
        from src.ai_service.adapters.adapter_factory import get_adapter

        try:
            import google.generativeai
        except ImportError:
            pytest.skip("google-generativeai 未安装，跳过Gemini适配器测试")

        from src.ai_service.adapters.gemini import GeminiAdapter
        settings = self._make_settings(gemini_api_key="test-gemini-key")
        adapter = get_adapter("gemini", settings)
        assert isinstance(adapter, GeminiAdapter)
        assert adapter.get_provider_name() == "gemini"
        assert adapter.get_model_name() == "gemini-2.0-flash"

    def test_get_adapter_openai(self):
        """测试创建OpenAI兼容适配器"""
        from src.ai_service.adapters.adapter_factory import get_adapter
        from src.ai_service.adapters.openai_compatible import OpenAICompatibleAdapter

        settings = self._make_settings(openai_api_key="test-openai-key")
        adapter = get_adapter("openai", settings)
        assert isinstance(adapter, OpenAICompatibleAdapter)
        assert adapter.get_provider_name() == "openai"
        assert adapter.get_model_name() == "gpt-4o"

    def test_get_adapter_missing_key(self):
        """测试缺少API Key时抛出异常"""
        from src.ai_service.adapters.adapter_factory import get_adapter

        settings = self._make_settings()  # 所有key为空
        with pytest.raises(ValueError, match="未配置"):
            get_adapter("deepseek", settings)

    def test_get_adapter_unknown_provider(self):
        """测试不支持的提供商"""
        from src.ai_service.adapters.adapter_factory import get_adapter

        settings = self._make_settings()
        with pytest.raises(ValueError, match="不支持的AI提供商"):
            get_adapter("unknown_provider", settings)

    def test_get_available_providers_none(self):
        """测试无可用提供商"""
        from src.ai_service.adapters.adapter_factory import get_available_providers

        settings = self._make_settings()
        providers = get_available_providers(settings)
        assert providers == []

    def test_get_available_providers_all(self):
        """测试所有提供商都可用"""
        from src.ai_service.adapters.adapter_factory import get_available_providers

        settings = self._make_settings(
            deepseek_api_key="dk-key",
            gemini_api_key="gm-key",
            openai_api_key="sk-key",
        )
        providers = get_available_providers(settings)
        assert len(providers) == 3
        ids = [p["id"] for p in providers]
        assert "deepseek" in ids
        assert "gemini" in ids
        assert "openai" in ids
        for p in providers:
            assert p["enabled"] is True

    def test_get_available_providers_partial(self):
        """测试部分提供商可用"""
        from src.ai_service.adapters.adapter_factory import get_available_providers

        settings = self._make_settings(gemini_api_key="gm-key")
        providers = get_available_providers(settings)
        assert len(providers) == 1
        assert providers[0]["id"] == "gemini"


# ============================================================
# 提示词管理器测试
# ============================================================

class TestPromptManager:
    """提示词管理器测试"""

    def _get_manager(self):
        from src.ai_service.prompts.prompt_manager import PromptManager
        return PromptManager()

    def test_list_prompts(self):
        """测试获取所有提示词列表"""
        pm = self._get_manager()
        prompts = pm.list_prompts()
        assert len(prompts) == 6
        ids = [p["id"] for p in prompts]
        assert "comprehensive" in ids
        assert "entry_timing" in ids
        assert "risk_assessment" in ids
        assert "trend_analysis" in ids
        assert "support_resistance" in ids
        assert "strategy_advice" in ids

    def test_list_prompts_fields(self):
        """测试提示词列表字段完整性"""
        pm = self._get_manager()
        for p in pm.list_prompts():
            assert "id" in p
            assert "name" in p
            assert "description" in p
            assert "category" in p
            assert isinstance(p["name"], str) and len(p["name"]) > 0

    def test_get_prompt_exists(self):
        """测试获取已有提示词"""
        pm = self._get_manager()
        prompt = pm.get_prompt("comprehensive")
        assert prompt is not None
        assert prompt["id"] == "comprehensive"
        assert "template" in prompt

    def test_get_prompt_not_exists(self):
        """测试获取不存在的提示词"""
        pm = self._get_manager()
        assert pm.get_prompt("nonexistent") is None

    def test_build_messages_comprehensive(self):
        """测试构建综合分析消息"""
        pm = self._get_manager()
        msgs = pm.build_messages(
            prompt_id="comprehensive",
            symbol="BTC/USDT",
            interval="1h",
            market_context="测试市场数据",
        )
        assert len(msgs) == 2
        assert msgs[0]["role"] == "system"
        assert "价格行为" in msgs[0]["content"]
        assert msgs[1]["role"] == "user"
        assert "BTC/USDT" in msgs[1]["content"]
        assert "1h" in msgs[1]["content"]
        assert "测试市场数据" in msgs[1]["content"]

    def test_build_messages_all_templates(self):
        """测试所有模板都能正常渲染"""
        pm = self._get_manager()
        template_ids = [
            "comprehensive", "entry_timing", "risk_assessment",
            "trend_analysis", "support_resistance", "strategy_advice",
        ]
        for tid in template_ids:
            msgs = pm.build_messages(
                prompt_id=tid,
                symbol="ETH/USDT",
                interval="4h",
                market_context="模拟上下文",
            )
            assert len(msgs) == 2, f"模板 {tid} 消息数量错误"
            assert "ETH/USDT" in msgs[1]["content"], f"模板 {tid} 未包含交易对"

    def test_build_messages_unknown_prompt(self):
        """测试未知提示词ID抛出异常"""
        pm = self._get_manager()
        with pytest.raises(ValueError, match="未知的提示词ID"):
            pm.build_messages("bad_id", "BTC/USDT", "1h", "ctx")


# ============================================================
# 上下文构建器测试
# ============================================================

class TestContextBuilder:
    """上下文构建器测试"""

    def _get_builder(self):
        from src.ai_service.context_builder import ContextBuilder
        return ContextBuilder()

    def test_build_market_context_returns_string(self):
        """测试构建市场上下文返回字符串"""
        builder = self._get_builder()
        df = _make_ohlcv_df(50)
        result = builder.build_market_context("BTC/USDT", "1h", df)
        assert isinstance(result, str)
        assert len(result) > 100

    def test_context_contains_price_section(self):
        """测试上下文包含价格概览"""
        builder = self._get_builder()
        df = _make_ohlcv_df(50)
        result = builder.build_market_context("BTC/USDT", "4h", df)
        assert "价格概览" in result
        assert "BTC/USDT" in result
        assert "4h" in result

    def test_context_contains_indicators(self):
        """测试上下文包含技术指标"""
        builder = self._get_builder()
        df = _make_ohlcv_df(50)
        result = builder.build_market_context("ETH/USDT", "1h", df)
        assert "技术指标" in result
        assert "RSI" in result

    def test_context_contains_structure(self):
        """测试上下文包含市场结构"""
        builder = self._get_builder()
        df = _make_ohlcv_df(50)
        result = builder.build_market_context("BTC/USDT", "1h", df)
        assert "市场结构" in result

    def test_context_contains_patterns(self):
        """测试上下文包含K线形态"""
        builder = self._get_builder()
        df = _make_ohlcv_df(50)
        result = builder.build_market_context("BTC/USDT", "1h", df)
        assert "K线形态" in result

    def test_context_contains_power(self):
        """测试上下文包含多空力量"""
        builder = self._get_builder()
        df = _make_ohlcv_df(50)
        result = builder.build_market_context("BTC/USDT", "1h", df)
        assert "多空力量" in result

    def test_context_with_minimal_data(self):
        """测试最少数据量（不崩溃）"""
        builder = self._get_builder()
        df = _make_ohlcv_df(5)
        result = builder.build_market_context("BTC/USDT", "1h", df)
        assert isinstance(result, str)
        assert "价格概览" in result


# ============================================================
# _safe_float 工具函数测试
# ============================================================

class TestSafeFloat:
    """_safe_float 工具函数测试"""

    def _safe_float(self, val, decimals=4):
        from src.ai_service.context_builder import _safe_float
        return _safe_float(val, decimals)

    def test_normal_float(self):
        assert self._safe_float(3.14159, 2) == 3.14

    def test_int_value(self):
        assert self._safe_float(42) == 42.0

    def test_numpy_float(self):
        assert self._safe_float(np.float64(1.2345), 3) == 1.234

    def test_none_value(self):
        assert self._safe_float(None) is None

    def test_nan_value(self):
        assert self._safe_float(float("nan")) is None

    def test_inf_value(self):
        assert self._safe_float(float("inf")) is None

    def test_string_value(self):
        assert self._safe_float("not_a_number") is None


# ============================================================
# AI分析器测试（mock外部调用）
# ============================================================

class TestAIAnalyzer:
    """AI分析器测试"""

    def _make_settings(self, **overrides):
        defaults = {
            "default_provider": "deepseek",
            "deepseek_api_key": "test-key",
            "deepseek_base_url": "https://api.deepseek.com",
            "deepseek_model": "deepseek-chat",
            "gemini_api_key": "",
            "gemini_model": "gemini-2.0-flash",
            "openai_api_key": "",
            "openai_base_url": "https://api.openai.com/v1",
            "openai_model": "gpt-4o",
            "max_tokens": 4096,
            "temperature": 0.3,
            "timeout": 60,
        }
        defaults.update(overrides)
        return MagicMock(**defaults)

    def test_get_providers(self):
        """测试获取提供商列表"""
        from src.ai_service.ai_analyzer import AIAnalyzer

        settings = self._make_settings(
            deepseek_api_key="dk", gemini_api_key="gm"
        )
        analyzer = AIAnalyzer(settings)
        providers = analyzer.get_providers()
        assert len(providers) == 2

    def test_get_prompts(self):
        """测试获取提示词列表"""
        from src.ai_service.ai_analyzer import AIAnalyzer

        settings = self._make_settings()
        analyzer = AIAnalyzer(settings)
        prompts = analyzer.get_prompts()
        assert len(prompts) == 6

    @pytest.mark.asyncio
    async def test_analyze_mock(self):
        """测试AI分析流程（mock适配器调用）"""
        from src.ai_service.ai_analyzer import AIAnalyzer

        settings = self._make_settings(deepseek_api_key="test-key")
        analyzer = AIAnalyzer(settings)
        df = _make_ohlcv_df(50)

        mock_adapter = MagicMock()
        mock_adapter.chat = AsyncMock(return_value="这是AI分析结果")
        mock_adapter.get_model_name = MagicMock(return_value="deepseek-chat")
        mock_adapter.get_provider_name = MagicMock(return_value="deepseek")

        with patch(
            "src.ai_service.ai_analyzer.get_adapter",
            return_value=mock_adapter,
        ):
            result = await analyzer.analyze(
                symbol="BTC/USDT",
                interval="1h",
                prompt_id="comprehensive",
                df=df,
            )

        assert result["symbol"] == "BTC/USDT"
        assert result["interval"] == "1h"
        assert result["provider"] == "deepseek"
        assert result["model"] == "deepseek-chat"
        assert result["analysis"] == "这是AI分析结果"
        assert "timestamp" in result
        assert "market_context_summary" in result
        mock_adapter.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_custom_provider(self):
        """测试指定非默认提供商"""
        from src.ai_service.ai_analyzer import AIAnalyzer

        settings = self._make_settings(
            deepseek_api_key="dk",
            gemini_api_key="gm",
        )
        analyzer = AIAnalyzer(settings)
        df = _make_ohlcv_df(50)

        mock_adapter = MagicMock()
        mock_adapter.chat = AsyncMock(return_value="Gemini结果")
        mock_adapter.get_model_name = MagicMock(return_value="gemini-2.0-flash")
        mock_adapter.get_provider_name = MagicMock(return_value="gemini")

        with patch(
            "src.ai_service.ai_analyzer.get_adapter",
            return_value=mock_adapter,
        ) as mock_factory:
            result = await analyzer.analyze(
                symbol="ETH/USDT",
                interval="4h",
                prompt_id="risk_assessment",
                df=df,
                provider="gemini",
            )

        mock_factory.assert_called_once_with("gemini", settings)
        assert result["provider"] == "gemini"
        assert result["analysis"] == "Gemini结果"


# ============================================================
# AI配置管理器测试
# ============================================================

class TestAIConfigManager:
    """AI配置管理器测试"""

    def _make_settings(self, **overrides):
        defaults = {
            "default_provider": "deepseek",
            "deepseek_api_key": "sk-env-deepseek-key",
            "deepseek_base_url": "https://api.deepseek.com",
            "deepseek_model": "deepseek-chat",
            "gemini_api_key": "",
            "gemini_model": "gemini-2.0-flash",
            "openai_api_key": "",
            "openai_base_url": "https://api.openai.com/v1",
            "openai_model": "gpt-4o",
            "max_tokens": 4096,
            "temperature": 0.3,
            "timeout": 60,
        }
        defaults.update(overrides)
        return MagicMock(**defaults)

    def test_mask_key_normal(self):
        """测试正常API Key脱敏"""
        from src.ai_service.config_manager import mask_key
        assert mask_key("sk-abcdefghijklmnop") == "sk-a****mnop"

    def test_mask_key_short(self):
        """测试短Key返回空字符串"""
        from src.ai_service.config_manager import mask_key
        assert mask_key("short") == ""
        assert mask_key("") == ""

    def test_mask_key_none(self):
        """测试None值返回空字符串"""
        from src.ai_service.config_manager import mask_key
        assert mask_key(None) == ""

    def test_load_no_json_file(self, tmp_path):
        """测试无JSON文件时使用环境变量默认值"""
        from src.ai_service.config_manager import AIConfigManager
        mgr = AIConfigManager(config_path=str(tmp_path / "nonexistent.json"))
        settings = self._make_settings()
        result = mgr.load(settings)
        assert result["default_provider"] == "deepseek"
        assert result["deepseek_api_key"] == "sk-env-deepseek-key"
        assert result["max_tokens"] == 4096

    def test_save_and_load(self, tmp_path):
        """测试保存后再加载，JSON覆盖环境变量"""
        from src.ai_service.config_manager import AIConfigManager
        cfg_path = str(tmp_path / "ai_config.json")
        mgr = AIConfigManager(config_path=cfg_path)
        settings = self._make_settings()

        # 保存新配置
        mgr.save({"deepseek_api_key": "sk-new-key-12345678", "temperature": 0.7})

        # 加载合并后的配置
        result = mgr.load(settings)
        assert result["deepseek_api_key"] == "sk-new-key-12345678"
        assert result["temperature"] == 0.7
        # 未修改的字段保持环境变量默认值
        assert result["deepseek_model"] == "deepseek-chat"

    def test_save_skips_masked_key(self, tmp_path):
        """测试保存时跳过脱敏的API Key"""
        from src.ai_service.config_manager import AIConfigManager
        cfg_path = str(tmp_path / "ai_config.json")
        mgr = AIConfigManager(config_path=cfg_path)

        # 先保存一个真实key
        mgr.save({"deepseek_api_key": "sk-real-key-abcd1234"})
        # 再用脱敏值保存，应该跳过
        mgr.save({"deepseek_api_key": "sk-r****1234"})

        settings = self._make_settings()
        result = mgr.load(settings)
        assert result["deepseek_api_key"] == "sk-real-key-abcd1234"

    def test_save_ignores_unknown_fields(self, tmp_path):
        """测试保存时忽略未知字段"""
        from src.ai_service.config_manager import AIConfigManager
        cfg_path = str(tmp_path / "ai_config.json")
        mgr = AIConfigManager(config_path=cfg_path)

        mgr.save({"unknown_field": "value", "deepseek_model": "deepseek-v3"})

        import json
        with open(cfg_path, "r") as f:
            saved = json.load(f)
        assert "unknown_field" not in saved
        assert saved["deepseek_model"] == "deepseek-v3"

    def test_get_config_response_structure(self, tmp_path):
        """测试配置响应结构完整性"""
        from src.ai_service.config_manager import AIConfigManager
        cfg_path = str(tmp_path / "ai_config.json")
        mgr = AIConfigManager(config_path=cfg_path)
        settings = self._make_settings()

        resp = mgr.get_config_response(settings)

        assert "default_provider" in resp
        assert "providers" in resp
        assert "general" in resp
        assert resp["default_provider"] == "deepseek"

        # 验证提供商结构
        for pid in ["deepseek", "gemini", "openai"]:
            assert pid in resp["providers"]
            p = resp["providers"][pid]
            assert "api_key" in p
            assert "model" in p
            assert "has_key" in p

        # deepseek有key，应该脱敏且has_key=True
        ds = resp["providers"]["deepseek"]
        assert ds["has_key"] is True
        assert "****" in ds["api_key"]

        # gemini无key
        gm = resp["providers"]["gemini"]
        assert gm["has_key"] is False
        assert gm["api_key"] == ""

        # 通用参数
        assert resp["general"]["max_tokens"] == 4096
        assert resp["general"]["temperature"] == 0.3
        assert resp["general"]["timeout"] == 60

    def test_get_effective_settings(self, tmp_path):
        """测试获取合并后的有效配置对象"""
        from src.ai_service.config_manager import AIConfigManager
        cfg_path = str(tmp_path / "ai_config.json")
        mgr = AIConfigManager(config_path=cfg_path)
        settings = self._make_settings()

        # 先保存覆盖值
        mgr.save({"temperature": 0.8})

        effective = mgr.get_effective_settings(settings)
        assert effective.temperature == 0.8
        assert effective.deepseek_api_key == "sk-env-deepseek-key"
        assert effective.default_provider == "deepseek"