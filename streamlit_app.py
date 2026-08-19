import os

import pandas as pd
import requests
import streamlit as st

from dotenv import load_dotenv


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()


API_BASE_URL = (
    os.getenv(
        "API_BASE_URL",
        "http://127.0.0.1:8000",
    )
    .rstrip("/")
)


# =========================================================
# HTTP SETTINGS
# =========================================================

CONNECT_TIMEOUT = 10

READ_TIMEOUT = 180

REQUEST_TIMEOUT = (
    CONNECT_TIMEOUT,
    READ_TIMEOUT,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title=(
        "Document Intelligence Agent"
    ),
    page_icon="📄",
    layout="wide",
)


# =========================================================
# SESSION STATE
# =========================================================

def initialize_session_state():

    defaults = {

        "messages": [],

        "backend_online":
            False,

        "backend_status": {

            "pdf": {
                "ready": False,
            },

            "dataset": {
                "ready": False,
            },
        },
    }


    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[
                key
            ] = value


initialize_session_state()


# =========================================================
# API ERROR CLASS
# =========================================================

class APIError(Exception):

    pass


# =========================================================
# API HELPER
# =========================================================

def api_request(
    method: str,
    endpoint: str,
    **kwargs,
):

    url = (
        f"{API_BASE_URL}"
        f"{endpoint}"
    )


    try:

        response = (
            requests.request(
                method=method,
                url=url,
                timeout=REQUEST_TIMEOUT,
                **kwargs,
            )
        )


    except requests.exceptions.Timeout:

        raise APIError(
            "The backend request timed out."
        )


    except requests.exceptions.ConnectionError:

        raise APIError(
            "Could not connect to the FastAPI backend. "
            "Make sure it is running on port 8000."
        )


    except requests.exceptions.RequestException as error:

        raise APIError(
            f"Backend request failed: "
            f"{error}"
        )


    # -----------------------------------------------------
    # Handle backend error response
    # -----------------------------------------------------

    if not response.ok:

        try:

            error_body = (
                response.json()
            )

            detail = (
                error_body.get(
                    "detail",
                    response.text,
                )
            )


        except ValueError:

            detail = (
                response.text
                or
                "Unknown backend error."
            )


        raise APIError(
            f"Backend returned "
            f"HTTP {response.status_code}: "
            f"{detail}"
        )


    # -----------------------------------------------------
    # Decode JSON
    # -----------------------------------------------------

    try:

        return response.json()


    except ValueError:

        raise APIError(
            "Backend returned invalid JSON."
        )


# =========================================================
# HEALTH
# =========================================================

def check_backend() -> bool:

    try:

        result = api_request(
            "GET",
            "/health",
        )


        return (
            result.get(
                "status"
            )
            == "ok"
        )


    except APIError:

        return False


# =========================================================
# STATUS
# =========================================================

def refresh_backend_status():

    result = api_request(
        "GET",
        "/api/v1/status",
    )


    st.session_state[
        "backend_status"
    ] = result


# =========================================================
# UPLOAD PDF
# =========================================================

def upload_pdf_to_api(
    uploaded_file,
):

    files = {

        "file": (

            uploaded_file.name,

            uploaded_file.getvalue(),

            uploaded_file.type
            or
            "application/pdf",
        )
    }


    result = api_request(
        "POST",
        "/api/v1/documents/upload",
        files=files,
    )


    refresh_backend_status()


    return result


# =========================================================
# UPLOAD DATASET
# =========================================================

def upload_dataset_to_api(
    uploaded_file,
):

    files = {

        "file": (

            uploaded_file.name,

            uploaded_file.getvalue(),

            uploaded_file.type
            or
            "application/octet-stream",
        )
    }


    result = api_request(
        "POST",
        "/api/v1/datasets/upload",
        files=files,
    )


    refresh_backend_status()


    return result


# =========================================================
# CHAT
# =========================================================

def ask_api(
    question: str,
) -> str:

    result = api_request(

        "POST",

        "/api/v1/chat",

        json={
            "question":
                question
        },
    )


    return result[
        "answer"
    ]


