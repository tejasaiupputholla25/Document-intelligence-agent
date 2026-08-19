# =========================================================
# TEMPORARY APPLICATION STATE
# =========================================================
#
# Phase 8 still uses in-memory state.
#
# Phase 9 will replace this approach with persistent
# database/session/document identifiers.
# =========================================================


runtime_state = {

    "pdf": {

        "ready": False,

        "file_name": None,

        "file_hash": None,

        "chunk_count": 0,
    },

    "dataset": {

        "ready": False,

        "file_name": None,

        "file_hash": None,

        "rows": 0,

        "columns": 0,

        "column_names": [],
    },
}


# =========================================================
# PDF RESET
# =========================================================

def reset_pdf_state() -> None:

    runtime_state["pdf"] = {

        "ready": False,

        "file_name": None,

        "file_hash": None,

        "chunk_count": 0,
    }


# =========================================================
# DATASET RESET
# =========================================================

def reset_dataset_state() -> None:

    runtime_state["dataset"] = {

        "ready": False,

        "file_name": None,

        "file_hash": None,

        "rows": 0,

        "columns": 0,

        "column_names": [],
    }