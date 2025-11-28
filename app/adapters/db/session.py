#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据库连接管理 - 修复所有类型提示问题"""
import asyncio
from typing import Optional

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker
)
from app.core.config import settings
from app.utils.logger import log_info, log_error, log_warn

# ------------------------------
# 全局变量 + 异步锁（修复并发初始化问题）
# ------------------------------
engine: Optional[AsyncEngine] = None
AsyncSessionLocal: Optional[async_sessionmaker[AsyncSession]] = None
# 修复点：增加异步锁，防止并发初始化
_db_init_lock = asyncio.Lock()


# ------------------------------
# 数据库连接池初始化
# ------------------------------
async def init_db() -> None:
    """初始化数据库连接池（应用启动时调用）"""
    global engine, AsyncSessionLocal
    # 修复点：异步锁保护，避免并发调用
    async with _db_init_lock:
        if engine is not None and AsyncSessionLocal is not None:
            log_warn("数据库连接池已初始化，跳过重复调用")
            return

        try:
            engine_instance: AsyncEngine = create_async_engine(
                settings.DATABASE_URL,
                pool_size=settings.DB_POOL_SIZE,
                max_overflow=settings.DB_MAX_OVERFLOW,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=settings.ENV == "dev",
                future=True
            )

            session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
                bind=engine_instance,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False
            )

            # 测试连接
            async with engine_instance.connect() as conn:
                await conn.exec_driver_sql("SELECT 1")

            engine = engine_instance
            AsyncSessionLocal = session_factory

            log_info("数据库连接池初始化成功",
                    db_url=settings.DATABASE_URL.split("@")[-1],
                    pool_size=settings.DB_POOL_SIZE)

        except Exception as e:
            log_error("数据库连接池初始化失败", error_msg=str(e), exc_info=True)
            raise


# ------------------------------
# 数据库连接池关闭
# ------------------------------
async def close_db_connection() -> None:
    """关闭数据库连接池（应用关闭时调用）"""
    global engine, AsyncSessionLocal
    async with _db_init_lock:
        if engine is None:
            return

        try:
            if isinstance(engine, AsyncEngine):
                await engine.dispose()

            engine = None
            AsyncSessionLocal = None
            log_info("数据库连接池已优雅关闭")

        except Exception as e:
            log_error("数据库连接池关闭失败", error_msg=str(e), exc_info=True)
            raise
