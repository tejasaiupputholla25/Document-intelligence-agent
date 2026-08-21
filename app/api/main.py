import json
import logging

from contextlib import (
    asynccontextmanager,
)

from uuid import (
    UUID,
    uuid4,
)


from fastapi import (
    FastAPI,
    File,
    HTTPException,
    Query,
    UploadFile,
)


from app.agent import (
    run_document_agent,
)


from app.document_processing import (
    process_pdf,
)


from app.semantic_search import (
    delete_document_chunks,
    index_documents,
)


from app.structured_data import (
    get_dataframe_for_session,
    load_structured_data,
)


from app.db.database import (
    create_database_tables,
)


from app.db.models import (
    DatasetRecord,
    DocumentRecord,
)


from app.db.repositories import (
    create_dataset,
    create_document,
    create_session,
    delete_chat_messages,
    get_chat_messages,
    get_latest_dataset,
    get_latest_document,
    get_ready_documents,
    get_session,
    mark_datasets_replaced,
    mark_documents_replaced,
    save_chat_message,
)


from app.api.file_utils import (
    save_upload,
)


from app.api.schemas import (
    ChatHistoryResponse,
    ChatRequest,
    ChatResponse,
    DatasetPreviewResponse,
    DatasetStatus,
    DatasetUploadResponse,
    DeleteChatResponse,
    DocumentStatus,
    DocumentUploadResponse,
    HealthResponse,
    SessionCreateResponse,
    SessionStatusResponse,
)


# =========================================================
# LOGGING
# =========================================================

logger = logging.getLogger(
    __name__
)


# =========================================================
# APPLICATION LIFESPAN
# =========================================================

@asynccontextmanager
async def lifespan(
    app: FastAPI,
):

    create_database_tables()

    yield


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(

    title=
        "Document Intelligence API",

    description=(
        "Persistent session-aware backend "
        "for PDF intelligence and "
        "structured-data analysis."
    ),

    version=
        "2.1.0",

    lifespan=
        lifespan,
)


# =========================================================
# SESSION VALIDATION
# =========================================================

def require_session(
    session_id: UUID,
):

    session = (
        get_session(
            session_id
        )
    )


    if session is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "Application session "
                "was not found."
            ),
        )


    return session


# =========================================================
# DOCUMENT STATUS
# =========================================================

def build_document_status(
    session_id: UUID,
) -> DocumentStatus:

    document = (
        get_latest_document(
            session_id
        )
    )


    if document is None:

        return DocumentStatus(
            ready=False
        )


    return DocumentStatus(

        ready=
            True,

        document_id=
            document.id,

        file_name=
            document.file_name,

        chunk_count=
            document.chunk_count,

        created_at=
            document.created_at,
    )


# =========================================================
# DATASET STATUS
# =========================================================

def build_dataset_status(
    session_id: UUID,
) -> DatasetStatus:

    dataset = (
        get_latest_dataset(
            session_id
        )
    )


    if dataset is None:

        return DatasetStatus(
            ready=False
        )


    return DatasetStatus(

        ready=
            True,

        dataset_id=
            dataset.id,

        file_name=
            dataset.file_name,

        rows=
            dataset.row_count,

        columns=
            dataset.column_count,

        column_names=
            dataset.column_names,

        created_at=
            dataset.created_at,
    )


# =========================================================
# HEALTH
# =========================================================

@app.get(
    "/health",

    response_model=
        HealthResponse,

    tags=[
        "System"
    ],
)
def health_check():

    return HealthResponse(

        status=
            "ok",

        service=
            "document-intelligence-api",
    )


# =========================================================
# CREATE SESSION
# =========================================================

@app.post(
    "/api/v1/sessions",

    response_model=
        SessionCreateResponse,

    status_code=
        201,

    tags=[
        "Sessions"
    ],
)
def create_application_session():

    session = (
        create_session()
    )


    return SessionCreateResponse(

        session_id=
            session.id,

        created_at=
            session.created_at,
    )


# =========================================================
# SESSION STATUS
# =========================================================

@app.get(
    "/api/v1/sessions/{session_id}/status",

    response_model=
        SessionStatusResponse,

    tags=[
        "Sessions"
    ],
)
def session_status(
    session_id: UUID,
):

    require_session(
        session_id
    )


    return SessionStatusResponse(

        session_id=
            session_id,

        document=
            build_document_status(
                session_id
            ),

        dataset=
            build_dataset_status(
                session_id
            ),
    )


# =========================================================
# PDF UPLOAD
# =========================================================

