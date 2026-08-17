from typing import (
    Annotated,
    Literal,
    Optional,
)

import pandas as pd

from haystack.tools import tool

from app.structured_data import (
    get_current_dataframe,
    get_current_file_name,
)


# ---------------------------------------------------------
# Helper function
# ---------------------------------------------------------

def _records_from_dataframe(
    dataframe: pd.DataFrame,
) -> list[dict]:
    """
    Convert a Pandas DataFrame into
    JSON-friendly Python dictionaries.

    Missing values are converted to None.
    """

    safe_dataframe = dataframe.astype(
        object
    ).where(
        pd.notna(dataframe),
        None,
    )

    return safe_dataframe.to_dict(
        orient="records"
    )


# =========================================================
# TOOL 1
# GET DATASET INFORMATION
# =========================================================

@tool
def get_data_info() -> dict:
    """
    Inspect the currently loaded structured dataset.

    Use this tool when the user asks about:

    - dataset columns
    - number of rows
    - number of columns
    - data types
    - missing values
    - dataset preview
    - dataset structure
    """

    print(
        "\n[TOOL EXECUTED] get_data_info\n"
    )

    dataframe = get_current_dataframe()

    # -----------------------------------------------------
    # Missing-value information
    # -----------------------------------------------------

    missing_values = {
        column: int(count)

        for column, count
        in dataframe.isna().sum().items()
    }

    # -----------------------------------------------------
    # Data types
    # -----------------------------------------------------

    data_types = {
        column: str(dtype)

        for column, dtype
        in dataframe.dtypes.items()
    }

    # -----------------------------------------------------
    # Return useful dataset metadata
    # -----------------------------------------------------

    return {
        "file_name":
            get_current_file_name(),

        "row_count":
            int(
                dataframe.shape[0]
            ),

        "column_count":
            int(
                dataframe.shape[1]
            ),

        "columns":
            dataframe.columns.tolist(),

        "data_types":
            data_types,

        "missing_values":
            missing_values,

        "preview":
            _records_from_dataframe(
                dataframe.head(5)
            ),
    }


# =========================================================
# TOOL 2
# AGGREGATION / CALCULATIONS
# =========================================================

@tool
def aggregate_data(
    column: Annotated[
        str,
        "Column to calculate the aggregation on."
    ],

    operation: Annotated[
        Literal[
            "sum",
            "mean",
            "median",
            "min",
            "max",
            "count",
        ],
        (
            "Aggregation operation to perform. "
            "Allowed values: sum, mean, median, "
            "min, max, count."
        ),
    ],

    group_by: Annotated[
        Optional[str],
        (
            "Optional column used to group rows "
            "before calculating the aggregation."
        ),
    ] = None,

) -> dict:
    """
    Perform a safe aggregation on the currently
    loaded structured dataset.

    Use this tool for questions such as:

    - total revenue
    - average revenue
    - minimum cost
    - maximum sales
    - median value
    - number of records
    - revenue by region
    - average revenue by product
    """

    print(
        "\n[TOOL EXECUTED] aggregate_data"
    )

    print(
        f"Column: {column}"
    )

    print(
        f"Operation: {operation}"
    )

    print(
        f"Group by: {group_by}\n"
    )

    dataframe = get_current_dataframe()

    # -----------------------------------------------------
    # Validate target column
    # -----------------------------------------------------

    if column not in dataframe.columns:

        return {
            "error": (
                f"Column '{column}' does not exist."
            ),

            "available_columns":
                dataframe.columns.tolist(),
        }

    # -----------------------------------------------------
    # Validate group-by column
    # -----------------------------------------------------

    if group_by is not None:

        if group_by not in dataframe.columns:

            return {
                "error": (
                    f"Group-by column "
                    f"'{group_by}' does not exist."
                ),

                "available_columns":
                    dataframe.columns.tolist(),
            }

    # =====================================================
    # COUNT
    # =====================================================

    if operation == "count":

        if group_by:

            grouped_result = (
                dataframe
                .groupby(
                    group_by,
                    dropna=False,
                )[column]
                .count()
            )

            results = [
                {
                    "group":
                        str(group),

                    "value":
                        int(value),
                }

                for group, value
                in grouped_result.items()
            ]

            return {
                "column": column,

                "operation":
                    operation,

                "group_by":
                    group_by,

                "results":
                    results,
            }

        return {
            "column":
                column,

            "operation":
                operation,

            "value":
                int(
                    dataframe[column].count()
                ),
        }

    # =====================================================
    # NUMERIC OPERATIONS
    # =====================================================

    numeric_values = pd.to_numeric(
        dataframe[column],
        errors="coerce",
    )

    # If every converted value became NaN,
    # the column isn't usable numerically.

    if numeric_values.notna().sum() == 0:

        return {
            "error": (
                f"Column '{column}' does not contain "
                f"numeric values suitable for "
                f"'{operation}'."
            )
        }

    # =====================================================
    # GROUPED AGGREGATION
    # =====================================================

    if group_by:

        temporary_dataframe = dataframe[
            [group_by]
        ].copy()

        temporary_dataframe[
            "_analysis_value"
        ] = numeric_values

        # Remove rows with unusable numeric values

        temporary_dataframe = (
            temporary_dataframe.dropna(
                subset=[
                    "_analysis_value"
                ]
            )
        )

        grouped = (
            temporary_dataframe
            .groupby(
                group_by,
                dropna=False,
            )["_analysis_value"]
        )

        if operation == "sum":

            result = grouped.sum()

        elif operation == "mean":

            result = grouped.mean()

        elif operation == "median":

            result = grouped.median()

        elif operation == "min":

            result = grouped.min()

        elif operation == "max":

            result = grouped.max()

        else:

            return {
                "error": (
                    f"Unsupported operation: "
                    f"{operation}"
                )
            }

        results = [
            {
                "group":
                    str(group),

                "value":
                    float(value),
            }

            for group, value
            in result.items()
        ]

        return {
            "column":
                column,

            "operation":
                operation,

            "group_by":
                group_by,

            "results":
                results,
        }

    # =====================================================
    # NON-GROUPED AGGREGATION
    # =====================================================

    clean_values = (
        numeric_values.dropna()
    )

    if operation == "sum":

        value = clean_values.sum()

    elif operation == "mean":

        value = clean_values.mean()

    elif operation == "median":

        value = clean_values.median()

    elif operation == "min":

        value = clean_values.min()

    elif operation == "max":

        value = clean_values.max()

    else:

        return {
            "error": (
                f"Unsupported operation: "
                f"{operation}"
            )
        }

    return {
        "column":
            column,

        "operation":
            operation,

        "value":
            float(value),
    }


