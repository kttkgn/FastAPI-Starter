#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""请求日志中间件 - 基于loguru+链路追踪（Trace ID/Span ID）"""
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# 导入自定义日志工具
from utils.logger import (
    trace_middleware as custom_trace_middleware,
    log_info, log_warn, log_exc
)

class LoggingMiddleware(BaseHTTPMiddleware):
    """基于loguru的请求日志中间件（兼容原有trace_middleware）"""
    async def dispatch(self, request: Request, call_next) -> Response:
        # 复用自定义的trace_middleware核心逻辑（已包含链路ID生成+基础日志）
        # 此处仅做扩展，保留原有链路追踪能力
        try:
            response = await custom_trace_middleware(request, call_next)
            return response
        except Exception as e:
            log_exc("请求处理异常",
                   method=request.method,
                   path=request.url.path,
                   client_ip=request.client.host,
                   error=str(e))
            raise