@app.post(
    "/api/v1/sessions/{session_id}/documents/upload",

    response_model=
        DocumentUploadResponse,

    tags=[
        "Documents"
    ],
)
def upload_pdf(

    session_id: UUID,

    file: UploadFile = File(...),
):

    require_session(
        session_id
    )


    new_document_id = None


    try:

        (
            saved_path,
            file_hash,
            safe_file_name,
        ) = save_upload(

            upload_file=
                file,

            allowed_extensions={
                ".pdf"
            },

            session_id=
                str(
                    session_id
                ),
        )


        # -------------------------------------------------
        # DUPLICATE CURRENT DOCUMENT
        # -------------------------------------------------

        current_document = (
            get_latest_document(
                session_id
            )
        )


        if (
            current_document is not None

            and

            current_document.sha256
            == file_hash
        ):

            return DocumentUploadResponse(

                message=(
                    "PDF is already processed "
                    "for this session."
                ),

                document=
                    build_document_status(
                        session_id
                    ),
            )


        # -------------------------------------------------
        # PROCESS PDF
        # -------------------------------------------------

        chunks = (
            process_pdf(
                str(
                    saved_path
                )
            )
        )


        if not chunks:

            raise HTTPException(
                status_code=400,
                detail=(
                    "No readable text could "
                    "be extracted from the PDF."
                ),
            )


        new_document_id = (
            uuid4()
        )


        previous_documents = (
            get_ready_documents(
                session_id
            )
        )


        # -------------------------------------------------
        # INDEX NEW VECTORS
        # -------------------------------------------------

        index_documents(

            documents=
                chunks,

            session_id=
                str(
                    session_id
                ),

            document_id=
                str(
                    new_document_id
                ),

            source_file=
                safe_file_name,
        )


        # -------------------------------------------------
        # METADATA
        # -------------------------------------------------

        document_record = (
            DocumentRecord(

                id=
                    new_document_id,

                session_id=
                    session_id,

                file_name=
                    safe_file_name,

                stored_path=
                    str(
                        saved_path
                    ),

                sha256=
                    file_hash,

                chunk_count=
                    len(
                        chunks
                    ),

                status=
                    "ready",
            )
        )


        create_document(
            document_record
        )


        mark_documents_replaced(

            session_id=
                session_id,

            keep_document_id=
                new_document_id,
        )


        # -------------------------------------------------
        # DELETE ONLY PREVIOUS DOCUMENT VECTORS
        # -------------------------------------------------

        for old_document in (
            previous_documents
        ):

            delete_document_chunks(

                session_id=
                    str(
                        session_id
                    ),

                document_id=
                    str(
                        old_document.id
                    ),
            )


        return DocumentUploadResponse(

            message=
                "PDF processed successfully.",

            document=
                build_document_status(
                    session_id
                ),
        )


    except HTTPException:

        raise


    except Exception:

        # -------------------------------------------------
        # FULL DETAILS GO TO SERVER LOG ONLY
        # -------------------------------------------------

        logger.exception(
            "PDF processing failed "
            "for session %s",
            session_id,
        )


        # -------------------------------------------------
        # CLEAN POSSIBLE ORPHAN VECTORS
        # -------------------------------------------------

        if new_document_id is not None:

            try:

                delete_document_chunks(

                    session_id=
                        str(
                            session_id
                        ),

                    document_id=
                        str(
                            new_document_id
                        ),
                )


            except Exception:

                logger.exception(
                    (
                        "Failed to remove orphan "
                        "vectors for document %s "
                        "in session %s"
                    ),
                    new_document_id,
                    session_id,
                )


        # -------------------------------------------------
        # GENERIC CLIENT RESPONSE
        # -------------------------------------------------

        raise HTTPException(
            status_code=500,
            detail=(
                "PDF processing failed."
            ),
        )


    finally:

        file.file.close()


# =========================================================
# DATASET UPLOAD
# =========================================================

@app.post(
    "/api/v1/sessions/{session_id}/datasets/upload",

    response_model=
        DatasetUploadResponse,

    tags=[
        "Datasets"
    ],
)
def upload_dataset(

    session_id: UUID,

    file: UploadFile = File(...),
):

    require_session(
        session_id
    )


    try:

        (
            saved_path,
            file_hash,
            safe_file_name,
        ) = save_upload(

            upload_file=
                file,

            allowed_extensions={
                ".csv",
                ".xlsx",
            },

            session_id=
                str(
                    session_id
                ),
        )


        current_dataset = (
            get_latest_dataset(
                session_id
            )
        )


        if (
            current_dataset is not None

            and

            current_dataset.sha256
            == file_hash
        ):

            return DatasetUploadResponse(

                message=(
                    "Dataset is already loaded "
                    "for this session."
                ),

                dataset=
                    build_dataset_status(
                        session_id
                    ),
            )


        data_info = (
            load_structured_data(
                str(
                    saved_path
                )
            )
        )


        dataset_id = (
            uuid4()
        )


        dataset_record = (
            DatasetRecord(

                id=
                    dataset_id,

                session_id=
                    session_id,

                file_name=
                    safe_file_name,

                stored_path=
                    str(
                        saved_path
                    ),

                sha256=
                    file_hash,

                row_count=
                    data_info[
                        "rows"
                    ],

                column_count=
                    data_info[
                        "columns"
                    ],

                column_names=
                    data_info[
                        "column_names"
                    ],

                status=
                    "ready",
            )
        )


        create_dataset(
            dataset_record
        )


        mark_datasets_replaced(

            session_id=
                session_id,

            keep_dataset_id=
                dataset_id,
        )


        return DatasetUploadResponse(

            message=(
                "Dataset loaded successfully."
            ),

            dataset=
                build_dataset_status(
                    session_id
                ),
        )


    except HTTPException:

        raise


    except Exception:

        logger.exception(
            "Dataset processing failed "
            "for session %s",
            session_id,
        )


        raise HTTPException(
            status_code=500,
            detail=(
                "Dataset processing failed."
            ),
        )


    finally:

        file.file.close()