# =========================================================
# PREVIEW
# =========================================================

def get_dataset_preview(
    limit: int = 20,
):

    return api_request(

        "GET",

        "/api/v1/datasets/preview",

        params={
            "limit":
                limit
        },
    )


# =========================================================
# CHECK BACKEND
# =========================================================

st.session_state.backend_online = (
    check_backend()
)


if st.session_state.backend_online:

    try:

        refresh_backend_status()

    except APIError:

        st.session_state.backend_online = (
            False
        )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.title(
        "📁 Files"
    )


    # =====================================================
    # BACKEND STATUS
    # =====================================================

    st.subheader(
        "Backend"
    )


    if st.session_state.backend_online:

        st.success(
            "FastAPI connected"
        )


    else:

        st.error(
            "FastAPI offline"
        )

        st.caption(
            "Start the backend with:"
        )

        st.code(
            "uvicorn app.api.main:app "
            "--reload --port 8000"
        )


    st.divider()


    # =====================================================
    # PDF
    # =====================================================

    st.subheader(
        "PDF Document"
    )


    uploaded_pdf = (
        st.file_uploader(
            "Choose PDF",
            type=[
                "pdf"
            ],
            key="pdf_uploader",
        )
    )


    if uploaded_pdf is not None:

        if st.button(
            "Upload PDF",
            type="primary",
            width="stretch",
            disabled=(
                not st.session_state
                .backend_online
            ),
        ):

            try:

                with st.spinner(
                    "Sending PDF to FastAPI...",
                    show_time=True,
                ):

                    result = (
                        upload_pdf_to_api(
                            uploaded_pdf
                        )
                    )


                st.success(
                    result[
                        "message"
                    ]
                )


            except APIError as error:

                st.error(
                    str(error)
                )


    # -----------------------------------------------------
    # PDF status
    # -----------------------------------------------------

    pdf_status = (
        st.session_state
        .backend_status
        .get(
            "pdf",
            {}
        )
    )


    if pdf_status.get(
        "ready"
    ):

        st.success(
            "PDF ready"
        )

        st.write(
            f"**File:** "
            f"{pdf_status.get('file_name')}"
        )

        st.write(
            f"**Chunks:** "
            f"{pdf_status.get('chunk_count')}"
        )


    else:

        st.info(
            "No PDF loaded."
        )


    st.divider()


    # =====================================================
    # DATASET
    # =====================================================

    st.subheader(
        "Structured Dataset"
    )


    uploaded_dataset = (
        st.file_uploader(
            "Choose CSV or XLSX",
            type=[
                "csv",
                "xlsx",
            ],
            key="dataset_uploader",
        )
    )


    if uploaded_dataset is not None:

        if st.button(
            "Upload Dataset",
            type="primary",
            width="stretch",
            disabled=(
                not st.session_state
                .backend_online
            ),
        ):

            try:

                with st.spinner(
                    "Sending dataset to FastAPI...",
                    show_time=True,
                ):

                    result = (
                        upload_dataset_to_api(
                            uploaded_dataset
                        )
                    )


                st.success(
                    result[
                        "message"
                    ]
                )


            except APIError as error:

                st.error(
                    str(error)
                )


    # -----------------------------------------------------
    # Dataset status
    # -----------------------------------------------------

    dataset_status = (
        st.session_state
        .backend_status
        .get(
            "dataset",
            {}
        )
    )


    if dataset_status.get(
        "ready"
    ):

        st.success(
            "Dataset ready"
        )

        st.write(
            f"**File:** "
            f"{dataset_status.get('file_name')}"
        )

        st.write(
            f"**Rows:** "
            f"{dataset_status.get('rows')}"
        )

        st.write(
            f"**Columns:** "
            f"{dataset_status.get('columns')}"
        )


    else:

        st.info(
            "No dataset loaded."
        )


    st.divider()


    # =====================================================
    # CLEAR CHAT
    # =====================================================

    if st.button(
        "Clear Chat",
        width="stretch",
    ):

        st.session_state.messages = []

        st.rerun()


