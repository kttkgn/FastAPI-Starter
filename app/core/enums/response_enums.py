#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""纯响应码枚举（无任何模型依赖）"""
from enum import Enum, unique


@unique
class ResponseCodeEnum(Enum):
    """响应码枚举（仅绑定code+msg，无业务逻辑）"""
    # 通用响应
    SUCCESS = (200, "操作成功")
    FAIL = (500, "操作失败")
    # 用户业务响应
    USER_EXIST = (409, "用户名/邮箱已存在")
    USER_NOT_FOUND = (404, "用户不存在")
    # 参数校验响应
    PARAM_ERROR = (422, "参数校验失败")

    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg = msg

    # 可选：添加通用工具方法（仅枚举相关）
    @classmethod
    def get_by_code(cls, code: int) -> "ResponseCodeEnum":
        """根据code获取枚举实例"""
        for item in cls:
            if item.code == code:
                return item
        return cls.FAIL
