#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全局标准化响应模型（依赖枚举，但解耦存放）"""
from typing import Optional, Generic, TypeVar
from pydantic import BaseModel, Field

# 导入枚举（依赖但解耦，枚举是纯数据，模型是逻辑）
from core.enums.response_enums import ResponseCodeEnum

# 泛型类型变量（支持任意数据类型）
DataT = TypeVar("DataT")


class BaseResponse(BaseModel, Generic[DataT]):
    """全局通用响应模型（所有接口的标准化返回格式）"""
    # 默认值取自枚举，保证一致性
    code: int = Field(
        ResponseCodeEnum.SUCCESS.code,
        description="响应码（参考ResponseCodeEnum）"
    )
    message: str = Field(
        ResponseCodeEnum.SUCCESS.msg,
        description="响应提示信息"
    )
    data: Optional[DataT] = Field(None, description="响应数据体")

    class Config:
        arbitrary_types_allowed = True  # 支持任意数据类型（如领域实体）
        use_enum_values = True  # 序列化时用枚举值而非对象

    # 快捷方法（封装响应逻辑，简化接口代码）
    @classmethod
    def success(cls, data: Optional[DataT] = None,
                message: str = None) -> "BaseResponse[DataT]":
        """快速创建成功响应"""
        return cls(
            code=ResponseCodeEnum.SUCCESS.code,
            message=message or ResponseCodeEnum.SUCCESS.msg,
            data=data
        )

    @classmethod
    def fail(cls, enum: ResponseCodeEnum,
             data: Optional[DataT] = None) -> "BaseResponse[DataT]":
        """快速创建失败响应（基于枚举）"""
        return cls(
            code=enum.code,
            data=data
        )

    @classmethod
    def custom(cls, code: int, message: str,
               data: Optional[DataT] = None) -> "BaseResponse[DataT]":
        """自定义响应（特殊场景）"""
        return cls(code=code, message=message, data=data)
