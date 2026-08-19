from pathlib import Path

from typing import (
    Optional,
)

from uuid import UUID

import pandas as pd


from app.db.repositories import (
    get_latest_dataset,
)


# =========================================================
# LEGACY SINGLE-DATASET STATE
# =========================================================
#
# Kept temporarily for backward compatibility.
#
# Session-aware Agent tools do NOT use these globals.
# =========================================================

_current_dataframe: Optional[
    pd.DataFrame
] = None


_current_file_name: Optional[
    str
] = None


SUPPORTED_EXTENSIONS = {
    ".csv",
    ".xlsx",
}


# =========================================================
# INTERNAL FILE READER
# =========================================================

def _read_structured_file(
    file_path: str,
) -> pd.DataFrame:
    """
    Read and validate CSV/XLSX data without
    modifying global state.
    """

    path = Path(
        file_path
    )


    # -----------------------------------------------------
    # FILE EXISTS
    # -----------------------------------------------------

    if not path.exists():

        raise FileNotFoundError(
            f"Structured data file "
            f"not found: {path}"
        )


    # -----------------------------------------------------
    # EXTENSION
    # -----------------------------------------------------

    extension = (
        path.suffix.lower()
    )


    if extension not in (
        SUPPORTED_EXTENSIONS
    ):

        raise ValueError(
            "Unsupported structured-data format. "
            "Supported formats: CSV and XLSX."
        )


    # -----------------------------------------------------
    # READ
    # -----------------------------------------------------

    if extension == ".csv":

        dataframe = (
            pd.read_csv(
                path
            )
        )


    elif extension == ".xlsx":

        dataframe = (
            pd.read_excel(
                path
            )
        )


    else:

        raise ValueError(
            f"Unsupported extension: "
            f"{extension}"
        )


    # -----------------------------------------------------
    # EMPTY DATASET
    # -----------------------------------------------------

    if dataframe.empty:

        raise ValueError(
            "The structured-data file "
            "contains no rows."
        )


    # -----------------------------------------------------
    # CLEAN COLUMN NAMES
    # -----------------------------------------------------

    dataframe.columns = [

        str(column).strip()

        for column
        in dataframe.columns
    ]


    # -----------------------------------------------------
    # DUPLICATE COLUMNS
    # -----------------------------------------------------

    if (
        dataframe.columns
        .duplicated()
        .any()
    ):

        duplicate_columns = (

            dataframe.columns[
                dataframe.columns
                .duplicated()
            ]
            .tolist()
        )


        raise ValueError(
            f"Duplicate columns detected: "
            f"{duplicate_columns}"
        )


    return dataframe


# =========================================================
# LEGACY LOAD
# =========================================================

def load_structured_data(
    file_path: str,
) -> dict:
    """
    Load a dataset into legacy single-process
    global state.

    This remains for compatibility with old code.

    New session-aware Agent tools use
    get_dataframe_for_session().
    """

    global _current_dataframe
    global _current_file_name


    path = Path(
        file_path
    )


    dataframe = (
        _read_structured_file(
            str(path)
        )
    )


    _current_dataframe = (
        dataframe
    )


    _current_file_name = (
        path.name
    )


    return {

        "file_name":
            path.name,

        "rows":
            int(
                dataframe.shape[0]
            ),

        "columns":
            int(
                dataframe.shape[1]
            ),

        "column_names":
            dataframe.columns.tolist(),
    }


# =========================================================
# LEGACY GET CURRENT DATAFRAME
# =========================================================

def get_current_dataframe() -> pd.DataFrame:

    if _current_dataframe is None:

        raise RuntimeError(
            "No structured dataset "
            "is currently loaded."
        )


    return _current_dataframe


# =========================================================
# LEGACY GET CURRENT FILE NAME
# =========================================================

def get_current_file_name() -> str:

    if _current_file_name is None:

        raise RuntimeError(
            "No structured dataset "
            "is currently loaded."
        )


    return _current_file_name


# =========================================================
# LEGACY STATE CHECK
# =========================================================

def has_structured_data() -> bool:

    return (
        _current_dataframe
        is not None
    )


# =========================================================
# LEGACY CLEAR
# =========================================================

def clear_structured_data() -> None:

    global _current_dataframe
    global _current_file_name


    _current_dataframe = None
    _current_file_name = None


# =========================================================
# SESSION-AWARE DATAFRAME LOADER
# =========================================================

def get_dataframe_for_session(
    session_id: str,
) -> tuple[
    pd.DataFrame,
    object,
]:
    """
    Find the latest dataset registered for
    a session in PostgreSQL and load its file.

    Returns:

    dataframe
    DatasetRecord
    """

    if not session_id:

        raise RuntimeError(
            "session_id is required "
            "to load structured data."
        )


    # -----------------------------------------------------
    # VALIDATE UUID
    # -----------------------------------------------------

    try:

        session_uuid = UUID(
            str(session_id)
        )


    except ValueError as error:

        raise RuntimeError(
            "Invalid session identifier."
        ) from error


    # -----------------------------------------------------
    # LOOK UP SESSION DATASET
    # -----------------------------------------------------

    dataset = (
        get_latest_dataset(
            session_uuid
        )
    )


    if dataset is None:

        raise RuntimeError(
            "No structured dataset exists "
            "for this session."
        )


    # -----------------------------------------------------
    # LOAD THAT SESSION'S FILE
    # -----------------------------------------------------

    dataframe = (
        _read_structured_file(
            dataset.stored_path
        )
    )


    return (
        dataframe,
        dataset,
    )