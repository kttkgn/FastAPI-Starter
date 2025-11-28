#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from functools import lru_cache
from typing import Optional, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ========== 基础应用配置（必选） ==========
    APP_TITLE: str = "FastAPI项目"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "极简FastAPI项目"

    # ========== 运行环境（控制 dev/prod 行为） ==========
    ENV: str = "dev"  # dev/prod

    # ========== 服务器配置 ==========
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # ========== API文档配置（dev显示，prod隐藏） ==========
    DOCS_URL: Optional[str] = "/docs" if ENV == "dev" else None
    REDOC_URL: Optional[str] = "/redoc" if ENV == "dev" else None
    OPENAPI_URL: str = "/api/openapi.json"

    # ========== CORS配置 ==========
    ALLOWED_ORIGINS: List[str] = ["*"]

    # ========== 日志配置（核心项） ==========
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"
    LOG_ROTATION: str = "1 day"  # 日志轮转规则
    LOG_RETENTION: str = "7 days"  # 日志保留时间
    LOG_COMPRESSION: str = "zip"  # 日志压缩格式
    LOG_SLOW_THRESHOLD: float = 1000  # 慢请求阈值（毫秒）

    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "RootQwe123"
    DB_NAME: str = "user"

    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # ========== Pydantic 基础配置（极简） ==========
    model_config = {
        "env_file": ".env",  # 支持从 .env 加载（可选）
        "case_sensitive": False,  # 不区分大小写（简化 ENV 变量书写）
        "extra": "ignore"  # 忽略未定义的配置
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """单例获取配置（缓存，避免重复初始化）"""
    return Settings()


# 全局配置实例（项目中直接导入使用）
settings = get_settings()
