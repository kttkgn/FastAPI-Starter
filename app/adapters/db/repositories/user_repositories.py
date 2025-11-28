from typing import Optional, List, Sequence

from sqlmodel.ext.asyncio.session import AsyncSession

from app.adapters.db.models.user import User, UserCreate, UserUpdate
from app.adapters.db.repositories.base_repositories import BaseRepository
from core.domain.user_domain import UserDomain


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    def _get_model(self) -> type[User]:
        return User

    # ========== 新增：数据库模型 ↔ 领域实体 转换方法 ==========
    @staticmethod
    def _to_domain_entity(db_user: User) -> UserDomain:
        """将数据库模型转换为领域实体"""
        return UserDomain(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            hashed_password=db_user.hashed_password,
            full_name=db_user.full_name,
            phone=db_user.phone,
            is_active=db_user.is_active,
            is_superuser=db_user.is_superuser,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at,
        )

    @staticmethod
    def _from_domain_entity(domain_user: UserDomain) -> User:

        return User(
            id=domain_user.id,
            username=domain_user.username,
            email=domain_user.email,
            hashed_password=domain_user.hashed_password,
            full_name=domain_user.full_name,
            phone=domain_user.phone,
            is_active=domain_user.is_active,
            is_superuser=domain_user.is_superuser,
            created_at=domain_user.created_at,
            updated_at=domain_user.updated_at,
        )

    # ========== 改造原有方法：返回领域实体 ==========
    async def get_by_id(self, user_id: int) -> Optional[UserDomain]:
        """重写：根据ID查询，返回领域实体"""
        db_user = await super().get_by_id(user_id)
        return self._to_domain_entity(db_user) if db_user else None

    async def get_by_username(self, username: str) -> Optional[UserDomain]:
        """改造：返回领域实体"""
        cond = self._eq("username", username)
        users = await self.list_all(conditions=[cond], limit=1)
        return self._to_domain_entity(users[0]) if users else None

    async def get_by_email(self, email: str) -> Optional[UserDomain]:
        """改造：返回领域实体"""
        cond = self._eq("email", email)
        users = await self.list_all(conditions=[cond], limit=1)
        return self._to_domain_entity(users[0]) if users else None

    async def batch_get_by_ids(self, ids: List[int]) -> Sequence[UserDomain]:
        """改造：批量查询返回领域实体列表"""
        if not ids:
            return []
        cond = self._get_column("id").in_(ids)
        db_users = await self.list_all(conditions=[cond])
        return [self._to_domain_entity(user) for user in db_users]

    async def list_filtered(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        is_superuser: Optional[bool] = None,
    ) -> Sequence[UserDomain]:
        """改造：条件查询返回领域实体列表"""
        conditions = []
        if is_active is not None:
            conditions.append(self._eq("is_active", is_active))
        if is_superuser is not None:
            conditions.append(self._eq("is_superuser", is_superuser))
        db_users = await self.list_all(skip=skip, limit=limit, conditions=conditions)
        return [self._to_domain_entity(user) for user in db_users]

    # ========== 新增：基于领域实体的CRUD ==========
    async def save_domain_entity(self, domain_user: UserDomain) -> UserDomain:
        """保存领域实体到数据库"""
        db_user = self._from_domain_entity(domain_user)
        if db_user.id:
            # 更新已有用户
            self.db.add(db_user)
            await self.db.commit()
            await self.db.refresh(db_user)
        else:
            # 创建新用户
            self.db.add(db_user)
            await self.db.commit()
            await self.db.refresh(db_user)
            # 同步数据库生成的ID/时间戳到领域实体
            domain_user.id = db_user.id
            domain_user.created_at = db_user.created_at
            domain_user.updated_at = db_user.updated_at
        return self._to_domain_entity(db_user)

    # ========== 保留原有方法（兼容历史调用） ==========
    async def exists_by_id(self, user_id: int) -> bool:
        return await self.exists([self._eq("id", user_id)])

    async def exists_by_username(self, username: str) -> bool:
        return await self.exists([self._eq("username", username)])

    async def exists_by_email(self, email: str) -> bool:
        return await self.exists([self._eq("email", email)])

    async def create_user(self, data: UserCreate) -> UserDomain:
        """改造：创建用户后返回领域实体"""
        db_user = await self.create(data)
        return self._to_domain_entity(db_user)

    async def update_user(self, user_id: int, data: UserUpdate) -> Optional[UserDomain]:
        """改造：更新后返回领域实体"""
        db_user = await self.update(user_id, data)
        return self._to_domain_entity(db_user) if db_user else None

    async def deactivate(self, user_id: int) -> Optional[UserDomain]:
        """改造：停用后返回领域实体"""
        db_user = await self.update(user_id, UserUpdate(is_active=False))
        return self._to_domain_entity(db_user) if db_user else None

    async def activate(self, user_id: int) -> Optional[UserDomain]:
        """改造：激活后返回领域实体"""
        db_user = await self.update(user_id, UserUpdate(is_active=True))
        return self._to_domain_entity(db_user) if db_user else None
