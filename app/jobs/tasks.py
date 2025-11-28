# app/jobs/tasks.py
import time
import logging

from adapters.cache.cache import async_redis_cache
from adapters.messaging.celery_config import celery_app

# 日志配置
logger = logging.getLogger(__name__)


# ------------------------------
# 示例1：基础任务（带 Redis 状态记录）
# ------------------------------
@celery_app.task(
    bind=True,  # 绑定任务实例，可访问 self 属性
    retry_backoff=2,  # 重试退避（指数级延迟）
    retry_kwargs={"max_retries": 3},  # 最大重试次数
    name="demo:user_data_sync"  # 显式任务名，便于管理
)
async def sync_user_data(self, user_id: int, force_refresh: bool = False):
    # 1. 定义 Redis Key（规范命名）
    cache_key = f"user:data:{user_id}"
    lock_key = f"lock:user:sync:{user_id}"
    status_key = f"task:status:{self.request.id}"  # 任务ID关联状态

    try:
        # 2. 记录任务开始状态
        await async_redis_cache.set(
            status_key,
            {"status": "running", "start_time": time.time(), "user_id": user_id},
            expire_seconds=3600
        )

        # 3. 检查缓存（避免重复计算）
        if not force_refresh:
            cached_data = await async_redis_cache.get(cache_key)
            if cached_data:
                logger.info(f"用户 {user_id} 数据缓存命中，跳过同步")
                await async_redis_cache.set(
                    status_key,
                    {"status": "success", "msg": "缓存命中", "user_id": user_id},
                    expire_seconds=3600
                )
                return {"code": 0, "data": cached_data, "msg": "缓存命中"}

        # 4. 分布式锁（防止并发同步）
        lock_token = await async_redis_cache.acquire_lock(
            lock_key,
            lock_timeout=60,  # 锁超时60秒
            max_retry_times=5  # 最大重试5次
        )
        if not lock_token:
            raise RuntimeError(f"用户 {user_id} 同步任务已在执行中")

        # 5. 模拟业务逻辑（替换为实际业务）
        logger.info(f"开始同步用户 {user_id} 数据...")
        time.sleep(2)  # 模拟耗时操作
        user_data = {
            "id": user_id,
            "name": f"User_{user_id}",
            "sync_time": time.time(),
            "source": "external_api"
        }

        # 6. 写入 Redis 缓存（设置过期时间）
        await async_redis_cache.set(
            cache_key,
            user_data,
            expire_seconds=1800  # 缓存30分钟
        )

        # 7. 释放分布式锁
        await async_redis_cache.release_lock(lock_key, lock_token)

        # 8. 更新任务成功状态
        await async_redis_cache.set(
            status_key,
            {
                "status": "success",
                "end_time": time.time(),
                "user_id": user_id,
                "data_size": len(str(user_data))
            },
            expire_seconds=3600
        )

        logger.info(f"用户 {user_id} 数据同步完成")
        return {"code": 0, "data": user_data, "msg": "同步成功"}

    except Exception as e:
        # 9. 异常处理：更新失败状态 + 重试
        logger.error(f"用户 {user_id} 数据同步失败: {str(e)}", exc_info=True)
        await async_redis_cache.set(
            status_key,
            {"status": "failed", "error": str(e), "user_id": user_id},
            expire_seconds=3600
        )
        # 触发重试（符合重试条件则自动重试）
        raise self.retry(exc=e, countdown=5)


# ------------------------------
# 示例2：批量任务（Redis 批量操作）
# ------------------------------
@celery_app.task(
    name="demo:batch_clear_cache",
    rate_limit="10/m"  # 限速：每分钟最多10次
)
async def batch_clear_cache(pattern: str = "user:data:*", batch_size: int = 100):
    """
    批量清理 Redis 缓存
    :param pattern: 缓存Key匹配模式
    :param batch_size: 批量删除大小
    """
    start_time = time.time()
    # 调用 Redis 批量清理方法
    deleted_count = await async_redis_cache.clear_pattern(pattern, batch_size)

    # 记录清理结果
    result = {
        "pattern": pattern,
        "deleted_count": deleted_count,
        "cost_time": round(time.time() - start_time, 2),
        "timestamp": time.time()
    }
    logger.info(f"批量清理缓存完成 | 模式: {pattern} | 删除数量: {deleted_count}")
    return result


# ------------------------------
# 示例3：定时任务（需配置 Beat）
# ------------------------------
@celery_app.task(
    name="demo:clean_expired_tasks",
    schedule=3600  # 每小时执行一次（需启用 celery beat）
)
async def clean_expired_task_status():
    """清理过期的任务状态缓存"""
    # 匹配所有任务状态Key并清理（TTL < 0 表示已过期）
    pattern = "task:status:*"
    cursor = 0
    deleted = 0

    while True:
        cursor, keys = await async_redis_cache.redis_client.scan(cursor=cursor,
                                                                 match=pattern,
                                                                 count=100)
        for key in keys:
            ttl = await async_redis_cache.ttl(key)
            if ttl < 0:  # 已过期（-1 永不过期 / -2 不存在）
                await async_redis_cache.delete(key)
                deleted += 1
        if cursor == 0:
            break

    logger.info(f"清理过期任务状态完成 | 共删除 {deleted} 个Key")
    return {"deleted_count": deleted}
