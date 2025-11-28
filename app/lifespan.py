#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FastAPI 生命周期管理 - 统一处理启动/关闭逻辑"""
from contextlib import asynccontextmanager
from fastapi import FastAPI

from adapters.messaging.celery_config import init_celery, shutdown_celery
from utils.logger import log_info, log_warn

# 导入资源初始化/关闭函数
from adapters.db.session import init_db, close_db_connection


# 生命周期初始化锁
_LIFESPAN_INITIALIZED = False


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """
    FastAPI 生命周期钩子
    - 启动时：初始化数据库、Celery 等资源
    - 关闭时：优雅释放资源
    """
    global _LIFESPAN_INITIALIZED
    if _LIFESPAN_INITIALIZED:
        yield
        return

    # ========== 应用启动阶段 ==========
    log_info("===== 应用启动中，执行初始化 =====")

    # 1. 初始化数据库连接池
    await init_db()

    # 2. 初始化 Celery
    init_celery()

    _LIFESPAN_INITIALIZED = True
    log_info("===== 应用初始化完成 =====")

    # 应用运行中（yield 之前是启动逻辑，之后是关闭逻辑）
    yield

    # ========== 应用关闭阶段 ==========
    log_info("===== 应用关闭中，释放资源 =====")

    # 1. 关闭数据库连接池
    await close_db_connection()

    # 2. 关闭 Celery
    shutdown_celery()

    log_info("===== 应用资源释放完成 =====")
