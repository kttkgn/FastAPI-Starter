#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异常处理器（统一注册）"""
import traceback
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

# 导入自定义异常（根据实际项目调整）
from app.core.exceptions import (
    UserNotFoundError,
    UserAlreadyExistsError,
    InvalidUserUpdateError
)


# ========== 异常处理器实现 ==========
async def user_not_found_handler(request: Request, exc: UserNotFoundError):
    """用户不存在异常处理器"""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"code": 404, "message": str(exc),
                 "trace_id": getattr(request.state, "trace_id", "")}
    )


async def user_already_exists_handler(request: Request, exc: UserAlreadyExistsError):
    """用户已存在异常处理器"""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"code": 409, "message": str(exc),
                 "trace_id": getattr(request.state, "trace_id", "")}
    )


async def invalid_update_handler(request: Request, exc: InvalidUserUpdateError):
    """用户更新参数无效异常处理器"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"code": 400, "message": str(exc),
                 "trace_id": getattr(request.state, "trace_id", "")}
    )


async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器（打印完整堆栈和异常链）"""
    # 构建异常信息（包含堆栈和异常链）
    error_details = []

    # 打印主异常堆栈
    main_traceback = traceback.format_exc()
    error_details.append(f"主异常信息:\n{main_traceback}")

    # 处理异常链（__cause__ 和 __context__）
    current_exc = exc
    chain_index = 1

    # 遍历 __cause__（显式异常链，raise ... from ...）
    while current_exc.__cause__ is not None:
        cause_exc = current_exc.__cause__
        cause_trace = ''.join(traceback.format_tb(
            cause_exc.__traceback__)) if cause_exc.__traceback__ else "无堆栈信息"
        error_details.append(
            f"\n异常链 {chain_index} (显式 cause):\n"
            f"异常类型: {type(cause_exc).__name__}\n"
            f"异常信息: {str(cause_exc)}\n"
            f"堆栈信息:\n{cause_trace}"
        )
        current_exc = cause_exc
        chain_index += 1

    # 重置并遍历 __context__（隐式异常链）
    current_exc = exc
    while current_exc.__context__ is not None and current_exc.__context__ is not exc:
        context_exc = current_exc.__context__
        context_trace = ''.join(traceback.format_tb(
            context_exc.__traceback__)) if context_exc.__traceback__ else "无堆栈信息"
        error_details.append(
            f"\n异常链 {chain_index} (隐式 context):\n"
            f"异常类型: {type(context_exc).__name__}\n"
            f"异常信息: {str(context_exc)}\n"
            f"堆栈信息:\n{context_trace}"
        )
        current_exc = context_exc
        chain_index += 1

    # 打印完整的异常信息到控制台/日志
    full_error_msg = '\n'.join(error_details)
    print("=" * 80)
    print("全局异常捕获 - 完整错误信息:")
    print(full_error_msg)
    print("=" * 80)

    # 返回标准化的JSON响应
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "trace_id": getattr(request.state, "trace_id", ""),
            # 生产环境建议注释掉以下行，仅在调试时启用
            # "debug_info": full_error_msg  # 调试用：返回详细错误信息
        }
    )


# ========== 批量注册函数（核心：解决未定义问题） ==========
def register_exception_handlers(app: FastAPI):
    """批量注册所有异常处理器"""
    app.add_exception_handler(UserNotFoundError, user_not_found_handler)
    app.add_exception_handler(UserAlreadyExistsError, user_already_exists_handler)
    app.add_exception_handler(InvalidUserUpdateError, invalid_update_handler)
    app.add_exception_handler(Exception, global_exception_handler)
