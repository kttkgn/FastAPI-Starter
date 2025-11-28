#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用户管理接口 - 完整实现（适配UserService所有能力）"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Path, Query

# 项目内部导入
from app.api.dependencies.dependencies import get_user_service
from app.api.v1.schemas.user_schemas import (
    UserResponse, UserCreateRequest, UserUpdateRequest, UserListResponse
)
from app.adapters.db.models.user import UserCreate, UserUpdate
from app.core.schemas.base_response import BaseResponse
from app.core.services.user_service import UserService
from passlib.context import CryptContext

from app.utils.logger import log_info

# ========== 基础配置 ==========
PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")
user_router = APIRouter(tags=["用户管理"])


# ========== 核心接口实现 ==========
@user_router.post(
    "/",
    summary="创建用户",
    response_model=BaseResponse[UserResponse],
    description="创建新用户，自动哈希密码并校验用户名/邮箱唯一性"
)
async def create_user(
    req: UserCreateRequest,
    user_service: UserService = Depends(get_user_service)
):
    """创建用户接口"""
    # 请求模型转ORM模型（极简内联）
    req_dict = req.model_dump(exclude_none=True)
    req_dict["hashed_password"] = PWD_CONTEXT.hash(req_dict.pop("password"))
    log_info(f"req_dict : {req_dict}")
    user_create = UserCreate(**req_dict)

    # 调用服务层
    domain_user = await user_service.create_user(user_create)

    # 返回标准化响应
    return BaseResponse.success(
        data=UserResponse.from_domain_entity(domain_user),
        message="用户创建成功"
    )


@user_router.get(
    "/{user_id}",
    summary="查询用户详情",
    response_model=BaseResponse[UserResponse],
    description="根据用户ID查询单个用户详情"
)
async def get_user_detail(
    user_id: int = Path(..., ge=1, description="用户ID（正整数）"),
    user_service: UserService = Depends(get_user_service)
):
    """查询用户详情接口"""
    domain_user = await user_service.get_user_by_id(user_id)
    return BaseResponse.success(
        data=UserResponse.from_domain_entity(domain_user),
        message="查询用户详情成功"
    )


@user_router.get(
    "/batch/",
    summary="批量查询用户",
    response_model=BaseResponse[List[UserResponse]],
    description="根据用户ID列表批量查询用户"
)
async def batch_get_users(
    user_ids: List[int] = Query(..., ge=1, description="用户ID列表（多个用逗号分隔）"),
    user_service: UserService = Depends(get_user_service)
):
    """批量查询用户接口"""
    domain_users = await user_service.batch_get_users_by_ids(user_ids)
    # 转换为响应模型列表
    resp_data = [UserResponse.from_domain_entity(u) for u in domain_users]
    return BaseResponse.success(
        data=resp_data,
        message=f"批量查询成功，共返回 {len(resp_data)} 条数据"
    )


@user_router.get(
    "/",
    summary="查询用户列表",
    response_model=BaseResponse[UserListResponse],
    description="条件分页查询用户列表"
)
async def list_users(
    skip: int = Query(0, ge=0, description="跳过条数"),
    limit: int = Query(10, ge=1, le=100, description="每页条数"),
    is_active: Optional[bool] = Query(None, description="是否激活（可选）"),
    is_superuser: Optional[bool] = Query(None, description="是否超级管理员（可选）"),
    user_service: UserService = Depends(get_user_service)
):
    """条件查询用户列表接口"""
    # 调用服务层获取列表
    domain_users = await user_service.list_users(
        skip=skip,
        limit=limit,
        is_active=is_active,
        is_superuser=is_superuser
    )
    # 转换为响应模型
    items = [UserResponse.from_domain_entity(u) for u in domain_users]
    resp_data = UserListResponse(total=len(items), items=items)  # 注：真实场景total需仓库层返回总条数

    return BaseResponse.success(
        data=resp_data,
        message="查询用户列表成功"
    )


@user_router.patch(
    "/{user_id}",
    summary="更新用户信息",
    response_model=BaseResponse[UserResponse],
    description="更新用户基本信息，自动校验用户名/邮箱唯一性"
)
async def update_user(
    user_id: int = Path(..., ge=1, description="用户ID（正整数）"),
    req: UserUpdateRequest = Depends(),
    user_service: UserService = Depends(get_user_service)
):
    """更新用户信息接口"""
    # 请求模型转ORM模型（极简内联）
    req_dict = req.model_dump(exclude_none=True)
    user_update = UserUpdate(**req_dict)

    # 调用服务层更新
    domain_user = await user_service.update_user(user_id, user_update)

    return BaseResponse.success(
        data=UserResponse.from_domain_entity(domain_user),
        message="更新用户信息成功"
    )


@user_router.put(
    "/{user_id}/activate",
    summary="激活用户",
    response_model=BaseResponse[UserResponse],
    description="激活指定ID的用户"
)
async def activate_user(
    user_id: int = Path(..., ge=1, description="用户ID（正整数）"),
    user_service: UserService = Depends(get_user_service)
):
    """激活用户接口"""
    domain_user = await user_service.activate_user(user_id)
    return BaseResponse.success(
        data=UserResponse.from_domain_entity(domain_user),
        message="用户激活成功"
    )


@user_router.put(
    "/{user_id}/deactivate",
    summary="停用用户",
    response_model=BaseResponse[UserResponse],
    description="停用指定ID的用户"
)
async def deactivate_user(
    user_id: int = Path(..., ge=1, description="用户ID（正整数）"),
    user_service: UserService = Depends(get_user_service)
):
    """停用用户接口"""
    domain_user = await user_service.deactivate_user(user_id)
    return BaseResponse.success(
        data=UserResponse.from_domain_entity(domain_user),
        message="用户停用成功"
    )


@user_router.get(
    "/{user_id}/exists",
    summary="检查用户是否存在",
    response_model=BaseResponse[bool],
    description="检查指定ID的用户是否存在"
)
async def check_user_exists(
    user_id: int = Path(..., ge=1, description="用户ID（正整数）"),
    user_service: UserService = Depends(get_user_service)
):
    """检查用户是否存在接口"""
    exists = await user_service.check_user_exists(user_id)
    return BaseResponse.success(
        data=exists,
        message=f"用户{'存在' if exists else '不存在'}"
    )
