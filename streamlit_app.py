from pathlib import Path
import hashlib

import streamlit as st


from app.document_processing import (
    process_pdf,
)

from app.semantic_search import (
    index_documents,
    clear_document_store,
)

from app.structured_data import (
    load_structured_data,
    get_current_dataframe,
    clear_structured_data,
)

from app.agent import (
    run_document_agent,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Document Intelligence Agent",
    page_icon="📄",
    layout="wide",
)


# =========================================================
# UPLOAD DIRECTORY
# =========================================================

UPLOAD_DIRECTORY = Path(
    "uploads"
)

UPLOAD_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)


# =========================================================
# DEVELOPMENT FILE SIZE LIMIT
# =========================================================

MAX_FILE_SIZE_MB = 20

MAX_FILE_SIZE_BYTES = (
    MAX_FILE_SIZE_MB
    * 1024
    * 1024
)


# =========================================================
# SESSION STATE
# =========================================================

def initialize_session_state():

    defaults = {

        # Chat
        "messages": [],

        # PDF
        "pdf_ready": False,
        "pdf_name": None,
        "pdf_hash": None,
        "pdf_chunk_count": 0,

        # Structured data
        "data_ready": False,
        "data_name": None,
        "data_hash": None,
        "data_rows": 0,
        "data_columns": 0,
        "data_column_names": [],
    }

    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[
                key
            ] = value


initialize_session_state()


# =========================================================
# FILE HASH
# =========================================================

def calculate_file_hash(
    file_bytes: bytes,
) -> str:

    return hashlib.sha256(
        file_bytes
    ).hexdigest()


# =========================================================
# SAVE UPLOAD
# =========================================================

def save_uploaded_file(
    uploaded_file,
) -> tuple[Path, str]:

    file_bytes = (
        uploaded_file.getvalue()
    )

    # -----------------------------------------------------
    # Validate size
    # -----------------------------------------------------

    if (
        len(file_bytes)
        > MAX_FILE_SIZE_BYTES
    ):

        raise ValueError(
            f"File is larger than "
            f"{MAX_FILE_SIZE_MB} MB."
        )

    # -----------------------------------------------------
    # Sanitize filename
    # -----------------------------------------------------

    safe_file_name = Path(
        uploaded_file.name
    ).name

    # -----------------------------------------------------
    # File hash
    # -----------------------------------------------------

    file_hash = (
        calculate_file_hash(
            file_bytes
        )
    )

    # -----------------------------------------------------
    # Save with unique prefix
    # -----------------------------------------------------

    saved_file_name = (
        f"{file_hash[:12]}_"
        f"{safe_file_name}"
    )

    saved_path = (
        UPLOAD_DIRECTORY
        / saved_file_name
    )

    saved_path.write_bytes(
        file_bytes
    )

    return (
        saved_path,
        file_hash,
    )


# =========================================================
# PROCESS PDF
# =========================================================

def process_uploaded_pdf(
    uploaded_file,
):

    saved_path, file_hash = (
        save_uploaded_file(
            uploaded_file
        )
    )

    # -----------------------------------------------------
    # Already processed
    # -----------------------------------------------------

    if (
        st.session_state.pdf_ready
        and
        st.session_state.pdf_hash
        == file_hash
    ):

        return

    # -----------------------------------------------------
    # Remove previously indexed PDF
    # -----------------------------------------------------

    clear_document_store()

    # -----------------------------------------------------
    # Phase 2
    # PDF -> chunks
    # -----------------------------------------------------

    chunks = process_pdf(
        str(saved_path)
    )

    if not chunks:

        raise ValueError(
            "No readable text was extracted "
            "from the uploaded PDF."
        )

    # -----------------------------------------------------
    # Phase 3
    # chunks -> embeddings -> vector store
    # -----------------------------------------------------

    index_documents(
        chunks
    )

    # -----------------------------------------------------
    # Save UI state
    # -----------------------------------------------------

    st.session_state.pdf_ready = True

    st.session_state.pdf_name = (
        uploaded_file.name
    )

    st.session_state.pdf_hash = (
        file_hash
    )

    st.session_state.pdf_chunk_count = (
        len(chunks)
    )


# =========================================================
# PROCESS CSV / XLSX
# =========================================================

