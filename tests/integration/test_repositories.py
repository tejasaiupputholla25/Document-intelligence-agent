import pytest


from app.db.repositories import (
    create_session,
    delete_chat_messages,
    get_chat_messages,
    get_session,
    save_chat_message,
)


pytestmark = (
    pytest.mark.integration
)


# =========================================================
# SESSION CREATE + READ
# =========================================================

def test_create_and_get_session(
    reset_metadata_db,
):

    created_session = (
        create_session()
    )


    loaded_session = (
        get_session(
            created_session.id
        )
    )


    assert (
        loaded_session
        is not None
    )


    assert (
        loaded_session.id
        == created_session.id
    )


# =========================================================
# CHAT PERSISTENCE
# =========================================================

def test_chat_message_persistence(
    reset_metadata_db,
):

    session = (
        create_session()
    )


    save_chat_message(

        session_id=
            session.id,

        role=
            "user",

        content=
            "Hello",
    )


    save_chat_message(

        session_id=
            session.id,

        role=
            "assistant",

        content=
            "Hi there",
    )


    messages = (
        get_chat_messages(
            session.id
        )
    )


    assert (
        len(
            messages
        )
        == 2
    )


    assert (
        messages[
            0
        ].role
        == "user"
    )


    assert (
        messages[
            0
        ].content
        == "Hello"
    )


    assert (
        messages[
            1
        ].role
        == "assistant"
    )


    assert (
        messages[
            1
        ].content
        == "Hi there"
    )


# =========================================================
# CHAT DELETE
# =========================================================

def test_delete_chat_messages(
    reset_metadata_db,
):

    session = (
        create_session()
    )


    save_chat_message(

        session_id=
            session.id,

        role=
            "user",

        content=
            "Test message",
    )


    assert (
        len(
            get_chat_messages(
                session.id
            )
        )
        == 1
    )


    delete_chat_messages(
        session.id
    )


    assert (
        get_chat_messages(
            session.id
        )
        == []
    )


# =========================================================
# INVALID CHAT ROLE SECURITY
# =========================================================

def test_invalid_chat_role_is_rejected(
    reset_metadata_db,
):

    session = (
        create_session()
    )


    with pytest.raises(
        ValueError,
        match=(
            "Unsupported chat role"
        ),
    ):

        save_chat_message(

            session_id=
                session.id,

            role=
                "system",

            content=
                (
                    "This message must "
                    "not be stored."
                ),
        )


    messages = (
        get_chat_messages(
            session.id
        )
    )


    assert (
        messages
        == []
    )