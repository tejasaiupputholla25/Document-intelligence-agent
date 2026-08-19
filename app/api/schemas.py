from datetime import datetime

from typing import Any

from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
)


# =========================================================
# HEALTH
# =========================================================

class HealthResponse(
    BaseModel
):

    status: str

    service: str


# =========================================================
# SESSION
# =========================================================

class SessionCreateResponse(
    BaseModel
):

    session_id: UUID

    created_at: datetime


# =========================================================
# DOCUMENT
# =========================================================

class DocumentStatus(
    BaseModel
):

    ready: bool

    document_id: UUID | None = None

    file_name: str | None = None

    chunk_count: int = 0

    created_at: datetime | None = None


class DocumentUploadResponse(
    BaseModel
):

    message: str

    document: DocumentStatus


# =========================================================
# DATASET
# =========================================================

class DatasetStatus(
    BaseModel
):

    ready: bool

    dataset_id: UUID | None = None

    file_name: str | None = None

    rows: int = 0

    columns: int = 0

    column_names: list[str] = Field(
        default_factory=list
    )

    created_at: datetime | None = None


class DatasetUploadResponse(
    BaseModel
):

    message: str

    dataset: DatasetStatus


class DatasetPreviewResponse(
    BaseModel
):

    file_name: str

    returned_rows: int

    rows: list[
        dict[
            str,
            Any,
        ]
    ] = Field(
        default_factory=list
    )


# =========================================================
# SESSION STATUS
# =========================================================

class SessionStatusResponse(
    BaseModel
):

    session_id: UUID

    document: DocumentStatus

    dataset: DatasetStatus


# =========================================================
# CHAT
# =========================================================

class ChatRequest(
    BaseModel
):

    question: str = Field(
        min_length=1,
        max_length=4000,
    )


class ChatResponse(
    BaseModel
):

    answer: str


class ChatMessageResponse(
    BaseModel
):

    role: str

    content: str

    created_at: datetime


class ChatHistoryResponse(
    BaseModel
):

    session_id: UUID

    messages: list[
        ChatMessageResponse
    ] = Field(
        default_factory=list
    )


class DeleteChatResponse(
    BaseModel
):

    message: str