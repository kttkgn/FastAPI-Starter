from typing import Optional
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, Integer, String, Boolean
from app.adapters.db.models.base import BaseModel


class User(BaseModel, table=True):
    __tablename__ = "users"
    __table_args__ = {
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
        "comment": "用户表",
    }

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            Integer,
            primary_key=True,
            autoincrement=True,
            nullable=False,
            comment="用户ID",
        ),
    )

    username: str = Field(
        sa_column=Column(
            String(50),
            unique=True,
            nullable=False,
            index=True,
            comment="用户名",
        )
    )

    email: str = Field(
        sa_column=Column(
            String(255),
            unique=True,
            nullable=False,
            index=True,
            comment="邮箱",
        )
    )

    password_hash: str = Field(
        sa_column=Column(
            String(255),
            nullable=False,
            comment="密码哈希",
        )
    )

    full_name: Optional[str] = Field(
        default=None,
        sa_column=Column(
            String(100),
            nullable=True,
            comment="真实姓名",
        )
    )

    is_active: bool = Field(
        default=True,
        sa_column=Column(
            Boolean,
            nullable=False,
            server_default="1",
            comment="是否激活",
        )
    )

    is_superuser: bool = Field(
        default=False,
        sa_column=Column(
            Boolean,
            nullable=False,
            server_default="0",
            comment="是否超级管理员",
        )
    )


class UserCreate(SQLModel):
    username: str = Field(max_length=50, min_length=3)
    email: str = Field(max_length=255)
    password_hash: str = Field(max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=100)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)


class UserUpdate(SQLModel):
    username: Optional[str] = Field(default=None, max_length=50, min_length=3)
    email: Optional[str] = Field(default=None, max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = Field(default=None)
    is_superuser: Optional[bool] = Field(default=None)
    password_hash: Optional[str] = Field(default=None, max_length=255)
