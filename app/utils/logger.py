#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全局日志工具 - 基于loguru+链路追踪（Trace ID/Span ID）"""
import uuid
import time

import logging
from contextvars import ContextVar
from loguru import logger
from typing import Any, Dict, Callable, Awaitable, Optional
from app.core.config import settings

# ------------------------------
# 链路追踪上下文（Trace/Span ID）
# ------------------------------
trace_id_ctx: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
span_id_ctx: ContextVar[Optional[str]] = ContextVar("span_id", default=None)


# ------------------------------
# 核心工具函数
# ------------------------------
def generate_id() -> str:
    """生成8位短UUID作为Trace/Span ID"""
    return str(uuid.uuid4())[:8]


def get_trace_id() -> str:
    """获取当前请求的Trace ID（不存在则生成）"""
    trace_id = trace_id_ctx.get()
    if not trace_id:
        trace_id = generate_id()
        trace_id_ctx.set(trace_id)
    return trace_id


def new_span() -> str:
    """生成新的Span ID并绑定到上下文"""
    span_id = generate_id()
    span_id_ctx.set(span_id)
    return span_id


def log_context(extra: Dict[str, Any] = None, logger_name: str = "app") -> Dict[
    str, Any]:
    """
    构建日志上下文（包含链路ID、时间戳等）
    :param extra: 额外日志字段
    :param logger_name: 日志来源名称（默认app，Uvicorn日志会覆盖）
    """
    base = {
        "trace_id": get_trace_id(),
        "span_id": span_id_ctx.get() or new_span(),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "logger_name": logger_name,  # 确保默认存在该字段
    }
    if extra:
        base.update(extra)
    return base


# ------------------------------
# 日志封装函数（简化调用）
# ------------------------------
def log(level: str, msg: str, **kwargs):
    """通用日志函数"""
    # 提取并删除logger_name（避免重复），没有则用默认值
    logger_name = kwargs.pop("logger_name", "app")
    ctx = log_context(kwargs, logger_name=logger_name)
    logger.bind(**ctx).__getattribute__(level)(msg)


def log_info(msg: str, **kwargs):
    """INFO级别日志"""
    log("info", msg, **kwargs)


def log_debug(msg: str, **kwargs):
    """DEBUG级别日志（开发环境）"""
    log("debug", msg, **kwargs)


def log_warn(msg: str, **kwargs):
    """WARNING级别日志"""
    log("warning", msg, **kwargs)


def log_error(msg: str, **kwargs):
    """ERROR级别日志"""
    log("error", msg, **kwargs)


def log_exc(msg: str, **kwargs):
    """EXCEPTION级别日志（含堆栈信息）"""
    log("exception", msg, **kwargs)


# ------------------------------
# Uvicorn日志适配（核心）
# ------------------------------
class UvicornLoguruHandler(logging.Handler):
    """将Uvicorn日志转发到Loguru的处理器"""

    def emit(self, record: logging.LogRecord):
        try:
            # 获取日志级别（兼容loguru）
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 构建上下文（包含链路ID + Uvicorn日志来源）
        ctx = log_context(
            extra={
                "module": record.module,
                "funcName": record.funcName,
                "lineno": record.lineno,
            },
            logger_name=record.name  # 使用Uvicorn的logger名称（如uvicorn.access）
        )

        # 格式化日志消息
        message = record.getMessage()

        # 转发到loguru
        logger.bind(**ctx).log(level, message)


def setup_uvicorn_logging():
    """配置Uvicorn日志，使其输出到Loguru"""
    # 获取uvicorn的所有logger
    uvicorn_loggers = [
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "fastapi",
        "sqlalchemy.engine.Engine",  # 可选：捕获sqlalchemy日志
    ]

    # 为每个uvicorn logger添加自定义处理器
    for logger_name in uvicorn_loggers:
        uvicorn_log = logging.getLogger(logger_name)
        uvicorn_log.handlers = [UvicornLoguruHandler()]  # 替换原有处理器
        uvicorn_log.setLevel(settings.LOG_LEVEL)  # 统一日志级别
        uvicorn_log.propagate = False  # 防止重复输出


