#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核心异常定义"""
from fastapi import HTTPException, status


class BaseAppException(HTTPException):
    """基础异常类"""
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class UserAlreadyExistsError(BaseAppException):
    """用户已存在异常"""
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_409_CONFLICT)


class UserNotFoundError(BaseAppException):
    """用户不存在异常"""
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_404_NOT_FOUND)


class InvalidUserUpdateError(BaseAppException):
    """用户更新异常"""
    def __init__(self, detail: str):
        super().__init__(detail=detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
