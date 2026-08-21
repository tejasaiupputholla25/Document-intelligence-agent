import json

from typing import Annotated

import pandas as pd

from haystack.components.agents import (
    State,
)

from haystack.tools import (
    tool,
)

from app.structured_data import (
    get_dataframe_for_session,
)


# =========================================================
# INTERNAL SESSION ACCESS
# =========================================================

def _get_session_id(
    state: State,
) -> str:

    session_id = (
        state.get(
            "session_id"
        )
    )


    if not session_id:

        raise RuntimeError(
            "Agent session_id is missing."
        )


    return str(
        session_id
    )


# =========================================================
# SAFE RECORD CONVERSION
# =========================================================

def _records_from_dataframe(
    dataframe: pd.DataFrame,
) -> list[dict]:

    json_text = (
        dataframe.to_json(

            orient=
                "records",

            date_format=
                "iso",
        )
    )


    return json.loads(
        json_text
    )


# =========================================================
# GET DATA INFO
# =========================================================

@tool
def get_data_info(

    request: Annotated[
        str,
        (
            "Type of dataset information requested. "
            "Use exactly one of: summary, row_count, "
            "column_count, columns, preview, "
            "data_types, missing_values."
        ),
    ],

    state: State,

) -> dict:
    """
    Get information about the current session's
    structured dataset.
    """

    session_id = (
        _get_session_id(
            state
        )
    )


    print(
        "\n[TOOL EXECUTED] get_data_info"
    )

    print(
        f"Session: {session_id}"
    )

    print(
        f"Request: {request}\n"
    )


    dataframe, dataset = (
        get_dataframe_for_session(
            session_id
        )
    )


    request = (
        request
        .strip()
        .lower()
    )


    allowed_requests = {
        "summary",
        "row_count",
        "column_count",
        "columns",
        "preview",
        "data_types",
        "missing_values",
    }


    if request not in allowed_requests:

        return {

            "error":
                (
                    f"Unsupported request "
                    f"'{request}'."
                ),

            "allowed_requests":
                sorted(
                    allowed_requests
                ),
        }


    # =====================================================
    # ROW COUNT
    # =====================================================

    if request == "row_count":

        return {

            "file_name":
                dataset.file_name,

            "row_count":
                int(
                    dataframe.shape[
                        0
                    ]
                ),
        }


    # =====================================================
    # COLUMN COUNT
    # =====================================================

    if request == "column_count":

        return {

            "file_name":
                dataset.file_name,

            "column_count":
                int(
                    dataframe.shape[
                        1
                    ]
                ),
        }


    # =====================================================
    # COLUMNS
    # =====================================================

    if request == "columns":

        return {

            "file_name":
                dataset.file_name,

            "columns":
                dataframe.columns.tolist(),
        }


    # =====================================================
    # PREVIEW
    # =====================================================

    if request == "preview":

        preview = (
            dataframe.head(
                5
            )
        )


        return {

            "file_name":
                dataset.file_name,

            "rows":
                _records_from_dataframe(
                    preview
                ),
        }


    # =====================================================
    # DATA TYPES
    # =====================================================

    if request == "data_types":

        data_types = {

            str(column):
                str(dtype)

            for column, dtype
            in dataframe.dtypes.items()
        }


        return {

            "file_name":
                dataset.file_name,

            "data_types":
                data_types,
        }


    # =====================================================
    # MISSING VALUES
    # =====================================================

    if request == "missing_values":

        missing_values = {

            str(column):
                int(count)

            for column, count
            in dataframe.isna().sum().items()
        }


        return {

            "file_name":
                dataset.file_name,

            "missing_values":
                missing_values,
        }


    # =====================================================
    # SUMMARY
    # =====================================================

    return {

        "file_name":
            dataset.file_name,

        "row_count":
            int(
                dataframe.shape[
                    0
                ]
            ),

        "column_count":
            int(
                dataframe.shape[
                    1
                ]
            ),

        "columns":
            dataframe.columns.tolist(),

        "preview":
            _records_from_dataframe(
                dataframe.head(
                    5
                )
            ),
    }


# =========================================================
# AGGREGATE DATA
# =========================================================