# ------------------------------
# 日志初始化（全局配置）
# ------------------------------
def init_logger():
    """初始化loguru配置（多格式输出+轮转+压缩）"""
    # 清除默认配置
    logger.remove()

    # 1. 控制台输出（带颜色+链路ID + 日志来源）
    logger.add(
        lambda m: print(m, end=""),
        level=settings.LOG_LEVEL,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "Trace:<cyan>{extra[trace_id]}</cyan> | "
            "Span:<cyan>{extra[span_id]}</cyan> | "
            "{extra[logger_name]:<12} | "  # 日志来源名称
            "<level>{message}</level>"
        ),
        colorize=True,
        enqueue=True  # 异步日志，提升性能
    )

    # 2. 普通文本日志文件（按天轮转）
    logger.add(
        f"{settings.LOG_DIR}/app_{{time:YYYY-MM-DD}}.log",
        level=settings.LOG_LEVEL,
        rotation=settings.LOG_ROTATION,  # 如 "00:00" 每天凌晨轮转
        retention=settings.LOG_RETENTION,  # 如 "7 days" 保留7天
        compression=settings.LOG_COMPRESSION,  # 如 "zip" 压缩旧日志
        enqueue=True,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | "
            "{level: <8} | "
            "Trace:{extra[trace_id]} | "
            "Span:{extra[span_id]} | "
            "{extra[logger_name]:<12} | "
            "{message}"
        )
    )

    # 3. JSON格式日志文件（便于日志分析平台解析）
    logger.add(
        f"{settings.LOG_DIR}/json_{{time:YYYY-MM-DD}}.log",
        serialize=True,  # 序列化为JSON
        level=settings.LOG_LEVEL,
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        enqueue=True
    )

    # 配置Uvicorn日志转发
    setup_uvicorn_logging()


# ------------------------------
# 链路追踪中间件（核心）
# ------------------------------
async def trace_middleware(request, call_next):
    """FastAPI中间件 - 为每个请求生成Trace/Span ID，记录请求生命周期"""
    # 初始化链路ID
    trace_id_ctx.set(generate_id())
    new_span()

    # 记录请求开始
    log_info(
        "请求开始",
        method=request.method,
        path=request.url.path,
        client_ip=request.client.host,
        user_agent=request.headers.get("user-agent", ""),
        logger_name="fastapi.request"  # 自定义业务日志来源
    )

    # 执行请求并计时
    start_time = time.time()
    try:
        response = await call_next(request)
    except Exception as e:
        log_exc("请求处理异常", error=str(e), logger_name="fastapi.error")
        raise

    # 计算耗时
    cost_ms = round((time.time() - start_time) * 1000, 2)

    # 记录请求结束
    log_info(
        "请求结束",
        status_code=response.status_code,
        cost_ms=cost_ms,
        logger_name="fastapi.request"
    )

    # 慢请求检测（超过阈值告警，配置中是毫秒，直接对比）
    if cost_ms > settings.LOG_SLOW_THRESHOLD:
        log_warn(
            "慢请求告警",
            cost_ms=cost_ms,
            threshold_ms=settings.LOG_SLOW_THRESHOLD,
            logger_name="fastapi.warning"
        )

    # 将Trace ID返回给前端（便于问题排查）
    response.headers["X-Trace-ID"] = get_trace_id()
    return response


# ------------------------------
# 异步任务包装器（兼容Celery/异步函数）
# ------------------------------
async def async_task_wrapper(func: Callable[..., Awaitable], *args, **kwargs):
    """异步任务包装器 - 继承主线程Trace ID，生成新Span ID"""
    # 继承当前上下文的Trace ID（若存在）
    current_trace_id = get_trace_id()
    trace_id_ctx.set(current_trace_id)
    # 生成新的Span ID（区分任务链路）
    new_span()

    # 记录任务开始
    log_info(
        "异步任务开始",
        task_name=func.__name__,
        trace_id=current_trace_id,
        logger_name="celery.task"
    )

    try:
        # 执行异步任务
        result = await func(*args, **kwargs)
        # 记录任务完成
        log_info("异步任务完成", task_name=func.__name__, logger_name="celery.task")
        return result
    except Exception as e:
        # 记录任务异常
        log_exc("异步任务异常", task_name=func.__name__, error=str(e),
                logger_name="celery.error")
        raise
