import os

import pandas as pd

import requests

import streamlit as st

from dotenv import (
    load_dotenv,
)


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


REQUEST_TIMEOUT = (
    10,
    180,
)


# =========================================================
# PAGE
# =========================================================

st.set_page_config(

    page_title=
        "Document Intelligence Agent",

    page_icon=
        "📄",

    layout=
        "wide",
)


# =========================================================
# INITIAL SESSION STATE
# =========================================================

def initialize_session_state():

    defaults = {

        "session_id":
            None,

        "messages":
            [],

        "backend_online":
            False,

        "backend_status": {

            "document": {
                "ready": False
            },

            "dataset": {
                "ready": False
            },
        },
    }


    for key, value in (
        defaults.items()
    ):

        if key not in (
            st.session_state
        ):

            st.session_state[
                key
            ] = value


initialize_session_state()


# =========================================================
# API ERROR
# =========================================================

class APIError(
    Exception
):

    pass


# =========================================================
# GENERIC API REQUEST
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

                method=
                    method,

                url=
                    url,

                timeout=
                    REQUEST_TIMEOUT,

                **kwargs,
            )
        )


    except requests.exceptions.Timeout:

        raise APIError(
            "Backend request timed out."
        )


    except requests.exceptions.ConnectionError:

        raise APIError(
            "Could not connect to FastAPI. "
            "Make sure the backend is running."
        )


    except requests.exceptions.RequestException as error:

        raise APIError(
            f"Backend request failed: "
            f"{error}"
        )


    if not response.ok:

        try:

            body = (
                response.json()
            )


            detail = (
                body.get(
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
            f"HTTP "
            f"{response.status_code}: "
            f"{detail}"
        )


    if (
        response.status_code
        == 204
    ):

        return None


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

        result = (
            api_request(
                "GET",
                "/health",
            )
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
# CREATE SESSION
# =========================================================

def create_backend_session() -> str:

    result = (
        api_request(
            "POST",
            "/api/v1/sessions",
        )
    )


    return str(
        result[
            "session_id"
        ]
    )


# =========================================================
# STATUS
# =========================================================

def get_session_status(
    session_id: str,
):

    return api_request(

        "GET",

        (
            f"/api/v1/sessions/"
            f"{session_id}/status"
        ),
    )


# =========================================================
# CHAT HISTORY
# =========================================================

def get_chat_history(
    session_id: str,
):

    result = (
        api_request(

            "GET",

            (
                f"/api/v1/sessions/"
                f"{session_id}/chat"
            ),
        )
    )


    return result[
        "messages"
    ]


def clear_chat_history(
    session_id: str,
):

    return api_request(

        "DELETE",

        (
            f"/api/v1/sessions/"
            f"{session_id}/chat"
        ),
    )


# =========================================================
# REFRESH STATUS
# =========================================================

def refresh_backend_status():

    session_id = (
        st.session_state
        .session_id
    )


    if not session_id:

        return


    st.session_state[
        "backend_status"
    ] = get_session_status(
        session_id
    )


# =========================================================
# REFRESH CHAT
# =========================================================

def refresh_chat_history():

    session_id = (
        st.session_state
        .session_id
    )


    if not session_id:

        st.session_state.messages = []

        return


    messages = (
        get_chat_history(
            session_id
        )
    )


    st.session_state.messages = [

        {
            "role":
                message[
                    "role"
                ],

            "content":
                message[
                    "content"
                ],
        }

        for message
        in messages
    ]


# =========================================================
# RESTORE OR CREATE APPLICATION SESSION
# =========================================================

def ensure_application_session():

    state_session = (
        st.session_state
        .get(
            "session_id"
        )
    )


    query_session = (
        st.query_params
        .get(
            "session"
        )
    )


    # -----------------------------------------------------
    # URL SESSION TAKES PRIORITY
    #
    # Important when user pastes an older
    # persistent workspace URL.
    # -----------------------------------------------------

    if (
        query_session

        and

        query_session
        != state_session
    ):

        try:

            get_session_status(
                query_session
            )


            st.session_state.session_id = (
                query_session
            )


            return


        except APIError:

            st.query_params.clear()


    # -----------------------------------------------------
    # EXISTING STREAMLIT SESSION
    # -----------------------------------------------------

    state_session = (
        st.session_state
        .get(
            "session_id"
        )
    )


    if state_session:

        try:

            get_session_status(
                state_session
            )


            st.query_params[
                "session"
            ] = state_session


            return


        except APIError:

            st.session_state.session_id = None


    # -----------------------------------------------------
    # VALID URL SESSION
    # -----------------------------------------------------

    query_session = (
        st.query_params
        .get(
            "session"
        )
    )


    if query_session:

        try:

            get_session_status(
                query_session
            )


            st.session_state.session_id = (
                query_session
            )


            return


        except APIError:

            st.query_params.clear()


    # -----------------------------------------------------
    # CREATE BRAND-NEW SESSION
    # -----------------------------------------------------

    new_session = (
        create_backend_session()
    )


    st.session_state.session_id = (
        new_session
    )


    st.query_params[
        "session"
    ] = new_session


# =========================================================
# PDF UPLOAD
# =========================================================

def upload_pdf_to_api(
    uploaded_file,
):

    session_id = (
        st.session_state
        .session_id
    )


    files = {

        "file": (

            uploaded_file.name,

            uploaded_file.getvalue(),

            uploaded_file.type
            or
            "application/pdf",
        )
    }


    result = (
        api_request(

            "POST",

            (
                f"/api/v1/sessions/"
                f"{session_id}"
                f"/documents/upload"
            ),

            files=
                files,
        )
    )


    refresh_backend_status()


    return result


# =========================================================
# DATASET UPLOAD
# =========================================================

def upload_dataset_to_api(
    uploaded_file,
):

    session_id = (
        st.session_state
        .session_id
    )


    files = {

        "file": (

            uploaded_file.name,

            uploaded_file.getvalue(),

            uploaded_file.type
            or
            "application/octet-stream",
        )
    }


    result = (
        api_request(

            "POST",

            (
                f"/api/v1/sessions/"
                f"{session_id}"
                f"/datasets/upload"
            ),

            files=
                files,
        )
    )


    refresh_backend_status()


    return result


# =========================================================
# DATASET PREVIEW
# =========================================================

def get_dataset_preview(
    limit: int = 20,
):

    session_id = (
        st.session_state
        .session_id
    )


    return api_request(

        "GET",

        (
            f"/api/v1/sessions/"
            f"{session_id}"
            f"/datasets/preview"
        ),

        params={
            "limit":
                limit
        },
    )


# =========================================================
# ASK AGENT
# =========================================================

def ask_api(
    question: str,
) -> str:

    session_id = (
        st.session_state
        .session_id
    )


    result = (
        api_request(

            "POST",

            (
                f"/api/v1/sessions/"
                f"{session_id}"
                f"/chat"
            ),

            json={
                "question":
                    question
            },
        )
    )


    return result[
        "answer"
    ]


# =========================================================
# BACKEND CONNECTION
# =========================================================

st.session_state.backend_online = (
    check_backend()
)


if (
    st.session_state
    .backend_online
):

    try:

        ensure_application_session()

        refresh_backend_status()

        refresh_chat_history()


    except APIError:

        st.session_state.backend_online = False


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.title(
        "📁 Workspace"
    )


    st.subheader(
        "Backend"
    )


    if (
        st.session_state
        .backend_online
    ):

        st.success(
            "FastAPI connected"
        )


    else:

        st.error(
            "FastAPI offline"
        )


    # -----------------------------------------------------
    # SESSION
    # -----------------------------------------------------

    if (
        st.session_state
        .session_id
    ):

        st.caption(
            "Application session"
        )


        st.code(
            st.session_state
            .session_id
        )


    if st.button(
        "New Session",
        disabled=(
            not st.session_state
            .backend_online
        ),
    ):

        try:

            new_session = (
                create_backend_session()
            )


            st.session_state.session_id = (
                new_session
            )


            st.session_state.messages = []


            st.query_params[
                "session"
            ] = new_session


            refresh_backend_status()


            st.rerun()


        except APIError as error:

            st.error(
                str(error)
            )


    st.divider()


    # -----------------------------------------------------
    # PDF
    # -----------------------------------------------------

    st.subheader(
        "PDF Document"
    )


    uploaded_pdf = (
        st.file_uploader(

            "Choose PDF",

            type=[
                "pdf"
            ],

            key=
                "pdf_uploader",

            disabled=(
                not st.session_state
                .backend_online
            ),
        )
    )


    if uploaded_pdf is not None:

        if st.button(
            "Upload PDF",
            type="primary",
        ):

            try:

                with st.spinner(
                    "Processing PDF..."
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


    document_status = (
        st.session_state
        .backend_status
        .get(
            "document",
            {},
        )
    )


    if document_status.get(
        "ready"
    ):

        st.success(
            "PDF ready"
        )


        st.write(
            f"**File:** "
            f"{document_status.get('file_name')}"
        )


        st.write(
            f"**Chunks:** "
            f"{document_status.get('chunk_count')}"
        )


    else:

        st.info(
            "No PDF in this session."
        )


    st.divider()


    # -----------------------------------------------------
    # DATASET
    # -----------------------------------------------------

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

            key=
                "dataset_uploader",

            disabled=(
                not st.session_state
                .backend_online
            ),
        )
    )


    if uploaded_dataset is not None:

        if st.button(
            "Upload Dataset",
            type="primary",
        ):

            try:

                with st.spinner(
                    "Loading dataset..."
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


    dataset_status = (
        st.session_state
        .backend_status
        .get(
            "dataset",
            {},
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
            "No dataset in this session."
        )


    st.divider()


    # -----------------------------------------------------
    # CLEAR CHAT
    # -----------------------------------------------------

    if st.button(
        "Clear Chat",

        disabled=(
            not st.session_state
            .backend_online
        ),
    ):

        try:

            clear_chat_history(
                st.session_state
                .session_id
            )


            st.session_state.messages = []


            st.rerun()


        except APIError as error:

            st.error(
                str(error)
            )


# =========================================================
# MAIN PAGE
# =========================================================

st.title(
    "📄 Document Intelligence Agent"
)


st.caption(
    "Persistent session-aware "
    "Streamlit + FastAPI + PostgreSQL + pgvector"
)


# =========================================================
# CONNECTION
# =========================================================

if (
    st.session_state
    .backend_online
):

    st.success(
        "Connected to persistent backend session."
    )


else:

    st.error(
        "FastAPI backend is offline."
    )


# =========================================================
# RESOURCE STATUS
# =========================================================

document_status = (
    st.session_state
    .backend_status
    .get(
        "document",
        {},
    )
)


dataset_status = (
    st.session_state
    .backend_status
    .get(
        "dataset",
        {},
    )
)


column_1, column_2 = (
    st.columns(2)
)


with column_1:

    if document_status.get(
        "ready"
    ):

        st.success(
            f"PDF: "
            f"{document_status.get('file_name')}"
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
    st.session_state
    .backend_online

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


            dataframe = (
                pd.DataFrame(
                    preview[
                        "rows"
                    ]
                )
            )


            st.dataframe(
                dataframe,
                hide_index=True,
            )


        except APIError as error:

            st.warning(
                str(error)
            )


# =========================================================
# EXAMPLES
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
# CHAT AVAILABILITY
# =========================================================

source_ready = (

    document_status.get(
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

    bool(
        st.session_state
        .session_id
    )

    and

    source_ready
)


# =========================================================
# CHAT INPUT
# =========================================================

prompt = (
    st.chat_input(

        (
            "Ask about your PDF or dataset..."

            if chat_enabled

            else

            "Upload a PDF or dataset first..."
        ),

        disabled=(
            not chat_enabled
        ),
    )
)


# =========================================================
# HANDLE CHAT
# =========================================================

if prompt:

    with st.chat_message(
        "user"
    ):

        st.markdown(
            prompt
        )


    with st.chat_message(
        "assistant"
    ):

        try:

            with st.spinner(
                "Agent is thinking..."
            ):

                answer = (
                    ask_api(
                        prompt
                    )
                )


            st.markdown(
                answer
            )


            # PostgreSQL is source of truth.

            refresh_chat_history()


        except APIError as error:

            st.error(
                f"API error: {error}"
            )