@tool
def aggregate_data(

    column: Annotated[
        str,
        (
            "Name of the dataset column "
            "to aggregate."
        ),
    ],

    operation: Annotated[
        str,
        (
            "Aggregation operation. "
            "Use one of: sum, mean, median, "
            "min, max, count."
        ),
    ],

    state: State,

    group_by: Annotated[
        str,
        (
            "Optional column to group results by. "
            "Use an empty string when grouping "
            "is not required."
        ),
    ] = "",

) -> dict:
    """
    Perform a controlled aggregation on the
    current session's dataset.
    """

    session_id = (
        _get_session_id(
            state
        )
    )


    print(
        "\n[TOOL EXECUTED] aggregate_data"
    )

    print(
        f"Session: {session_id}"
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


    dataframe, dataset = (
        get_dataframe_for_session(
            session_id
        )
    )


    column = (
        column.strip()
    )


    operation = (
        operation
        .strip()
        .lower()
    )


    group_by = (
        group_by.strip()
    )


    allowed_operations = {
        "sum",
        "mean",
        "median",
        "min",
        "max",
        "count",
    }


    if operation not in allowed_operations:

        return {

            "error":
                (
                    f"Unsupported operation "
                    f"'{operation}'."
                ),

            "allowed_operations":
                sorted(
                    allowed_operations
                ),
        }


    if column not in dataframe.columns:

        return {

            "error":
                (
                    f"Column '{column}' "
                    f"does not exist."
                ),

            "available_columns":
                dataframe.columns.tolist(),
        }


    if (
        group_by

        and

        group_by not in dataframe.columns
    ):

        return {

            "error":
                (
                    f"Group-by column "
                    f"'{group_by}' "
                    f"does not exist."
                ),

            "available_columns":
                dataframe.columns.tolist(),
        }


    # =====================================================
    # COUNT
    # =====================================================

    if operation == "count":

        if group_by:

            grouped = (
                dataframe
                .groupby(
                    group_by,
                    dropna=False,
                )[
                    column
                ]
                .count()
            )


            return {

                "file_name":
                    dataset.file_name,

                "column":
                    column,

                "operation":
                    operation,

                "group_by":
                    group_by,

                "results": {

                    str(key):
                        int(value)

                    for key, value
                    in grouped.items()
                },
            }


        return {

            "file_name":
                dataset.file_name,

            "column":
                column,

            "operation":
                operation,

            "result":
                int(
                    dataframe[
                        column
                    ].count()
                ),
        }


    # =====================================================
    # NUMERIC CONVERSION
    # =====================================================

    numeric_values = (
        pd.to_numeric(

            dataframe[
                column
            ],

            errors=
                "coerce",
        )
    )


    if numeric_values.notna().sum() == 0:

        return {

            "error":
                (
                    f"Column '{column}' does not "
                    f"contain numeric values "
                    f"required for '{operation}'."
                )
        }


    # =====================================================
    # GROUPED NUMERIC AGGREGATION
    # =====================================================

    if group_by:

        working = (
            dataframe[
                [
                    group_by,
                ]
            ]
            .copy()
        )


        working[
            "_analysis_value"
        ] = numeric_values


        grouped = (
            working
            .groupby(
                group_by,
                dropna=False,
            )[
                "_analysis_value"
            ]
        )


        if operation == "sum":

            result_series = (
                grouped.sum()
            )


        elif operation == "mean":

            result_series = (
                grouped.mean()
            )


        elif operation == "median":

            result_series = (
                grouped.median()
            )


        elif operation == "min":

            result_series = (
                grouped.min()
            )


        elif operation == "max":

            result_series = (
                grouped.max()
            )


        else:

            raise RuntimeError(
                "Unexpected aggregation operation."
            )


        results = {}


        for key, value in (
            result_series.items()
        ):

            if pd.isna(
                value
            ):

                results[
                    str(key)
                ] = None

            else:

                results[
                    str(key)
                ] = float(
                    value
                )


        return {

            "file_name":
                dataset.file_name,

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
    # NON-GROUPED NUMERIC AGGREGATION
    # =====================================================

    if operation == "sum":

        result = (
            numeric_values.sum()
        )


    elif operation == "mean":

        result = (
            numeric_values.mean()
        )


    elif operation == "median":

        result = (
            numeric_values.median()
        )


    elif operation == "min":

        result = (
            numeric_values.min()
        )


    elif operation == "max":

        result = (
            numeric_values.max()
        )


    else:

        raise RuntimeError(
            "Unexpected aggregation operation."
        )


    return {

        "file_name":
            dataset.file_name,

        "column":
            column,

        "operation":
            operation,

        "result":
            (
                None

                if pd.isna(
                    result
                )

                else float(
                    result
                )
            ),
    }


# =========================================================
# FILTER DATA
# =========================================================

@tool
def filter_data(

    column: Annotated[
        str,
        (
            "Dataset column on which the "
            "filter should be applied."
        ),
    ],

    operator: Annotated[
        str,
        (
            "Comparison operator. "
            "Use one of: eq, ne, gt, gte, "
            "lt, lte, contains."
        ),
    ],

    value: Annotated[
        str,
        (
            "Value to compare against."
        ),
    ],

    state: State,

    limit: Annotated[
        int,
        (
            "Maximum number of matching rows "
            "to return. Maximum allowed is 50."
        ),
    ] = 10,

) -> dict:
    """
    Filter rows in the current session's dataset
    using controlled operators.
    """

    session_id = (
        _get_session_id(
            state
        )
    )


    print(
        "\n[TOOL EXECUTED] filter_data"
    )

    print(
        f"Session: {session_id}"
    )

    print(
        f"Column: {column}"
    )

    print(
        f"Operator: {operator}"
    )

    print(
        f"Value: {value}\n"
    )


    dataframe, dataset = (
        get_dataframe_for_session(
            session_id
        )
    )


    column = (
        column.strip()
    )


    operator = (
        operator
        .strip()
        .lower()
    )


    allowed_operators = {
        "eq",
        "ne",
        "gt",
        "gte",
        "lt",
        "lte",
        "contains",
    }


    if operator not in allowed_operators:

        return {

            "error":
                (
                    f"Unsupported operator "
                    f"'{operator}'."
                ),

            "allowed_operators":
                sorted(
                    allowed_operators
                ),
        }


    if column not in dataframe.columns:

        return {

            "error":
                (
                    f"Column '{column}' "
                    f"does not exist."
                ),

            "available_columns":
                dataframe.columns.tolist(),
        }


    limit = max(
        1,
        min(
            int(limit),
            50,
        ),
    )


    series = (
        dataframe[
            column
        ]
    )


    # =====================================================
    # CONTAINS
    # =====================================================

    if operator == "contains":

        mask = (
            series
            .astype(
                str
            )
            .str.contains(

                str(
                    value
                ),

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

        try:

            comparison_value = (
                float(
                    value
                )
            )


        except (
            TypeError,
            ValueError,
        ):

            return {

                "error":
                    (
                        f"Operator '{operator}' "
                        f"requires a numeric value."
                    )
            }


        numeric_series = (
            pd.to_numeric(

                series,

                errors=
                    "coerce",
            )
        )


        if operator == "gt":

            mask = (
                numeric_series
                > comparison_value
            )


        elif operator == "gte":

            mask = (
                numeric_series
                >= comparison_value
            )


        elif operator == "lt":

            mask = (
                numeric_series
                < comparison_value
            )


        else:

            mask = (
                numeric_series
                <= comparison_value
            )


    # =====================================================
    # EQUALITY / INEQUALITY
    # =====================================================

    else:

        if pd.api.types.is_numeric_dtype(
            series
        ):

            try:

                comparison_value = (
                    float(
                        value
                    )
                )


                numeric_series = (
                    pd.to_numeric(

                        series,

                        errors=
                            "coerce",
                    )
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


            except (
                TypeError,
                ValueError,
            ):

                return {

                    "error":
                        (
                            f"Value '{value}' "
                            f"is not valid for "
                            f"numeric column '{column}'."
                        )
                }


        else:

            normalized_series = (
                series
                .astype(
                    str
                )
                .str
                .casefold()
            )


            normalized_value = (
                str(
                    value
                )
                .casefold()
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


    filtered = (
        dataframe[
            mask.fillna(
                False
            )
        ]
    )


    return {

        "file_name":
            dataset.file_name,

        "column":
            column,

        "operator":
            operator,

        "value":
            value,

        "matching_row_count":
            int(
                len(
                    filtered
                )
            ),

        "returned_row_count":
            int(
                min(
                    len(
                        filtered
                    ),
                    limit,
                )
            ),

        "rows":
            _records_from_dataframe(

                filtered.head(
                    limit
                )
            ),
    }