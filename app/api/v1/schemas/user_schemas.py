#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用户接口层模型（Schemas）- 简化版（移除冗余校验函数）"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

from core.domain.user_domain import UserDomain


# ========== 请求模型 ==========
class UserCreateRequest(BaseModel):
    """创建用户请求模型"""
    # Field 原生校验已覆盖所有规则，无需自定义 validator
    username: str = Field(
        ...,
        min_length=3,
        max_length=20,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="用户名（3-20位字母/数字/下划线/减号）"
    )
    email: EmailStr = Field(..., description="用户邮箱")
    password: str = Field(..., min_length=8, description="原始密码（后端会哈希）")
    full_name: Optional[str] = Field(None, description="真实姓名")
    phone: Optional[str] = Field(None, description="手机号")
    is_superuser: bool = Field(False, description="是否超级管理员")


class UserUpdateRequest(BaseModel):
    """更新用户请求模型"""
    username: Optional[str] = Field(
        None,
        min_length=3,
        max_length=20,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="用户名（3-20位字母/数字/下划线/减号）"
    )
    email: Optional[EmailStr] = Field(None, description="用户邮箱")
    full_name: Optional[str] = Field(None, description="真实姓名")
    phone: Optional[str] = Field(None, description="手机号")
    is_active: Optional[bool] = Field(None, description="是否激活")


class UserListRequest(BaseModel):
    """用户列表查询请求模型"""
    skip: int = Field(0, ge=0, description="跳过条数")
    limit: int = Field(10, ge=1, le=100, description="查询条数")
    is_active: Optional[bool] = Field(None, description="是否激活")
    is_superuser: Optional[bool] = Field(None, description="是否超级管理员")


# ========== 响应模型 ==========
class UserResponse(BaseModel):
    """用户详情响应模型（脱敏）"""
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="用户邮箱")
    full_name: Optional[str] = Field(None, description="真实姓名")
    phone: Optional[str] = Field(None, description="手机号")
    is_active: bool = Field(..., description="是否激活")
    is_superuser: bool = Field(..., description="是否超级管理员")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True  # 支持从ORM模型/领域实体转换

    # 从领域实体转换为响应模型
    @classmethod
    def from_domain_entity(cls, entity: UserDomain) -> "UserResponse":
        return cls(
            id=entity.id,
            username=entity.username,
            email=entity.email,
            full_name=entity.full_name,
            phone=entity.phone,
            is_active=entity.is_active,
            is_superuser=entity.is_superuser,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


class UserListResponse(BaseModel):
    """用户列表响应模型"""
    total: int = Field(..., description="总条数")  # 如需分页可补充
    items: List[UserResponse] = Field(..., description="用户列表")
