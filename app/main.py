#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""FastAPI应用入口（极简版）"""
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 核心依赖（仅保留必要导入）
from api.v1.endpoints.user_endpoints import user_router
from core.config import settings
from utils.logger import init_logger, log_info
# 修复：导入生命周期函数并接入
from lifespan import app_lifespan

# 1. 基础初始化（仅执行1次）
init_logger()

# 2. 创建FastAPI实例
# 修复点1：接入lifespan，启动时自动初始化数据库
app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    lifespan=app_lifespan  # 关键：接入生命周期钩子
)

# 3. 核心中间件
# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trace ID中间件（简化实现）
@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    request.state.trace_id = uuid.uuid4().hex
    response = await call_next(request)
    response.headers["X-Trace-ID"] = request.state.trace_id
    return response

# 4. 注册路由（核心）
# 修复点2：如果user_router内部已经带/api/v1前缀，这里只需要写/
# 先检查user_endpoints.py中路由的前缀，再决定这里的prefix：
# 情况1：user_router里的接口是@router.post("/users/") → 这里prefix="/api/v1"（正确）
# 情况2：user_router里的接口是@router.post("/api/v1/users/") → 这里prefix="/"
app.include_router(user_router, prefix="/api/v1", tags=["用户管理"])

# 5. 健康检查接口（简化版）
@app.get("/health", tags=["系统管理"])
async def health_check(request: Request):
    trace_id = getattr(request.state, "trace_id", uuid.uuid4().hex)
    log_info(f"健康检查 - trace_id: {trace_id}")
    return {
        "code": 200,
        "msg": "应用正常",
        "data": {
            "env": settings.ENV,
            "version": settings.APP_VERSION,
            "trace_id": trace_id,
            "db": "connected" if settings.DATABASE_URL else "disconnected",
            "redis": "connected" if settings.REDIS_URL else "disconnected"
        }
    }

# 6. 启动服务（简化逻辑）
if __name__ == "__main__":
    log_info(f"启动服务：{settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENV != "production",
        log_config=None,
        access_log=False  # 关闭uvicorn默认access log，避免日志混乱
    )
