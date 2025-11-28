import re
from dataclasses import dataclass, field
from typing import Optional

from app.core.domain.base_domain import BaseDomain  # 导入重命名后的基类


@dataclass(kw_only=True)
class UserDomain(BaseDomain):  # 继承BaseDomain（替代原BaseEntity）
    """用户领域实体"""
    # 必选属性
    username: str
    email: str
    hashed_password: str

    # 可选属性
    full_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = field(default=True)
    is_superuser: bool = field(default=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        self._validate_username()
        self._validate_email()

    def _validate_username(self) -> None:
        if not re.match(r"^[a-zA-Z0-9_-]{3,20}$", self.username):
            raise ValueError(f"用户名 {self.username} 格式错误")

    def _validate_email(self) -> None:
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                        self.email):
            raise ValueError(f"邮箱 {self.email} 格式错误")

    def set_active(self, is_active: bool) -> None:
        self.is_active = is_active
        self.touch_updated_at()