# =========================================================
# TOOL 3
# FILTER DATA
# =========================================================

@tool
def filter_data(
    column: Annotated[
        str,
        "Column to filter."
    ],

    operator: Annotated[
        Literal[
            "eq",
            "ne",
            "gt",
            "gte",
            "lt",
            "lte",
            "contains",
        ],
        (
            "Comparison operator. "
            "eq=equal, ne=not equal, "
            "gt=greater than, gte=greater than or equal, "
            "lt=less than, lte=less than or equal, "
            "contains=text contains."
        ),
    ],

    value: Annotated[
        str,
        "Value to compare against."
    ],

    limit: Annotated[
        int,
        (
            "Maximum number of matching rows "
            "to return."
        ),
    ] = 10,

) -> dict:
    """
    Filter rows in the currently loaded dataset.

    Use this tool when the user asks to:

    - show rows matching a value
    - find records by region
    - find revenue above a value
    - find revenue below a value
    - find text containing a phrase
    """

    print(
        "\n[TOOL EXECUTED] filter_data"
    )

    print(
        f"Condition: "
        f"{column} {operator} {value}\n"
    )

    dataframe = get_current_dataframe()

    # -----------------------------------------------------
    # Validate column
    # -----------------------------------------------------

    if column not in dataframe.columns:

        return {
            "error": (
                f"Column '{column}' does not exist."
            ),

            "available_columns":
                dataframe.columns.tolist(),
        }

    # -----------------------------------------------------
    # Protect against excessive output
    # -----------------------------------------------------

    limit = max(
        1,
        min(
            int(limit),
            50,
        )
    )

    series = dataframe[column]

    # =====================================================
    # CONTAINS
    # =====================================================

    if operator == "contains":

        mask = (
            series
            .astype(str)
            .str.contains(
                str(value),
                case=False,
                na=False,
            )
        )

    # =====================================================
    # NUMERIC COMPARISONS
    # =====================================================

    elif operator in {
        "gt",
        "gte",
        "lt",
        "lte",
    }:

        numeric_series = pd.to_numeric(
            series,
            errors="coerce",
        )

        try:

            numeric_value = float(
                value
            )

        except ValueError:

            return {
                "error": (
                    f"Value '{value}' must be "
                    "numeric for operator "
                    f"'{operator}'."
                )
            }

        if operator == "gt":

            mask = (
                numeric_series
                > numeric_value
            )

        elif operator == "gte":

            mask = (
                numeric_series
                >= numeric_value
            )

        elif operator == "lt":

            mask = (
                numeric_series
                < numeric_value
            )

        else:

            mask = (
                numeric_series
                <= numeric_value
            )

    # =====================================================
    # EQ / NE
    # =====================================================

    else:

        # -------------------------------------------------
        # Numeric columns
        # -------------------------------------------------

        if pd.api.types.is_numeric_dtype(
            series
        ):

            try:

                comparison_value = float(
                    value
                )

            except ValueError:

                return {
                    "error": (
                        f"Value '{value}' is not valid "
                        f"for numeric column '{column}'."
                    )
                }

            numeric_series = pd.to_numeric(
                series,
                errors="coerce",
            )

            if operator == "eq":

                mask = (
                    numeric_series
                    == comparison_value
                )

            else:

                mask = (
                    numeric_series
                    != comparison_value
                )

        # -------------------------------------------------
        # Text columns
        # -------------------------------------------------

        else:

            normalized_series = (
                series
                .astype(str)
                .str.casefold()
            )

            normalized_value = (
                str(value).casefold()
            )

            if operator == "eq":

                mask = (
                    normalized_series
                    == normalized_value
                )

            else:

                mask = (
                    normalized_series
                    != normalized_value
                )

    # -----------------------------------------------------
    # Apply filter
    # -----------------------------------------------------

    filtered_dataframe = (
        dataframe.loc[
            mask
        ]
    )

    returned_rows = (
        filtered_dataframe.head(
            limit
        )
    )

    # -----------------------------------------------------
    # Return structured output
    # -----------------------------------------------------

    return {
        "condition": {
            "column":
                column,

            "operator":
                operator,

            "value":
                value,
        },

        "matching_row_count":
            int(
                filtered_dataframe.shape[0]
            ),

        "returned_row_count":
            int(
                returned_rows.shape[0]
            ),

        "rows":
            _records_from_dataframe(
                returned_rows
            ),
    }