def process_uploaded_dataset(
    uploaded_file,
):

    saved_path, file_hash = (
        save_uploaded_file(
            uploaded_file
        )
    )

    # -----------------------------------------------------
    # Already loaded
    # -----------------------------------------------------

    if (
        st.session_state.data_ready
        and
        st.session_state.data_hash
        == file_hash
    ):

        return

    # -----------------------------------------------------
    # Reset previous dataset
    # -----------------------------------------------------

    clear_structured_data()

    # -----------------------------------------------------
    # Phase 6
    # CSV/XLSX -> Pandas
    # -----------------------------------------------------

    data_info = (
        load_structured_data(
            str(saved_path)
        )
    )

    # -----------------------------------------------------
    # Save UI state
    # -----------------------------------------------------

    st.session_state.data_ready = True

    st.session_state.data_name = (
        uploaded_file.name
    )

    st.session_state.data_hash = (
        file_hash
    )

    st.session_state.data_rows = (
        data_info[
            "rows"
        ]
    )

    st.session_state.data_columns = (
        data_info[
            "columns"
        ]
    )

    st.session_state.data_column_names = (
        data_info[
            "column_names"
        ]
    )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.title(
        "📁 Files"
    )

    st.caption(
        "Upload a PDF and/or CSV/XLSX file."
    )


    # =====================================================
    # PDF SECTION
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
            "Process PDF",
            type="primary",
            width="stretch",
        ):

            try:

                with st.spinner(
                    "Processing PDF...",
                    show_time=True,
                ):

                    process_uploaded_pdf(
                        uploaded_pdf
                    )

                st.success(
                    "PDF processed successfully."
                )

            except Exception as error:

                st.error(
                    f"PDF processing failed: "
                    f"{error}"
                )


    # -----------------------------------------------------
    # PDF STATUS
    # -----------------------------------------------------

    if st.session_state.pdf_ready:

        st.success(
            "PDF ready"
        )

        st.write(
            f"**File:** "
            f"{st.session_state.pdf_name}"
        )

        st.write(
            f"**Chunks:** "
            f"{st.session_state.pdf_chunk_count}"
        )

    else:

        st.info(
            "No PDF processed."
        )


    st.divider()


    # =====================================================
    # DATASET SECTION
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
            "Load Dataset",
            type="primary",
            width="stretch",
        ):

            try:

                with st.spinner(
                    "Loading dataset...",
                    show_time=True,
                ):

                    process_uploaded_dataset(
                        uploaded_dataset
                    )

                st.success(
                    "Dataset loaded successfully."
                )

            except Exception as error:

                st.error(
                    f"Dataset loading failed: "
                    f"{error}"
                )


    # -----------------------------------------------------
    # DATASET STATUS
    # -----------------------------------------------------

    if st.session_state.data_ready:

        st.success(
            "Dataset ready"
        )

        st.write(
            f"**File:** "
            f"{st.session_state.data_name}"
        )

        st.write(
            f"**Rows:** "
            f"{st.session_state.data_rows}"
        )

        st.write(
            f"**Columns:** "
            f"{st.session_state.data_columns}"
        )

    else:

        st.info(
            "No structured dataset loaded."
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
    "Ask questions about PDF documents "
    "and analyze CSV/XLSX datasets."
)


# =========================================================
# SOURCE STATUS
# =========================================================

pdf_column, data_column = (
    st.columns(2)
)


with pdf_column:

    if st.session_state.pdf_ready:

        st.success(
            f"PDF: "
            f"{st.session_state.pdf_name}"
        )

    else:

        st.info(
            "PDF: Not loaded"
        )


with data_column:

    if st.session_state.data_ready:

        st.success(
            f"Dataset: "
            f"{st.session_state.data_name}"
        )

    else:

        st.info(
            "Dataset: Not loaded"
        )


# =========================================================
# DATASET PREVIEW
# =========================================================

if st.session_state.data_ready:

    with st.expander(
        "Preview dataset"
    ):

        try:

            dataframe = (
                get_current_dataframe()
            )

            st.dataframe(
                dataframe.head(20),
                width="stretch",
                hide_index=True,
            )

        except Exception as error:

            st.warning(
                f"Dataset preview unavailable: "
                f"{error}"
            )


# =========================================================
# SAMPLE QUESTIONS
# =========================================================

with st.expander(
    "Example questions"
):

    st.markdown(
        """
**PDF**

- What skills are mentioned in the PDF?
- What experience is described?
- What does the document say about machine learning?
- How many PDF chunks are indexed?

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
# DISPLAY CHAT HISTORY
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
# CHAT READY?
# =========================================================

source_ready = (
    st.session_state.pdf_ready
    or
    st.session_state.data_ready
)


# =========================================================
# CHAT INPUT
# =========================================================

prompt = st.chat_input(

    (
        "Ask about your PDF or dataset..."
        if source_ready
        else
        "Upload and process a file first..."
    ),

    disabled=
        not source_ready,
)


# =========================================================
# HANDLE QUESTION
# =========================================================

if prompt:

    # -----------------------------------------------------
    # Save user message
    # -----------------------------------------------------

    st.session_state.messages.append(
        {
            "role":
                "user",

            "content":
                prompt,
        }
    )


    # -----------------------------------------------------
    # Display user message
    # -----------------------------------------------------

    with st.chat_message(
        "user"
    ):

        st.markdown(
            prompt
        )


    # -----------------------------------------------------
    # Agent
    # -----------------------------------------------------

    with st.chat_message(
        "assistant"
    ):

        try:

            with st.spinner(
                "Thinking...",
                show_time=True,
            ):

                answer = (
                    run_document_agent(
                        prompt
                    )
                )

            st.markdown(
                answer
            )

        except Exception as error:

            answer = (
                "An error occurred while "
                "processing the request.\n\n"
                f"`{error}`"
            )

            st.error(
                answer
            )


    # -----------------------------------------------------
    # Save assistant response
    # -----------------------------------------------------

    st.session_state.messages.append(
        {
            "role":
                "assistant",

            "content":
                answer,
        }
    )