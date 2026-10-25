from sqlalchemy import String
from sqlalchemy.sql import func
from sqlalchemy.orm import as_declarative, declared_attr, mapped_column, Mapped
from sqlalchemy.ext.asyncio import AsyncAttrs
from typing import Optional
from pydantic import BaseModel, TypeAdapter
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON, TypeDecorator, VARCHAR
from typing_extensions import Annotated
from datetime import datetime
import json

str_60 = Annotated[str, 60]

str_30 = Annotated[str, 30]

str_100 = Annotated[str, 100]

str_500 = Annotated[str, 500]

required_30 = Annotated[str, mapped_column(String(30), nullable=False, index=True)]

required_100 = Annotated[str, mapped_column(String(100), nullable=False, index=True)]

required_600 = Annotated[str, mapped_column(String(600), nullable=False, index=True)]

required_60 = Annotated[str, mapped_column(String(60), nullable=False, index=True)]

bool_col = Annotated[bool, mapped_column(default=False)]

deferred_500 = Annotated[str, mapped_column(String(500), nullable=False, deferred=True)]


timestamp = Annotated[
    datetime,
    mapped_column(nullable=False, server_default=func.CURRENT_TIMESTAMP()),
]

str_pk_60 = Annotated[
    str,
    mapped_column(String(60), primary_key=True, index=True),
]


@as_declarative()
class Base(AsyncAttrs):
    __name__: str
    # Generate __tablename__ automatically

    @declared_attr.directive
    def __tablename__(cls) -> Optional[str]:
        return cls.__name__.lower()


class Audit(Base):
    id: Mapped[str_pk_60]
    created_at: Mapped[timestamp] = mapped_column(server_default=func.now())
    modified_at: Mapped[datetime | None] = mapped_column(
        default=None,
        nullable=True,
    )
    modified_by: Mapped[str_60 | None] = mapped_column(
        default=None,
        nullable=True,
    )
    created_by: Mapped[required_60]
    type: Mapped[str]

    __mapper_args__ = {
        "polymorphic_identity": "audit",
        "polymorphic_on": "type",
    }

    def __repr__(self):
        return f"{self.__class__.__name__}({self.created_at!r})"


class PydanticColumn(TypeDecorator):
    """
    PydanticColumn type.
    * for custom column type implementation check https://docs.sqlalchemy.org/en/20/core/custom_types.html
    * Uses sqlalchemy.dialects.postgresql.JSONB if dialects == postgresql else generic sqlalchemy.types.JSON
    * Save:
        - Accepts the pydantic model and converts it to a dict on save.
        - SQLAlchemy engine JSON-encodes the dict to a string.
    * Load:
        - Pulls the string from the database.
        - SQLAlchemy engine JSON-decodes the string to a dict.
        - Uses the dict to create a pydantic model.
    """

    impl = JSON
    cache_ok = True

    def __init__(self, pydantic_type):
        super().__init__()
        if not issubclass(pydantic_type, BaseModel):
            raise ValueError("Column Type Should be Pydantic Class")
        self.pydantic_type = pydantic_type

    def load_dialect_impl(self, dialect):
        # Use JSONB for PostgreSQL and JSON for other databases.
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        # return value.dict() if value else None   # pydantic <2.0.0
        return value.model_dump(by_alias=True) if value else None

    def process_result_value(self, value, dialect):
        # return parse_obj_as(self.pydantic_type, value) if value else None # pydantic < 2.0.0
        return TypeAdapter(self.pydantic_type).validate_python(value)


class JSONEncodedDict(TypeDecorator):
    "Represents an immutable structure as a json-encoded string."

    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value
