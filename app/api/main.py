import json

from fastapi import (
    FastAPI,
    HTTPException,
    Query,
    UploadFile,
)


from app.document_processing import (
    process_pdf,
)


from app.semantic_search import (
    index_documents,
    clear_document_store,
)


from app.structured_data import (
    load_structured_data,
    clear_structured_data,
    get_current_dataframe,
)


from app.agent import (
    run_document_agent,
)


from app.api.file_utils import (
    save_upload,
)


from app.api.schemas import (
    ApplicationStatus,
    ChatRequest,
    ChatResponse,
    HealthResponse,
)


from app.api.state import (
    runtime_state,
    reset_dataset_state,
    reset_pdf_state,
)


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(

    title=(
        "Document Intelligence API"
    ),

    description=(
        "Backend API for document question answering "
        "and structured-data analysis."
    ),

    version="1.0.0",
)


# =========================================================
# HEALTH
# =========================================================

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=[
        "System"
    ],
)
def health_check():

    return {
        "status":
            "ok",

        "service":
            "document-intelligence-api",
    }


# =========================================================
# STATUS
# =========================================================

@app.get(
    "/api/v1/status",
    response_model=ApplicationStatus,
    tags=[
        "System"
    ],
)
def application_status():

    return runtime_state


# =========================================================
# PDF UPLOAD
# =========================================================

@app.post(
    "/api/v1/documents/upload",
    tags=[
        "Documents"
    ],
)
def upload_pdf(
    file: UploadFile,
):

    try:

        # -------------------------------------------------
        # Save upload
        # -------------------------------------------------

        saved_path, file_hash = (
            save_upload(
                upload_file=file,
                allowed_extensions={
                    ".pdf"
                },
            )
        )


        # -------------------------------------------------
        # Same file already indexed
        # -------------------------------------------------

        if (
            runtime_state["pdf"]["ready"]
            and
            runtime_state["pdf"]["file_hash"]
            == file_hash
        ):

            return {
                "message":
                    "PDF is already processed.",

                "pdf":
                    runtime_state[
                        "pdf"
                    ],
            }


        # -------------------------------------------------
        # Clear previous PDF
        # -------------------------------------------------

        clear_document_store()

        reset_pdf_state()


        # -------------------------------------------------
        # Phase 2:
        # PDF -> chunks
        # -------------------------------------------------

        chunks = process_pdf(
            str(
                saved_path
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


        # -------------------------------------------------
        # Phase 3:
        # chunks -> vectors
        # -------------------------------------------------

        index_documents(
            chunks
        )


        # -------------------------------------------------
        # Update state
        # -------------------------------------------------

        runtime_state["pdf"] = {

            "ready":
                True,

            "file_name":
                file.filename,

            "file_hash":
                file_hash,

            "chunk_count":
                len(chunks),
        }


        return {
            "message":
                "PDF processed successfully.",

            "pdf":
                runtime_state[
                    "pdf"
                ],
        }


    except HTTPException:

        raise


    except Exception as error:

        reset_pdf_state()

        raise HTTPException(
            status_code=500,
            detail=(
                f"PDF processing failed: "
                f"{error}"
            ),
        )


    finally:

        file.file.close()


# =========================================================
# DATASET UPLOAD
# =========================================================

@app.post(
    "/api/v1/datasets/upload",
    tags=[
        "Datasets"
    ],
)
def upload_dataset(
    file: UploadFile,
):

    try:

        # -------------------------------------------------
        # Save upload
        # -------------------------------------------------

        saved_path, file_hash = (
            save_upload(
                upload_file=file,
                allowed_extensions={
                    ".csv",
                    ".xlsx",
                },
            )
        )


        # -------------------------------------------------
        # Same dataset
        # -------------------------------------------------

        if (
            runtime_state[
                "dataset"
            ][
                "ready"
            ]
            and
            runtime_state[
                "dataset"
            ][
                "file_hash"
            ]
            == file_hash
        ):

            return {
                "message":
                    "Dataset is already loaded.",

                "dataset":
                    runtime_state[
                        "dataset"
                    ],
            }


        # -------------------------------------------------
        # Clear previous dataset
        # -------------------------------------------------

        clear_structured_data()

        reset_dataset_state()


        # -------------------------------------------------
        # Phase 6:
        # CSV/XLSX -> DataFrame
        # -------------------------------------------------

        data_info = (
            load_structured_data(
                str(
                    saved_path
                )
            )
        )


        # -------------------------------------------------
        # Update state
        # -------------------------------------------------

        runtime_state[
            "dataset"
        ] = {

            "ready":
                True,

            "file_name":
                file.filename,

            "file_hash":
                file_hash,

            "rows":
                data_info[
                    "rows"
                ],

            "columns":
                data_info[
                    "columns"
                ],

            "column_names":
                data_info[
                    "column_names"
                ],
        }


        return {
            "message":
                "Dataset loaded successfully.",

            "dataset":
                runtime_state[
                    "dataset"
                ],
        }


    except HTTPException:

        raise


    except Exception as error:

        reset_dataset_state()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Dataset loading failed: "
                f"{error}"
            ),
        )


    finally:

        file.file.close()


# =========================================================
# DATASET PREVIEW
# =========================================================

@app.get(
    "/api/v1/datasets/preview",
    tags=[
        "Datasets"
    ],
)
def dataset_preview(

    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
):

    # -----------------------------------------------------
    # Dataset must exist
    # -----------------------------------------------------

    if not runtime_state[
        "dataset"
    ][
        "ready"
    ]:

        raise HTTPException(
            status_code=409,
            detail=(
                "No structured dataset "
                "is currently loaded."
            ),
        )


    try:

        dataframe = (
            get_current_dataframe()
        )


        preview_dataframe = (
            dataframe.head(
                limit
            )
        )


        # -------------------------------------------------
        # Convert Pandas values to JSON-safe records
        # -------------------------------------------------

        rows = json.loads(

            preview_dataframe.to_json(
                orient="records",
                date_format="iso",
            )
        )


        return {
            "file_name":
                runtime_state[
                    "dataset"
                ][
                    "file_name"
                ],

            "returned_rows":
                len(rows),

            "rows":
                rows,
        }


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Dataset preview failed: "
                f"{error}"
            ),
        )


# =========================================================
# CHAT
# =========================================================

@app.post(
    "/api/v1/chat",
    response_model=ChatResponse,
    tags=[
        "Chat"
    ],
)
def chat(
    request: ChatRequest,
):

    # -----------------------------------------------------
    # At least one information source
    # must be available.
    # -----------------------------------------------------

    if not (
        runtime_state["pdf"]["ready"]
        or
        runtime_state["dataset"]["ready"]
    ):

        raise HTTPException(
            status_code=409,
            detail=(
                "Upload a PDF or dataset "
                "before asking questions."
            ),
        )


    question = (
        request
        .question
        .strip()
    )


    try:

        answer = (
            run_document_agent(
                question
            )
        )


        return ChatResponse(
            answer=answer
        )


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Agent request failed: "
                f"{error}"
            ),
        )