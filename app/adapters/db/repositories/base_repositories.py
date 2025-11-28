from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Type, Any, Sequence
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import func, ColumnElement, Row, RowMapping

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=SQLModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=SQLModel)


class BaseRepository(ABC, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.model: Type[ModelType] = self._get_model()
        self.pk_field: str = self._get_pk_field()

    @abstractmethod
    def _get_model(self) -> Type[ModelType]:
        raise NotImplementedError

    @staticmethod
    def _get_pk_field() -> str:
        return "id"

    async def get_by_id(self, pk: int | str) -> Optional[ModelType]:
        return await self.db.get(self.model, pk)

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        conditions: List[ColumnElement[bool]] | None = None
    ) -> Sequence[Row[Any] | RowMapping | Any]:
        stmt = select(self.model).offset(skip).limit(limit)
        if conditions:
            for cond in conditions:
                stmt = stmt.where(cond)
        result = await self.db.exec(stmt)
        return result.all()

    async def count(self, conditions: List[ColumnElement[bool]] | None = None) -> int:
        pk_column = getattr(self.model, self.pk_field)
        stmt = select(func.count(pk_column))
        if conditions:
            for cond in conditions:
                stmt = stmt.where(cond)
        result = await self.db.exec(stmt)
        return result.scalar()

    async def exists(self, conditions: List[ColumnElement[bool]]) -> bool:
        return await self.count(conditions) > 0

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        db_obj = self.model(**obj_in.model_dump())
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, pk: int | str, obj_in: UpdateSchemaType) -> Optional[
        ModelType]:
        db_obj = await self.get_by_id(pk)
        if not db_obj:
            return None

        for key, value in obj_in.model_dump(exclude_unset=True).items():
            if key not in [self.pk_field, "created_at"] and value is not None:
                setattr(db_obj, key, value)

        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, pk: int | str) -> bool:
        db_obj = await self.get_by_id(pk)
        if not db_obj:
            return False
        await self.db.delete(db_obj)
        await self.db.flush()
        return True

    def _get_column(self, column_name: str) -> ColumnElement:
        return getattr(self.model, column_name)

    def _eq(self, column_name: str, value: Any) -> ColumnElement[bool]:
        return self._get_column(column_name).is_(value)
