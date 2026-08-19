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
# SESSION HELPER
# =========================================================

def _get_session_id(
    state: State,
) -> str:

    session_id = state.get(
        "session_id"
    )


    if not session_id:

        raise RuntimeError(
            "Agent session_id is missing."
        )


    return str(
        session_id
    )


# =========================================================
# DATAFRAME -> JSON RECORDS
# =========================================================

def _records_from_dataframe(
    dataframe: pd.DataFrame,
) -> list[dict]:

    json_text = (
        dataframe.to_json(
            orient="records",
            date_format="iso",
        )
    )


    return json.loads(
        json_text
    )


# =========================================================
# TOOL 1
# DATASET INFORMATION
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
    Inspect the structured dataset belonging
    to the current application session.
    """

    session_id = (
        _get_session_id(
            state
        )
    )


    print(
        "\n[TOOL EXECUTED] "
        "get_data_info"
    )

    print(
        f"Session: "
        f"{session_id}"
    )

    print(
        f"Request: "
        f"{request}\n"
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


    if request not in (
        allowed_requests
    ):

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


    # -----------------------------------------------------
    # SHARED DATA
    # -----------------------------------------------------

    row_count = int(
        dataframe.shape[0]
    )


    column_count = int(
        dataframe.shape[1]
    )


    columns = (
        dataframe.columns.tolist()
    )


    missing_values = {

        column:
            int(count)

        for column, count
        in dataframe
        .isna()
        .sum()
        .items()
    }


    data_types = {

        column:
            str(dtype)

        for column, dtype
        in dataframe.dtypes.items()
    }


    preview = (
        _records_from_dataframe(
            dataframe.head(5)
        )
    )


    # =====================================================
    # ROW COUNT
    # =====================================================

    if request == "row_count":

        return {

            "file_name":
                dataset.file_name,

            "row_count":
                row_count,
        }


    # =====================================================
    # COLUMN COUNT
    # =====================================================

    if request == "column_count":

        return {

            "file_name":
                dataset.file_name,

            "column_count":
                column_count,
        }


    # =====================================================
    # COLUMNS
    # =====================================================

    if request == "columns":

        return {

            "file_name":
                dataset.file_name,

            "columns":
                columns,
        }


    # =====================================================
    # PREVIEW
    # =====================================================

    if request == "preview":

        return {

            "file_name":
                dataset.file_name,

            "preview":
                preview,
        }


    # =====================================================
    # DATA TYPES
    # =====================================================

    if request == "data_types":

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
            row_count,

        "column_count":
            column_count,

        "columns":
            columns,

        "data_types":
            data_types,

        "missing_values":
            missing_values,

        "preview":
            preview,
    }


# =========================================================
# TOOL 2
# AGGREGATION
# =========================================================

@tool
def aggregate_data(

    column: Annotated[
        str,
        (
            "Column on which the calculation "
            "should be performed."
        ),
    ],

    operation: Annotated[
        str,
        (
            "Aggregation operation. "
            "Use exactly one of: "
            "sum, mean, median, min, max, count."
        ),
    ],

    state: State,

    group_by: Annotated[
        str,
        (
            "Optional grouping column. "
            "Use an empty string when grouping "
            "is not required."
        ),
    ] = "",

) -> dict:
    """
    Perform a safe aggregation on the
    current session's structured dataset.
    """

    session_id = (
        _get_session_id(
            state
        )
    )


    print(
        "\n[TOOL EXECUTED] "
        "aggregate_data"
    )

    print(
        f"Session: "
        f"{session_id}"
    )

    print(
        f"Column: "
        f"{column}"
    )

    print(
        f"Operation: "
        f"{operation}"
    )

    print(
        f"Group by: "
        f"{group_by}\n"
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

        if group_by

        else ""
    )


    valid_operations = {

        "sum",

        "mean",

        "median",

        "min",

        "max",

        "count",
    }


    # -----------------------------------------------------
    # VALIDATE OPERATION
    # -----------------------------------------------------

    if operation not in (
        valid_operations
    ):

        return {

            "error":
                (
                    f"Unsupported operation "
                    f"'{operation}'."
                ),

            "allowed_operations":
                sorted(
                    valid_operations
                ),
        }


    # -----------------------------------------------------
    # VALIDATE COLUMN
    # -----------------------------------------------------

    if column not in (
        dataframe.columns
    ):

        return {

            "error":
                (
                    f"Column '{column}' "
                    "does not exist."
                ),

            "available_columns":
                dataframe.columns.tolist(),
        }


    # -----------------------------------------------------
    # VALIDATE GROUP-BY
    # -----------------------------------------------------

    if (
        group_by

        and

        group_by
        not in dataframe.columns
    ):

        return {

            "error":
                (
                    f"Grouping column "
                    f"'{group_by}' "
                    "does not exist."
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


        return {

            "file_name":
                dataset.file_name,

            "column":
                column,

            "operation":
                operation,

            "value":
                int(
                    dataframe[
                        column
                    ]
                    .count()
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


    if (
        numeric_values
        .notna()
        .sum()
        == 0
    ):

        return {

            "error":
                (
                    f"Column '{column}' does "
                    "not contain numeric values "
                    f"suitable for '{operation}'."
                )
        }


    # =====================================================
    # GROUPED CALCULATION
    # =====================================================

    if group_by:

        temporary_dataframe = (

            dataframe[
                [group_by]
            ]

            .copy()
        )


        temporary_dataframe[
            "_analysis_value"
        ] = numeric_values


        temporary_dataframe = (

            temporary_dataframe
            .dropna(
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
            )[
                "_analysis_value"
            ]
        )


        if operation == "sum":

            result = (
                grouped.sum()
            )


        elif operation == "mean":

            result = (
                grouped.mean()
            )


        elif operation == "median":

            result = (
                grouped.median()
            )


        elif operation == "min":

            result = (
                grouped.min()
            )


        elif operation == "max":

            result = (
                grouped.max()
            )


        else:

            return {

                "error":
                    (
                        f"Unsupported operation "
                        f"'{operation}'."
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
    # NON-GROUPED CALCULATION
    # =====================================================

    clean_values = (
        numeric_values.dropna()
    )


    if operation == "sum":

        result_value = (
            clean_values.sum()
        )


    elif operation == "mean":

        result_value = (
            clean_values.mean()
        )


    elif operation == "median":

        result_value = (
            clean_values.median()
        )


    elif operation == "min":

        result_value = (
            clean_values.min()
        )


    elif operation == "max":

        result_value = (
            clean_values.max()
        )


    else:

        return {

            "error":
                (
                    f"Unsupported operation "
                    f"'{operation}'."
                )
        }


    return {

        "file_name":
            dataset.file_name,

        "column":
            column,

        "operation":
            operation,

        "value":
            float(
                result_value
            ),
    }


# =========================================================
# TOOL 3
# FILTER DATA
# =========================================================

@tool
def filter_data(

    column: Annotated[
        str,
        (
            "Column on which the filter "
            "should be applied."
        ),
    ],

    operator: Annotated[
        str,
        (
            "Filter operator. "
            "Use exactly one of: "
            "eq, ne, gt, gte, lt, lte, contains."
        ),
    ],

    value: Annotated[
        str,
        (
            "Value to compare the "
            "column against."
        ),
    ],

    state: State,

    limit: Annotated[
        int,
        (
            "Maximum number of matching "
            "rows to return."
        ),
    ] = 10,

) -> dict:
    """
    Filter rows from the current session's
    structured dataset.
    """

    session_id = (
        _get_session_id(
            state
        )
    )


    print(
        "\n[TOOL EXECUTED] "
        "filter_data"
    )

    print(
        f"Session: "
        f"{session_id}"
    )

    print(
        f"Condition: "
        f"{column} {operator} {value}\n"
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


    valid_operators = {

        "eq",

        "ne",

        "gt",

        "gte",

        "lt",

        "lte",

        "contains",
    }


    # -----------------------------------------------------
    # VALIDATE OPERATOR
    # -----------------------------------------------------

    if operator not in (
        valid_operators
    ):

        return {

            "error":
                (
                    f"Unsupported operator "
                    f"'{operator}'."
                ),

            "allowed_operators":
                sorted(
                    valid_operators
                ),
        }


    # -----------------------------------------------------
    # VALIDATE COLUMN
    # -----------------------------------------------------

    if column not in (
        dataframe.columns
    ):

        return {

            "error":
                (
                    f"Column '{column}' "
                    "does not exist."
                ),

            "available_columns":
                dataframe.columns.tolist(),
        }


    # -----------------------------------------------------
    # LIMIT
    # -----------------------------------------------------

    limit = max(

        1,

        min(
            int(limit),
            50,
        )
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

        numeric_series = (
            pd.to_numeric(

                series,

                errors=
                    "coerce",
            )
        )


        try:

            numeric_value = float(
                value
            )


        except ValueError:

            return {

                "error":
                    (
                        f"Value '{value}' "
                        "must be numeric for "
                        "this comparison."
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
    # EQUALITY / INEQUALITY
    # =====================================================

    else:

        if (
            pd.api.types
            .is_numeric_dtype(
                series
            )
        ):

            try:

                comparison_value = float(
                    value
                )


            except ValueError:

                return {

                    "error":
                        (
                            f"Value '{value}' "
                            "is not valid for "
                            f"numeric column "
                            f"'{column}'."
                        )
                }


            numeric_series = (
                pd.to_numeric(
                    series,
                    errors="coerce",
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


        else:

            normalized_series = (

                series

                .astype(str)

                .str.casefold()
            )


            normalized_value = (

                str(value)
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


    # =====================================================
    # APPLY FILTER
    # =====================================================

    filtered_dataframe = (

        dataframe.loc[
            mask
        ]
    )


    returned_rows = (

        filtered_dataframe
        .head(
            limit
        )
    )


    return {

        "file_name":
            dataset.file_name,

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