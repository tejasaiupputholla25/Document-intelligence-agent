import hashlib

import pytest

from app.db.models import (
    DatasetRecord,
)

from app.db.repositories import (
    create_dataset,
    create_session,
)

from app.structured_data import (
    get_dataframe_for_session,
)


pytestmark = pytest.mark.integration


# =========================================================
# HELPER
# =========================================================

def calculate_hash(
    file_path,
) -> str:

    return hashlib.sha256(
        file_path.read_bytes()
    ).hexdigest()


# =========================================================
# TEST 1
# SESSION A AND B MUST LOAD DIFFERENT DATA
# =========================================================

def test_sessions_load_only_their_own_datasets(
    reset_metadata_db,
    tmp_path,
):

    # -----------------------------------------------------
    # CREATE TWO APPLICATION SESSIONS
    # -----------------------------------------------------

    session_a = (
        create_session()
    )

    session_b = (
        create_session()
    )


    # -----------------------------------------------------
    # CREATE TWO PHYSICAL CSV FILES
    # -----------------------------------------------------

    file_a = (
        tmp_path
        / "session_a.csv"
    )

    file_b = (
        tmp_path
        / "session_b.csv"
    )


    file_a.write_text(
        (
            "name,value\n"
            "A1,100\n"
            "A2,200\n"
        ),
        encoding="utf-8",
    )


    file_b.write_text(
        (
            "name,value\n"
            "B1,10\n"
            "B2,20\n"
            "B3,30\n"
            "B4,40\n"
            "B5,50\n"
        ),
        encoding="utf-8",
    )


    # -----------------------------------------------------
    # REGISTER DATASET A
    # -----------------------------------------------------

    dataset_a = (
        DatasetRecord(

            session_id=
                session_a.id,

            file_name=
                "session_a.csv",

            stored_path=
                str(
                    file_a
                ),

            sha256=
                calculate_hash(
                    file_a
                ),

            row_count=
                2,

            column_count=
                2,

            column_names=[
                "name",
                "value",
            ],

            status=
                "ready",
        )
    )


    create_dataset(
        dataset_a
    )


    # -----------------------------------------------------
    # REGISTER DATASET B
    # -----------------------------------------------------

    dataset_b = (
        DatasetRecord(

            session_id=
                session_b.id,

            file_name=
                "session_b.csv",

            stored_path=
                str(
                    file_b
                ),

            sha256=
                calculate_hash(
                    file_b
                ),

            row_count=
                5,

            column_count=
                2,

            column_names=[
                "name",
                "value",
            ],

            status=
                "ready",
        )
    )


    create_dataset(
        dataset_b
    )


    # -----------------------------------------------------
    # LOAD SESSION A
    # -----------------------------------------------------

    dataframe_a, loaded_dataset_a = (
        get_dataframe_for_session(
            str(
                session_a.id
            )
        )
    )


    # -----------------------------------------------------
    # LOAD SESSION B
    # -----------------------------------------------------

    dataframe_b, loaded_dataset_b = (
        get_dataframe_for_session(
            str(
                session_b.id
            )
        )
    )


    # -----------------------------------------------------
    # VERIFY ROW COUNTS
    # -----------------------------------------------------

    assert (
        len(
            dataframe_a
        )
        == 2
    )


    assert (
        len(
            dataframe_b
        )
        == 5
    )


    # -----------------------------------------------------
    # VERIFY CONTENT
    # -----------------------------------------------------

    assert (
        dataframe_a.iloc[
            0
        ][
            "name"
        ]
        == "A1"
    )


    assert (
        dataframe_b.iloc[
            0
        ][
            "name"
        ]
        == "B1"
    )


    # -----------------------------------------------------
    # VERIFY DATABASE RECORD
    # -----------------------------------------------------

    assert (
        loaded_dataset_a.session_id
        == session_a.id
    )


    assert (
        loaded_dataset_b.session_id
        == session_b.id
    )


    assert (
        loaded_dataset_a.file_name
        == "session_a.csv"
    )


    assert (
        loaded_dataset_b.file_name
        == "session_b.csv"
    )
    
# =========================================================
# TEST 2
# SESSION WITHOUT DATA MUST NOT SEE ANOTHER SESSION'S DATA
# =========================================================

def test_session_without_dataset_cannot_use_other_session_dataset(
    reset_metadata_db,
    tmp_path,
):

    session_a = (
        create_session()
    )

    session_b = (
        create_session()
    )


    file_a = (
        tmp_path
        / "only_a.csv"
    )


    file_a.write_text(
        (
            "name,value\n"
            "SECRET_A,999\n"
        ),
        encoding="utf-8",
    )


    create_dataset(

        DatasetRecord(

            session_id=
                session_a.id,

            file_name=
                "only_a.csv",

            stored_path=
                str(
                    file_a
                ),

            sha256=
                calculate_hash(
                    file_a
                ),

            row_count=
                1,

            column_count=
                2,

            column_names=[
                "name",
                "value",
            ],

            status=
                "ready",
        )
    )


    # -----------------------------------------------------
    # A SHOULD WORK
    # -----------------------------------------------------

    dataframe_a, _ = (
        get_dataframe_for_session(
            str(
                session_a.id
            )
        )
    )


    assert (
        dataframe_a.iloc[
            0
        ][
            "name"
        ]
        == "SECRET_A"
    )


    # -----------------------------------------------------
    # B MUST FAIL
    #
    # It must NOT silently use Session A's dataset.
    # -----------------------------------------------------

    with pytest.raises(
        RuntimeError,
        match=(
            "No structured dataset exists"
        ),
    ):

        get_dataframe_for_session(
            str(
                session_b.id
            )
        )