#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""依赖注入配置中心 - 统一管理所有依赖实例"""
from typing import Callable, Type, TypeVar, AsyncGenerator, Optional, Any
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

# 导入基础设施依赖
from app.adapters.cache.cache import async_redis_cache
from app.adapters.db.session import AsyncSessionLocal, init_db
from app.adapters.external.http_client import HttpClient

# 导入仓库和服务
from app.adapters.db.repositories.base_repositories import BaseRepository
from app.adapters.db.repositories.user_repositories import UserRepository
from app.core.services.user_service import UserService
from app.utils.logger import log_error, log_warn

# 类型变量（限制仓库类型）
RepoType = TypeVar("RepoType", bound=BaseRepository)


# ------------------------------
# 获取数据库会话（适配 async_sessionmaker）
# ------------------------------
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（自动提交/回滚/关闭）"""
    # 修复点：优先使用已初始化的会话工厂，避免重复触发init_db
    if AsyncSessionLocal is None:
        log_warn("数据库连接池未初始化，自动触发初始化")
        await init_db()

    if AsyncSessionLocal is None:
        raise RuntimeError("数据库连接池初始化失败，请检查数据库配置")

    # 使用 2.0 会话工厂创建会话
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            log_error("数据库会话执行失败，已回滚", error_msg=str(e), exc_info=True)
            raise e
        finally:
            await session.close()


async def get_redis_cache() -> AsyncGenerator[Any, None]:
    """获取 Redis 缓存实例"""
    yield async_redis_cache


async def get_http_client(
    base_url: Optional[str] = None,
    timeout: int = 10,
    retries: int = 2
) -> AsyncGenerator[HttpClient, None]:
    """获取 HTTP 客户端（支持自定义参数）"""
    async with HttpClient(
        base_url=base_url,
        timeout=timeout,
        retries=retries
    ) as client:
        yield client


# 默认 HTTP 客户端（固定参数，直接供外部使用）
get_default_http_client = Depends(get_http_client)


# ========== 仓库依赖工厂 ==========
def get_repository(repo_class: Type[RepoType]) -> Callable[[AsyncSession], RepoType]:
    """通用仓库依赖工厂函数"""
    def _get_repo(db_session: AsyncSession = Depends(get_db_session)) -> RepoType:
        return repo_class(db_session)
    return _get_repo


get_user_repo = get_repository(UserRepository)


async def get_user_service(
    user_repo: UserRepository = Depends(get_user_repo)
) -> UserService:
    """获取用户服务实例（自动注入用户仓库）"""
    return UserService(user_repo)
