from pydantic import BaseModel, Field


# =========================================================
# CHAT
# =========================================================

class ChatRequest(BaseModel):
    """
    JSON body expected by the chat endpoint.
    """

    question: str = Field(
        min_length=1,
        max_length=4000,
    )


class ChatResponse(BaseModel):
    """
    JSON returned by the chat endpoint.
    """

    answer: str


# =========================================================
# HEALTH
# =========================================================

class HealthResponse(BaseModel):

    status: str
    service: str


# =========================================================
# PDF STATUS
# =========================================================

class PDFStatus(BaseModel):

    ready: bool
    file_name: str | None = None
    chunk_count: int = 0
    file_hash: str | None = None


# =========================================================
# DATASET STATUS
# =========================================================

class DatasetStatus(BaseModel):

    ready: bool
    file_name: str | None = None
    rows: int = 0
    columns: int = 0
    column_names: list[str] = []
    file_hash: str | None = None


# =========================================================
# APPLICATION STATUS
# =========================================================

class ApplicationStatus(BaseModel):

    pdf: PDFStatus
    dataset: DatasetStatus