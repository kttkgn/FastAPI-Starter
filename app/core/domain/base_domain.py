import datetime
from dataclasses import dataclass, field
from typing import Optional

@dataclass(kw_only=True)  # 关键：开启关键字参数模式
class BaseDomain:
    """
    领域层基础类（替代原BaseEntity）
    所有领域实体的通用基类，封装ID、审计时间等通用属性和方法
    """
    id: Optional[int] = None
    created_at: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(datetime.UTC))
    updated_at: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(datetime.UTC))

    def __post_init__(self) -> None:
        """初始化后置方法，供子类重写"""
        pass

    def touch_updated_at(self) -> None:
        """更新updated_at为当前UTC时间（时区感知）"""
        self.updated_at = datetime.datetime.now(datetime.UTC)
