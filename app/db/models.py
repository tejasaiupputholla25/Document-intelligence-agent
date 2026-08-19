from datetime import datetime

from uuid import (
    UUID,
    uuid4,
)

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Uuid,
    func,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.database import (
    Base,
)


# =========================================================
# APPLICATION SESSION
# =========================================================

class SessionRecord(
    Base
):

    __tablename__ = (
        "app_sessions"
    )


    id: Mapped[UUID] = mapped_column(

        Uuid,

        primary_key=True,

        default=uuid4,
    )


    created_at: Mapped[datetime] = mapped_column(

        DateTime(
            timezone=True
        ),

        server_default=func.now(),

        nullable=False,
    )


# =========================================================
# DOCUMENT METADATA
# =========================================================

class DocumentRecord(
    Base
):

    __tablename__ = (
        "documents"
    )


    id: Mapped[UUID] = mapped_column(

        Uuid,

        primary_key=True,

        default=uuid4,
    )


    session_id: Mapped[UUID] = mapped_column(

        Uuid,

        ForeignKey(
            "app_sessions.id",
            ondelete="CASCADE",
        ),

        nullable=False,

        index=True,
    )


    file_name: Mapped[str] = mapped_column(

        String(500),

        nullable=False,
    )


    stored_path: Mapped[str] = mapped_column(

        Text,

        nullable=False,
    )


    sha256: Mapped[str] = mapped_column(

        String(64),

        nullable=False,

        index=True,
    )


    chunk_count: Mapped[int] = mapped_column(

        Integer,

        default=0,

        nullable=False,
    )


    status: Mapped[str] = mapped_column(

        String(50),

        default="ready",

        nullable=False,
    )


    created_at: Mapped[datetime] = mapped_column(

        DateTime(
            timezone=True
        ),

        server_default=func.now(),

        nullable=False,
    )


# =========================================================
# DATASET METADATA
# =========================================================

class DatasetRecord(
    Base
):

    __tablename__ = (
        "datasets"
    )


    id: Mapped[UUID] = mapped_column(

        Uuid,

        primary_key=True,

        default=uuid4,
    )


    session_id: Mapped[UUID] = mapped_column(

        Uuid,

        ForeignKey(
            "app_sessions.id",
            ondelete="CASCADE",
        ),

        nullable=False,

        index=True,
    )


    file_name: Mapped[str] = mapped_column(

        String(500),

        nullable=False,
    )


    stored_path: Mapped[str] = mapped_column(

        Text,

        nullable=False,
    )


    sha256: Mapped[str] = mapped_column(

        String(64),

        nullable=False,

        index=True,
    )


    row_count: Mapped[int] = mapped_column(

        Integer,

        nullable=False,
    )


    column_count: Mapped[int] = mapped_column(

        Integer,

        nullable=False,
    )


    column_names: Mapped[list] = mapped_column(

        JSON,

        nullable=False,
    )


    status: Mapped[str] = mapped_column(

        String(50),

        default="ready",

        nullable=False,
    )


    created_at: Mapped[datetime] = mapped_column(

        DateTime(
            timezone=True
        ),

        server_default=func.now(),

        nullable=False,
    )


# =========================================================
# CHAT MESSAGE
# =========================================================

class ChatMessageRecord(
    Base
):

    __tablename__ = (
        "chat_messages"
    )


    id: Mapped[UUID] = mapped_column(

        Uuid,

        primary_key=True,

        default=uuid4,
    )


    session_id: Mapped[UUID] = mapped_column(

        Uuid,

        ForeignKey(
            "app_sessions.id",
            ondelete="CASCADE",
        ),

        nullable=False,

        index=True,
    )


    role: Mapped[str] = mapped_column(

        String(30),

        nullable=False,
    )


    content: Mapped[str] = mapped_column(

        Text,

        nullable=False,
    )


    created_at: Mapped[datetime] = mapped_column(

        DateTime(
            timezone=True
        ),

        server_default=func.now(),

        nullable=False,
    )