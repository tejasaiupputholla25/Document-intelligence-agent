from pathlib import Path
from typing import Optional

import pandas as pd


# ---------------------------------------------------------
# Temporary application state
# ---------------------------------------------------------
# For Phase 6, we keep one structured dataset loaded
# in memory at a time.
#
# Later, when we build a real multi-user application,
# this will be replaced with per-user / per-session storage.
# ---------------------------------------------------------

_current_dataframe: Optional[pd.DataFrame] = None
_current_file_name: Optional[str] = None


SUPPORTED_EXTENSIONS = {
    ".csv",
    ".xlsx",
}


def load_structured_data(
    file_path: str,
) -> dict:
    """
    Load a CSV or XLSX file into memory
    as a Pandas DataFrame.

    Returns basic information about
    the loaded dataset.
    """

    global _current_dataframe
    global _current_file_name

    path = Path(file_path)

    # -----------------------------------------------------
    # Validate file existence
    # -----------------------------------------------------

    if not path.exists():
        raise FileNotFoundError(
            f"Structured data file not found: {path}"
        )

    # -----------------------------------------------------
    # Validate extension
    # -----------------------------------------------------

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            "Unsupported structured data format. "
            "Currently supported formats are CSV and XLSX."
        )

    # -----------------------------------------------------
    # Load data
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
        # Defensive fallback
        raise ValueError(
            f"Unsupported file extension: {extension}"
        )

    # -----------------------------------------------------
    # Validate content
    # -----------------------------------------------------

    if dataframe.empty:
        raise ValueError(
            "The structured data file contains no rows."
        )

    # -----------------------------------------------------
    # Clean column names
    # -----------------------------------------------------
    # Example:
    #
    # " revenue " -> "revenue"
    # -----------------------------------------------------

    dataframe.columns = [
        str(column).strip()
        for column in dataframe.columns
    ]

    # -----------------------------------------------------
    # Duplicate columns can create ambiguous analysis.
    # -----------------------------------------------------

    if dataframe.columns.duplicated().any():

        duplicate_columns = (
            dataframe.columns[
                dataframe.columns.duplicated()
            ]
            .tolist()
        )

        raise ValueError(
            "The dataset contains duplicate column names: "
            f"{duplicate_columns}"
        )

    # -----------------------------------------------------
    # Save current dataset in memory
    # -----------------------------------------------------

    _current_dataframe = dataframe

    _current_file_name = path.name

    # -----------------------------------------------------
    # Return dataset information
    # -----------------------------------------------------

    return {
        "file_name": path.name,

        "rows": int(
            dataframe.shape[0]
        ),

        "columns": int(
            dataframe.shape[1]
        ),

        "column_names":
            dataframe.columns.tolist(),
    }


def get_current_dataframe() -> pd.DataFrame:
    """
    Return the currently loaded Pandas DataFrame.
    """

    if _current_dataframe is None:

        raise RuntimeError(
            "No structured dataset is currently loaded."
        )

    return _current_dataframe


def get_current_file_name() -> str:
    """
    Return the filename of the currently
    loaded structured dataset.
    """

    if _current_file_name is None:

        raise RuntimeError(
            "No structured dataset is currently loaded."
        )

    return _current_file_name


def has_structured_data() -> bool:
    """
    Return True if a structured dataset
    is currently loaded.
    """

    return _current_dataframe is not None