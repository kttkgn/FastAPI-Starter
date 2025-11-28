from typing import Optional, List, Sequence

from app.adapters.db.models.user import UserCreate, UserUpdate
from app.adapters.db.repositories.user_repositories import UserRepository
from app.core.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
    InvalidUserUpdateError
)
from app.core.domain.user_domain import UserDomain


class UserService:
    """用户应用服务层 - 极简版（依赖仓库层返回合法领域实体）"""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def create_user(self, user_create: UserCreate) -> UserDomain:
        """创建用户（仅做唯一性校验，仓库层返回合法领域实体）"""
        # 1. 核心业务规则：用户名/邮箱唯一性
        if await self.user_repo.exists_by_username(user_create.username):
            raise UserAlreadyExistsError(f"用户名 {user_create.username} 已存在")
        if await self.user_repo.exists_by_email(user_create.email):
            raise UserAlreadyExistsError(f"邮箱 {user_create.email} 已存在")

        # 2. 仓库层直接返回合法的UserDomain，无需任何手动赋值/重新实例化
        return await self.user_repo.create_user(user_create)

    async def get_user_by_id(self, user_id: int) -> UserDomain:
        """根据ID查询用户"""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"ID为 {user_id} 的用户不存在")
        return user

    async def get_user_by_username(self, username: str) -> UserDomain:
        """根据用户名查询用户"""
        user = await self.user_repo.get_by_username(username)
        if not user:
            raise UserNotFoundError(f"用户名 {username} 不存在")
        return user

    async def get_user_by_email(self, email: str) -> UserDomain:
        """根据邮箱查询用户"""
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise UserNotFoundError(f"邮箱 {email} 对应的用户不存在")
        return user

    async def batch_get_users_by_ids(self, user_ids: List[int]) -> Sequence[UserDomain]:
        """批量查询用户"""
        if not user_ids:
            return []
        return await self.user_repo.batch_get_by_ids(user_ids)

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        is_superuser: Optional[bool] = None
    ) -> Sequence[UserDomain]:
        """条件查询用户列表"""
        return await self.user_repo.list_filtered(
            skip=skip,
            limit=limit,
            is_active=is_active,
            is_superuser=is_superuser
        )

    async def update_user(self, user_id: int, user_update: UserUpdate) -> UserDomain:
        """更新用户信息（仅做唯一性校验，仓库层返回合法领域实体）"""
        # 1. 校验用户是否存在
        existing_user = await self.get_user_by_id(user_id)

        # 2. 核心业务规则：更新的用户名/邮箱需唯一
        if user_update.username and user_update.username != existing_user.username:
            if await self.user_repo.exists_by_username(user_update.username):
                raise UserAlreadyExistsError(f"用户名 {user_update.username} 已存在")
        if user_update.email and user_update.email != existing_user.email:
            if await self.user_repo.exists_by_email(user_update.email):
                raise UserAlreadyExistsError(f"邮箱 {user_update.email} 已存在")

        # 3. 仓库层直接返回更新后的合法UserDomain
        updated_user = await self.user_repo.update_user(user_id, user_update)
        if not updated_user:
            raise InvalidUserUpdateError(f"更新用户 {user_id} 失败")
        return updated_user

    async def activate_user(self, user_id: int) -> UserDomain:
        """激活用户（调用领域实体方法+仓库层保存）"""
        # 1. 查询合法的领域实体
        user = await self.get_user_by_id(user_id)

        # 2. 调用领域实体的业务方法（保证状态变更的合法性）
        user.set_active(True)

        # 3. 仓库层保存并返回更新后的合法领域实体
        return await self.user_repo.save_domain_entity(user)

    async def deactivate_user(self, user_id: int) -> UserDomain:
        """停用用户（调用领域实体方法+仓库层保存）"""
        # 1. 查询合法的领域实体
        user = await self.get_user_by_id(user_id)

        # 2. 调用领域实体的业务方法
        user.set_active(False)

        # 3. 仓库层保存并返回更新后的合法领域实体
        return await self.user_repo.save_domain_entity(user)

    async def check_user_exists(self, user_id: int) -> bool:
        """检查用户是否存在"""
        return await self.user_repo.exists_by_id(user_id)