# =========================================================
# MAIN PAGE
# =========================================================

st.title(
    "📄 Document Intelligence Agent"
)


st.caption(
    "Streamlit frontend + FastAPI backend"
)


# =========================================================
# ARCHITECTURE STATUS
# =========================================================

if st.session_state.backend_online:

    st.success(
        "Frontend connected to FastAPI backend."
    )


else:

    st.error(
        "FastAPI backend is not running."
    )


# =========================================================
# SOURCE STATUS
# =========================================================

pdf_status = (
    st.session_state
    .backend_status
    .get(
        "pdf",
        {}
    )
)


dataset_status = (
    st.session_state
    .backend_status
    .get(
        "dataset",
        {}
    )
)


column_1, column_2 = (
    st.columns(2)
)


with column_1:

    if pdf_status.get(
        "ready"
    ):

        st.success(
            f"PDF: "
            f"{pdf_status.get('file_name')}"
        )


    else:

        st.info(
            "PDF: Not loaded"
        )


with column_2:

    if dataset_status.get(
        "ready"
    ):

        st.success(
            f"Dataset: "
            f"{dataset_status.get('file_name')}"
        )


    else:

        st.info(
            "Dataset: Not loaded"
        )


# =========================================================
# DATASET PREVIEW
# =========================================================

if (
    st.session_state.backend_online
    and
    dataset_status.get(
        "ready"
    )
):

    with st.expander(
        "Preview dataset"
    ):

        try:

            preview = (
                get_dataset_preview(
                    limit=20
                )
            )


            dataframe = pd.DataFrame(
                preview[
                    "rows"
                ]
            )


            st.dataframe(
                dataframe,
                hide_index=True,
                width="stretch",
            )


        except APIError as error:

            st.warning(
                str(error)
            )


# =========================================================
# EXAMPLE QUESTIONS
# =========================================================

with st.expander(
    "Example questions"
):

    st.markdown(
        """
**PDF**

- What skills are mentioned in the PDF?
- How many PDF chunks are indexed?
- What does the document say about machine learning?

**Dataset**

- How many records are in the dataset?
- What columns are available?
- Show the first 5 rows.
- What is average revenue?
- What is total revenue by region?
- Show West region orders.
        """
    )


# =========================================================
# CHAT HISTORY
# =========================================================

for message in (
    st.session_state.messages
):

    with st.chat_message(
        message[
            "role"
        ]
    ):

        st.markdown(
            message[
                "content"
            ]
        )


# =========================================================
# ENABLE CHAT?
# =========================================================

source_ready = (

    pdf_status.get(
        "ready",
        False,
    )

    or

    dataset_status.get(
        "ready",
        False,
    )
)


chat_enabled = (

    st.session_state
    .backend_online

    and

    source_ready
)


# =========================================================
# CHAT INPUT
# =========================================================

prompt = st.chat_input(

    (
        "Ask about your PDF or dataset..."
        if chat_enabled
        else
        "Start FastAPI and upload a file first..."
    ),

    disabled=(
        not chat_enabled
    ),
)


# =========================================================
# HANDLE CHAT
# =========================================================

if prompt:

    # -----------------------------------------------------
    # User message
    # -----------------------------------------------------

    st.session_state.messages.append(
        {
            "role":
                "user",

            "content":
                prompt,
        }
    )


    with st.chat_message(
        "user"
    ):

        st.markdown(
            prompt
        )


    # -----------------------------------------------------
    # Assistant
    # -----------------------------------------------------

    with st.chat_message(
        "assistant"
    ):

        try:

            with st.spinner(
                "Agent is thinking...",
                show_time=True,
            ):

                answer = (
                    ask_api(
                        prompt
                    )
                )


            st.markdown(
                answer
            )


        except APIError as error:

            answer = (
                f"API error: {error}"
            )


            st.error(
                answer
            )


    # -----------------------------------------------------
    # Store assistant answer
    # -----------------------------------------------------

    st.session_state.messages.append(
        {
            "role":
                "assistant",

            "content":
                answer,
        }
    )