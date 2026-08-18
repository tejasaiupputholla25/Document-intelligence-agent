from pathlib import Path
from typing import Optional

import pandas as pd


# =========================================================
# CURRENT STRUCTURED DATA STATE
# =========================================================
#
# Phase 6 supports one structured dataset at a time.
#
# This is appropriate for our local learning application.
# Later we will replace this global state with
# user/session-specific storage.
# =========================================================

_current_dataframe: Optional[pd.DataFrame] = None
_current_file_name: Optional[str] = None


SUPPORTED_EXTENSIONS = {
    ".csv",
    ".xlsx",
}


# =========================================================
# LOAD DATA
# =========================================================

def load_structured_data(
    file_path: str,
) -> dict:
    """
    Load a CSV or XLSX file into memory.

    Returns basic metadata describing
    the loaded dataset.
    """

    global _current_dataframe
    global _current_file_name

    path = Path(file_path)

    # -----------------------------------------------------
    # File existence
    # -----------------------------------------------------

    if not path.exists():
        raise FileNotFoundError(
            f"Structured data file not found: {path}"
        )

    # -----------------------------------------------------
    # File extension
    # -----------------------------------------------------

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            "Unsupported structured-data format. "
            "Supported formats: CSV and XLSX."
        )

    # -----------------------------------------------------
    # Read file
    # -----------------------------------------------------

    if extension == ".csv":

        dataframe = pd.read_csv(
            path
        )

    elif extension == ".xlsx":

        dataframe = pd.read_excel(
            path
        )

    else:

        raise ValueError(
            f"Unsupported extension: {extension}"
        )

    # -----------------------------------------------------
    # Validate data
    # -----------------------------------------------------

    if dataframe.empty:
        raise ValueError(
            "The structured-data file contains no rows."
        )

    # -----------------------------------------------------
    # Clean column names
    # -----------------------------------------------------

    dataframe.columns = [
        str(column).strip()
        for column in dataframe.columns
    ]

    # -----------------------------------------------------
    # Validate duplicate columns
    # -----------------------------------------------------

    if dataframe.columns.duplicated().any():

        duplicate_columns = (
            dataframe.columns[
                dataframe.columns.duplicated()
            ]
            .tolist()
        )

        raise ValueError(
            "Duplicate columns detected: "
            f"{duplicate_columns}"
        )

    # -----------------------------------------------------
    # Store current dataset
    # -----------------------------------------------------

    _current_dataframe = dataframe
    _current_file_name = path.name

    return {
        "file_name":
            path.name,

        "rows":
            int(dataframe.shape[0]),

        "columns":
            int(dataframe.shape[1]),

        "column_names":
            dataframe.columns.tolist(),
    }


# =========================================================
# GET DATAFRAME
# =========================================================

def get_current_dataframe() -> pd.DataFrame:
    """
    Return the currently loaded structured dataset.
    """

    if _current_dataframe is None:

        raise RuntimeError(
            "No structured dataset is currently loaded."
        )

    return _current_dataframe


# =========================================================
# GET FILE NAME
# =========================================================

def get_current_file_name() -> str:
    """
    Return the name of the currently loaded dataset.
    """

    if _current_file_name is None:

        raise RuntimeError(
            "No structured dataset is currently loaded."
        )

    return _current_file_name


# =========================================================
# CHECK STATE
# =========================================================

def has_structured_data() -> bool:
    """
    Return True if a structured dataset
    is currently loaded.
    """

    return _current_dataframe is not None


# =========================================================
# CLEAR DATA
# =========================================================

def clear_structured_data() -> None:
    """
    Remove the current structured dataset
    from application memory.
    """

    global _current_dataframe
    global _current_file_name

    _current_dataframe = None
    _current_file_name = None