# =========================================================
# DATASET PREVIEW
# =========================================================

@app.get(
    "/api/v1/sessions/{session_id}/datasets/preview",

    response_model=
        DatasetPreviewResponse,

    tags=[
        "Datasets"
    ],
)
def dataset_preview(

    session_id: UUID,

    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
):

    require_session(
        session_id
    )


    try:

        dataframe, dataset = (
            get_dataframe_for_session(
                str(
                    session_id
                )
            )
        )


        preview_dataframe = (
            dataframe.head(
                limit
            )
        )


        rows = json.loads(

            preview_dataframe.to_json(
                orient="records",
                date_format="iso",
            )
        )


        return DatasetPreviewResponse(

            file_name=
                dataset.file_name,

            returned_rows=
                len(
                    rows
                ),

            rows=
                rows,
        )


    except RuntimeError as error:

        # -------------------------------------------------
        # EXPECTED BUSINESS/APPLICATION ERROR
        # -------------------------------------------------

        raise HTTPException(
            status_code=409,
            detail=str(
                error
            ),
        )


    except Exception:

        logger.exception(
            "Dataset preview failed "
            "for session %s",
            session_id,
        )


        raise HTTPException(
            status_code=500,
            detail=(
                "Dataset preview failed."
            ),
        )


# =========================================================
# CHAT
# =========================================================

@app.post(
    "/api/v1/sessions/{session_id}/chat",

    response_model=
        ChatResponse,

    tags=[
        "Chat"
    ],
)
def chat(

    session_id: UUID,

    request: ChatRequest,
):

    require_session(
        session_id
    )


    document = (
        get_latest_document(
            session_id
        )
    )


    dataset = (
        get_latest_dataset(
            session_id
        )
    )


    if (
        document is None

        and

        dataset is None
    ):

        raise HTTPException(
            status_code=409,
            detail=(
                "Upload a PDF or dataset "
                "before asking questions."
            ),
        )


    question = (
        request.question.strip()
    )


    if not question:

        raise HTTPException(
            status_code=400,
            detail=(
                "Question cannot be empty."
            ),
        )


    try:

        save_chat_message(

            session_id=
                session_id,

            role=
                "user",

            content=
                question,
        )


        answer = (
            run_document_agent(

                question=
                    question,

                session_id=
                    str(
                        session_id
                    ),
            )
        )


        save_chat_message(

            session_id=
                session_id,

            role=
                "assistant",

            content=
                answer,
        )


        return ChatResponse(
            answer=
                answer
        )


    except HTTPException:

        raise


    except Exception:

        logger.exception(
            "Agent request failed "
            "for session %s",
            session_id,
        )


        raise HTTPException(
            status_code=500,
            detail=(
                "Agent request failed."
            ),
        )


# =========================================================
# CHAT HISTORY
# =========================================================

@app.get(
    "/api/v1/sessions/{session_id}/chat",

    response_model=
        ChatHistoryResponse,

    tags=[
        "Chat"
    ],
)
def chat_history(
    session_id: UUID,
):

    require_session(
        session_id
    )


    messages = (
        get_chat_messages(
            session_id
        )
    )


    return ChatHistoryResponse(

        session_id=
            session_id,

        messages=[

            {
                "role":
                    message.role,

                "content":
                    message.content,

                "created_at":
                    message.created_at,
            }

            for message
            in messages
        ],
    )


# =========================================================
# CLEAR CHAT
# =========================================================

@app.delete(
    "/api/v1/sessions/{session_id}/chat",

    response_model=
        DeleteChatResponse,

    tags=[
        "Chat"
    ],
)
def clear_chat_history(
    session_id: UUID,
):

    require_session(
        session_id
    )


    delete_chat_messages(
        session_id
    )


    return DeleteChatResponse(

        message=(
            "Chat history cleared."
        )
    )