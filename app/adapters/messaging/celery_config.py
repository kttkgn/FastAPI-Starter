#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Celery 极简配置（无 IDE 提示 + 适配极简 Pydantic）"""
import asyncio
import atexit
from celery import Celery

from app.adapters.cache.cache import async_redis_cache
from app.core.config import settings  # 导入极简 Pydantic 配置

from app.utils.logger import log_info, log_error

# ------------------------------
# 核心变量（极简，修复 IDE 提示）
# ------------------------------
_celery_app = None  # 全局 Celery 实例（简化类型，避免 Optional 提示）
_celery_initialized = False


# ------------------------------
# 核心初始化（适配极简配置 + 无冗余）
# ------------------------------
def init_celery() -> Celery | None:
    """初始化 Celery 实例（单例 + 无 IDE 提示）"""
    global _celery_app, _celery_initialized
    if _celery_initialized and _celery_app:
        log_info("Celery 复用现有实例")
        return _celery_app

    try:
        # 1. 基础校验（适配极简配置的 Redis URL）
        if not settings.REDIS_URL:
            raise ValueError("Redis URL 未配置，无法初始化 Celery")

        # 2. 构建 Celery 连接串（适配极简配置）
        broker_url = f"{settings.REDIS_URL}/1"
        result_backend = f"{settings.REDIS_URL}/2"

        # 3. 创建 Celery 实例（核心参数仅保留必要项）
        celery_instance = Celery(
            "app",
            broker=broker_url,
            backend=result_backend,
            include=["app.jobs.tasks"],  # 任务模块路径
        )

        # 4. 极简配置（只保留核心，砍掉冗余）
        celery_instance.conf.update({
            "task_time_limit": 300,  # 极简默认值（也可从 settings 取）
            "task_soft_time_limit": 240,
            "worker_max_tasks_per_child": 100,
            "broker_transport_options": {"visibility_timeout": 3600},
            "timezone": "Asia/Shanghai",  # 固定时区（极简）
            "enable_utc": True,
            "broker_connection_retry_on_startup": True,
        })

        # 5. 初始化标记
        _celery_app = celery_instance
        _celery_initialized = True
        atexit.register(shutdown_celery)

        log_info(
            f"Celery 初始化成功 | broker: {broker_url} | backend: {result_backend}")
        return celery_instance

    except Exception as e:
        log_error("Celery 初始化失败", error_msg=str(e), exc_info=True)
        raise


# ------------------------------
# 优雅关闭（极简逻辑，无属性报错）
# ------------------------------
def shutdown_celery() -> None:
    """关闭 Celery 连接（极简安全处理）"""
    global _celery_app, _celery_initialized
    if not _celery_initialized or not _celery_app:
        return

    try:
        # 1. 关闭 Celery 连接池（极简判断，避免 IDE 提示）
        if hasattr(_celery_app, 'connection_pool') and _celery_app.connection_pool:
            _celery_app.connection_pool.disconnect()

        # 2. 关闭 Redis 连接（适配重构后的 Redis 客户端）
        loop = asyncio.get_event_loop() if asyncio.get_event_loop().is_running() else asyncio.new_event_loop()
        loop.run_until_complete(async_redis_cache.redis_client.close())

        # 3. 重置状态
        _celery_app = None
        _celery_initialized = False
        log_info("Celery 已优雅关闭")

    except Exception as e:
        log_error("Celery 关闭失败", error_msg=str(e), exc_info=True)


# ------------------------------
# 便捷获取实例（对外暴露，无提示）
# ------------------------------
def get_celery_app() -> Celery:
    """获取 Celery 实例（确保非 None）"""
    global _celery_app
    if not _celery_app:
        _celery_app = init_celery()
    return _celery_app


# ------------------------------
# 对外暴露实例（兼容任务装饰器）
# ------------------------------
celery_app = get_celery_app()
