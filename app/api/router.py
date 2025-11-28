from fastapi import APIRouter

from app.api.v1.endpoints.user_endpoints import user_router

# 创建API路由
api_router = APIRouter(prefix="/v1")

api_router.include_router(user_router, prefix="/user", tags=["用户管理"])
