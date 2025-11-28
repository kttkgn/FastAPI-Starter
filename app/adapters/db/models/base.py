from datetime import datetime
from typing import Any
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func


class BaseModel(SQLModel):
    __abstract__ = True

    created_at: datetime = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        )
    )

    updated_at: datetime = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            onupdate=func.now(),
            nullable=True,
        )
    )

    async def update(self, **kwargs: Any) -> None:
        allowed_fields = [
            field_name for field_name in self.model_fields.keys()
            if field_name not in ["id", "created_at"]
        ]

        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(self, key, value)

        self.updated_at = datetime.now()
