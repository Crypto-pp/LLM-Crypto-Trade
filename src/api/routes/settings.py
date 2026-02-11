"""
系统设置API路由

提供交易所配置和信号监控配置的查询和更新接口。
"""

from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from src.config.exchange_config_manager import ExchangeConfigManager
from src.config.signal_config_manager import SignalConfigManager
from src.config.notification_config_manager import NotificationConfigManager
from src.services.signal_notification import SignalNotificationService

router = APIRouter(tags=["settings"])

_exchange_config_manager = ExchangeConfigManager()
_signal_config_manager = SignalConfigManager()
_notification_config_manager = NotificationConfigManager()
_notification_service = SignalNotificationService(_notification_config_manager)


@router.get("/exchange")
async def get_exchange_config():
    """获取交易所配置（敏感字段已脱敏）"""
    try:
        return _exchange_config_manager.get_config_response()
    except Exception as e:
        logger.error(f"获取交易所配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/exchange")
async def update_exchange_config(data: dict):
    """更新交易所配置（持久化到JSON文件）"""
    try:
        _exchange_config_manager.save(data)
        return _exchange_config_manager.get_config_response()
    except Exception as e:
        logger.error(f"更新交易所配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 信号监控配置端点 ==========


@router.get("/signal-monitors")
async def get_signal_monitors():
    """获取所有信号监控任务"""
    try:
        tasks = _signal_config_manager.get_tasks()
        return {"tasks": tasks}
    except Exception as e:
        logger.error(f"获取信号监控任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/signal-monitors")
async def add_signal_monitor(data: dict):
    """添加信号监控任务"""
    try:
        task = _signal_config_manager.add_task(data)
        return {"task": task}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"添加信号监控任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/signal-monitors/{task_id}")
async def update_signal_monitor(task_id: str, data: dict):
    """更新信号监控任务"""
    try:
        task = _signal_config_manager.update_task(task_id, data)
        if task is None:
            raise HTTPException(status_code=404, detail="任务不存在")
        return {"task": task}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新信号监控任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/signal-monitors/{task_id}")
async def delete_signal_monitor(task_id: str):
    """删除信号监控任务"""
    try:
        deleted = _signal_config_manager.delete_task(task_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="任务不存在")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除信号监控任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/signal-monitors/{task_id}/run")
async def run_signal_monitor(task_id: str, request: Request):
    """手动触发执行信号监控任务"""
    try:
        scheduler = getattr(request.app.state, "signal_scheduler", None)
        if scheduler is None:
            raise HTTPException(status_code=503, detail="信号调度器未启动")
        signals = await scheduler.run_task_now(task_id)
        return {"signals": signals}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"手动执行信号监控任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 通知渠道配置端点 ==========


@router.get("/notifications")
async def get_notification_config():
    """获取通知配置（敏感字段已脱敏）"""
    try:
        return _notification_config_manager.get_config_response()
    except Exception as e:
        logger.error(f"获取通知配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notifications/settings")
async def update_notification_settings(data: dict):
    """更新通知全局设置（买入/卖出/持有通知开关）"""
    try:
        settings = _notification_config_manager.update_settings(data)
        return {"settings": settings}
    except Exception as e:
        logger.error(f"更新通知设置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/channels")
async def add_notification_channel(data: dict):
    """添加通知渠道"""
    try:
        channel = _notification_config_manager.add_channel(data)
        return {"channel": channel}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"添加通知渠道失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notifications/channels/{channel_id}")
async def update_notification_channel(channel_id: str, data: dict):
    """更新通知渠道"""
    try:
        channel = _notification_config_manager.update_channel(channel_id, data)
        if channel is None:
            raise HTTPException(status_code=404, detail="渠道不存在")
        return {"channel": channel}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新通知渠道失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/notifications/channels/{channel_id}")
async def delete_notification_channel(channel_id: str):
    """删除通知渠道"""
    try:
        deleted = _notification_config_manager.delete_channel(channel_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="渠道不存在")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除通知渠道失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/channels/{channel_id}/test")
async def test_notification_channel(channel_id: str):
    """发送测试消息到指定渠道"""
    try:
        success = await _notification_service.send_test(channel_id)
        if success:
            return {"success": True, "message": "测试消息发送成功"}
        raise HTTPException(status_code=502, detail="测试消息发送失败，请检查配置")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试通知发送失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
