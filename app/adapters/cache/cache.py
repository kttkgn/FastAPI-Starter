#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""极简异步 Redis 客户端（适配 Celery 场景）"""
import hashlib
import json
import logging
import pickle
import time
import uuid
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, Awaitable

import asyncio
import redis.asyncio as redis
from redis.exceptions import ConnectionError, TimeoutError
from app.core.config import settings  # 导入极简版 Pydantic 配置

# 类型定义
T = TypeVar("T")
AsyncFunc = Callable[..., Awaitable[T]]

# 极简日志配置
logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, settings.LOG_LEVEL))


class AsyncRedisCache:
    """极简异步 Redis 客户端（适配 Celery）"""
    _instance: Optional["AsyncRedisCache"] = None
    _lock = asyncio.Lock()

    def __new__(cls):
        """单例模式（Celery 多进程共享）"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._redis_client: Optional[redis.Redis] = None
        self._init_client()

    def _init_client(self) -> None:
        """初始化 Redis 客户端（适配极简配置）"""
        if not settings.REDIS_URL:
            logger.error("Redis URL 未配置")
            raise ValueError("REDIS_URL is required")

        # 解析 Redis URL（适配极简配置的 URL 格式）
        try:
            self._redis_client = redis.from_url(
                url=settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                health_check_interval=30,
                max_connections=20,
                retry_on_timeout=True,
                retry_on_error=[ConnectionError, TimeoutError],
            )
            logger.info(f"Redis 客户端初始化成功: {settings.REDIS_URL}")
        except Exception as e:
            logger.error(f"Redis 初始化失败: {str(e)}", exc_info=True)
            raise

    @property
    def redis_client(self) -> redis.Redis:
        """懒加载 + 断线重连"""
        if not self._redis_client or not self._redis_client.connection_pool:
            self._init_client()
        return self._redis_client

    # ========== 核心基础方法 ==========
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存（适配 Celery 序列化格式）"""
        try:
            value = await self.redis_client.get(key)
            if not value:
                return None

            # 兼容 Celery pickle 格式
            if value.startswith('pickle:'):
                return pickle.loads(value[7:].encode('latin-1'))
            # 兼容 JSON 格式
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except (ConnectionError, TimeoutError):
            logger.error(f"Redis 连接异常 - GET {key}")
            self._init_client()
            return None
        except Exception as e:
            logger.error(f"GET {key} 失败: {str(e)}", exc_info=True)
            return None

    async def set(
        self,
        key: str,
        value: Any,
        expire_seconds: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """设置缓存（支持 Celery 任务结果）"""
        if nx and xx:
            logger.error("nx/xx 不能同时为 True")
            return False

        try:
            # 序列化：Celery 复杂类型用 pickle，其他用 JSON
            if isinstance(value, (dict, list, tuple)) and not isinstance(value, str):
                data = f"pickle:{pickle.dumps(value).decode('latin-1')}"
            else:
                data = json.dumps(value, default=str, ensure_ascii=False)

            # 执行设置
            if expire_seconds:
                result = await self.redis_client.setex(key, expire_seconds, data)
            else:
                result = await self.redis_client.set(key, data, nx=nx, xx=xx)
            return result is True
        except (ConnectionError, TimeoutError):
            logger.error(f"Redis 连接异常 - SET {key}")
            self._init_client()
            return False
        except Exception as e:
            logger.error(f"SET {key} 失败: {str(e)}", exc_info=True)
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            return await self.redis_client.delete(key) > 0
        except Exception as e:
            logger.error(f"DEL {key} 失败: {str(e)}", exc_info=True)
            return False

    # ========== Celery 核心适配方法 ==========
    async def acquire_lock(
        self,
        lock_key: str,
        lock_timeout: int = 10,
        retry_interval: float = 0.05,
        max_retry_times: Optional[int] = None
    ) -> Optional[str]:
        """Celery 分布式锁"""
        token = str(uuid.uuid4())
        retry_count = 0
        end_time = time.time() + lock_timeout

        try:
            while time.time() < end_time:
                if max_retry_times and retry_count >= max_retry_times:
                    break

                if await self.redis_client.set(lock_key, token, nx=True,
                                               ex=lock_timeout):
                    logger.debug(f"获取锁成功: {lock_key[:20]}...")
                    return token

                retry_count += 1
                await asyncio.sleep(retry_interval)

            logger.debug(f"获取锁超时: {lock_key[:20]}...")
            return None
        except Exception as e:
            logger.error(f"获取锁失败: {lock_key[:20]}... {str(e)}")
            self._init_client()
            return None

    async def release_lock(self, lock_key: str, token: str) -> bool:
        """释放 Celery 分布式锁"""
        if not token:
            return False

        try:
            lua_script = """
            if redis.call("GET", KEYS[1]) == ARGV[1] then
                return redis.call("DEL", KEYS[1])
            else
                return 0
            end
            """
            return await self.redis_client.eval(lua_script, 1, lock_key, token) == 1
        except Exception as e:
            logger.error(f"释放锁失败: {lock_key[:20]}... {str(e)}")
            return False

    # ========== 精简常用方法（保留核心） ==========
    async def exists(self, key: str) -> bool:
        return await self.redis_client.exists(key) == 1

    async def expire(self, key: str, expire_seconds: int) -> bool:
        return expire_seconds > 0 and await self.redis_client.expire(key,
                                                                     expire_seconds) == 1

    async def clear_pattern(self, pattern: str, batch_size: int = 100) -> int:
        """批量清理 Celery 缓存"""
        if not pattern:
            return 0

        try:
            cursor, total_deleted = 0, 0
            while True:
                cursor, keys = await self.redis_client.scan(cursor=cursor,
                                                            match=pattern,
                                                            count=batch_size)
                if keys:
                    total_deleted += await self.redis_client.delete(*keys)
                if cursor == 0:
                    break
            logger.info(f"清理 {pattern} 完成，共删除 {total_deleted} 个 key")
            return total_deleted
        except Exception as e:
            logger.error(f"批量清理失败: {pattern} {str(e)}")
            return 0


# 全局单例（Celery 多进程共享）
async_redis_cache = AsyncRedisCache()


# ========== 极简装饰器（适配 Celery） ==========
def async_redis_lock(lock_prefix: str, expire: int = 10, raise_on_fail: bool = True):
    """Celery 分布式锁装饰器"""

    def decorator(func: AsyncFunc[T]) -> AsyncFunc[T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            if not settings.REDIS_URL:  # 极简判断 Redis 是否启用
                return await func(*args, **kwargs)

            lock_key = f"{lock_prefix}:{func.__name__}"
            token = await async_redis_cache.acquire_lock(lock_key, lock_timeout=expire)
            if not token:
                msg = f"任务 {func.__name__} 已锁定"
                if raise_on_fail:
                    raise RuntimeError(msg)
                logger.warning(msg)
                return None  # type: ignore

            try:
                return await func(*args, **kwargs)
            finally:
                await async_redis_cache.release_lock(lock_key, token)

        return wrapper

    return decorator


def async_cache(prefix: str = "", expire_seconds: int = 300, ignore_none: bool = False):
    """Celery 缓存装饰器"""

    def decorator(func: AsyncFunc[T]) -> AsyncFunc[T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            if not settings.REDIS_URL:
                return await func(*args, **kwargs)

            # 生成缓存 key
            payload = pickle.dumps((args, kwargs))
            cache_key = f"{prefix or func.__name__}:{hashlib.sha256(payload).hexdigest()[:16]}"

            # 读取缓存
            cached = await async_redis_cache.get(cache_key)
            if cached is not None:
                return cached

            # 执行并缓存结果
            result = await func(*args, **kwargs)
            if result is not None or not ignore_none:
                await async_redis_cache.set(cache_key, result, expire_seconds)
            return result

        return wrapper

    return decorator
