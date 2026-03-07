from sqlalchemy import Column, Enum, LargeBinary, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base
import enum
import uuid

Base = declarative_base()


class StatusEnum(str, enum.Enum):
    pending = "pending"
    ready = "ready"
    error = "error"


status_enum = Enum(
    StatusEnum,
    name="statusenum",
    create_type=False  
)


class Chat(Base):
    __tablename__ = "chat"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, default="New Conversation")
    messages = Column(JSONB, nullable=False, default=list)


class Document(Base):
    __tablename__ = "document"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False, default="untitled")
    content = Column(LargeBinary, nullable=False)

    status = Column(
        status_enum,
        default=StatusEnum.pending,
        nullable=False
    )