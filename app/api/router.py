from fastapi import APIRouter

from app.api.v1.endpoints import user_endpoints

# 创建API路由
api_router = APIRouter()

# 包含v1版本端点
api_router.include_router(xxx.router, prefix="/v1", tags=["examples"])

# 根据需要添加更多版本的路由
# api_router.include_router(
#     v2.router,
#     prefix="/v2",
#     tags=["v2"]
# )
