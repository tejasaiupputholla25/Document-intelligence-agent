import pytest


# =========================================================
# TEST MARKER
# =========================================================

pytestmark = pytest.mark.integration


# =========================================================
# HELPER — CREATE TEST SESSION
# =========================================================

def create_test_session(
    client,
) -> str:
    """
    Create a new backend application session
    and return its UUID as a string.
    """

    response = client.post(
        "/api/v1/sessions"
    )


    assert (
        response.status_code
        == 201
    )


    body = (
        response.json()
    )


    assert (
        "session_id"
        in body
    )


    return body[
        "session_id"
    ]


# =========================================================
# TEST 1 — HEALTH ENDPOINT
# =========================================================

def test_health_endpoint(
    client,
):

    response = client.get(
        "/health"
    )


    assert (
        response.status_code
        == 200
    )


    body = (
        response.json()
    )


    assert (
        body[
            "status"
        ]
        == "ok"
    )


    assert (
        body[
            "service"
        ]
        ==
        "document-intelligence-api"
    )


# =========================================================
# TEST 2 — SESSION CREATION
# =========================================================

def test_create_session_endpoint(
    client,
):

    session_id = (
        create_test_session(
            client
        )
    )


    assert session_id


# =========================================================
# TEST 3 — NEW SESSION MUST BE EMPTY
# =========================================================

def test_new_session_is_empty(
    client,
):

    session_id = (
        create_test_session(
            client
        )
    )


    response = client.get(

        (
            f"/api/v1/sessions/"
            f"{session_id}/status"
        )
    )


    assert (
        response.status_code
        == 200
    )


    body = (
        response.json()
    )


    assert (
        body[
            "document"
        ][
            "ready"
        ]
        is False
    )


    assert (
        body[
            "dataset"
        ][
            "ready"
        ]
        is False
    )


# =========================================================
# TEST 4 — NONEXISTENT SESSION RETURNS 404
# =========================================================

def test_nonexistent_session_returns_404(
    client,
):

    response = client.get(

        (
            "/api/v1/sessions/"
            "11111111-1111-1111-1111-111111111111/"
            "status"
        )
    )


    assert (
        response.status_code
        == 404
    )


    body = (
        response.json()
    )


    assert (
        body[
            "detail"
        ]
        ==
        "Application session was not found."
    )


# =========================================================
# TEST 5 — INVALID UUID RETURNS 422
# =========================================================

def test_invalid_uuid_returns_422(
    client,
):

    response = client.get(

        (
            "/api/v1/sessions/"
            "not-a-valid-uuid/"
            "status"
        )
    )


    assert (
        response.status_code
        == 422
    )


# =========================================================
# TEST 6 — CHAT REQUIRES A RESOURCE
# =========================================================

def test_chat_requires_uploaded_resource(
    client,
):

    session_id = (
        create_test_session(
            client
        )
    )


    response = client.post(

        (
            f"/api/v1/sessions/"
            f"{session_id}/chat"
        ),

        json={
            "question":
                "Hello"
        },
    )


    assert (
        response.status_code
        == 409
    )


    body = (
        response.json()
    )


    assert (
        body[
            "detail"
        ]
        ==
        (
            "Upload a PDF or dataset "
            "before asking questions."
        )
    )


# =========================================================
# TEST 7 — DATASET UPLOAD
# =========================================================

def test_dataset_upload(
    client,
):

    session_id = (
        create_test_session(
            client
        )
    )


    csv_content = (
        b"name,value\n"
        b"A,10\n"
        b"B,20\n"
        b"C,30\n"
    )


    response = client.post(

        (
            f"/api/v1/sessions/"
            f"{session_id}"
            f"/datasets/upload"
        ),

        files={
            "file": (
                "sample.csv",
                csv_content,
                "text/csv",
            )
        },
    )


    assert (
        response.status_code
        == 200
    )


    body = (
        response.json()
    )


    assert (
        body[
            "dataset"
        ][
            "ready"
        ]
        is True
    )


    assert (
        body[
            "dataset"
        ][
            "file_name"
        ]
        == "sample.csv"
    )


    assert (
        body[
            "dataset"
        ][
            "rows"
        ]
        == 3
    )


    assert (
        body[
            "dataset"
        ][
            "columns"
        ]
        == 2
    )


    assert (
        body[
            "dataset"
        ][
            "column_names"
        ]
        ==
        [
            "name",
            "value",
        ]
    )


# =========================================================
# TEST 8 — DATASET PREVIEW
# =========================================================

def test_dataset_preview(
    client,
):

    session_id = (
        create_test_session(
            client
        )
    )


    upload_response = client.post(

        (
            f"/api/v1/sessions/"
            f"{session_id}"
            f"/datasets/upload"
        ),

        files={
            "file": (
                "sample.csv",

                (
                    b"name,value\n"
                    b"A,10\n"
                    b"B,20\n"
                    b"C,30\n"
                ),

                "text/csv",
            )
        },
    )


    assert (
        upload_response.status_code
        == 200
    )


    response = client.get(

        (
            f"/api/v1/sessions/"
            f"{session_id}"
            f"/datasets/preview"
        ),

        params={
            "limit":
                2
        },
    )


    assert (
        response.status_code
        == 200
    )


    body = (
        response.json()
    )


    assert (
        body[
            "file_name"
        ]
        == "sample.csv"
    )


    assert (
        body[
            "returned_rows"
        ]
        == 2
    )


    assert (
        len(
            body[
                "rows"
            ]
        )
        == 2
    )


    assert (
        body[
            "rows"
        ][0][
            "name"
        ]
        == "A"
    )


    assert (
        body[
            "rows"
        ][1][
            "name"
        ]
        == "B"
    )


# =========================================================
# TEST 9 — CHAT IS SAVED TO DATABASE
# =========================================================

def test_chat_is_saved_to_database(
    client,
):

    session_id = (
        create_test_session(
            client
        )
    )


    # -----------------------------------------------------
    # CHAT REQUIRES AT LEAST ONE RESOURCE
    # -----------------------------------------------------

    upload_response = client.post(

        (
            f"/api/v1/sessions/"
            f"{session_id}"
            f"/datasets/upload"
        ),

        files={
            "file": (
                "sample.csv",

                (
                    b"name,value\n"
                    b"A,10\n"
                ),

                "text/csv",
            )
        },
    )


    assert (
        upload_response.status_code
        == 200
    )


    # -----------------------------------------------------
    # SEND CHAT MESSAGE
    #
    # conftest.py replaces run_document_agent()
    # with a fake deterministic Agent.
    # -----------------------------------------------------

    chat_response = client.post(

        (
            f"/api/v1/sessions/"
            f"{session_id}/chat"
        ),

        json={
            "question":
                "How many rows?"
        },
    )


    assert (
        chat_response.status_code
        == 200
    )


    assert (
        chat_response.json()[
            "answer"
        ]
        ==
        "Test answer for: How many rows?"
    )


    # -----------------------------------------------------
    # LOAD PERSISTENT HISTORY
    # -----------------------------------------------------

    history_response = client.get(

        (
            f"/api/v1/sessions/"
            f"{session_id}/chat"
        )
    )


    assert (
        history_response.status_code
        == 200
    )


    messages = (
        history_response
        .json()[
            "messages"
        ]
    )


    assert (
        len(
            messages
        )
        == 2
    )


    # USER MESSAGE

    assert (
        messages[
            0
        ][
            "role"
        ]
        == "user"
    )


    assert (
        messages[
            0
        ][
            "content"
        ]
        == "How many rows?"
    )


    # ASSISTANT MESSAGE

    assert (
        messages[
            1
        ][
            "role"
        ]
        == "assistant"
    )


    assert (
        messages[
            1
        ][
            "content"
        ]
        ==
        "Test answer for: How many rows?"
    )


# =========================================================
# TEST 10 — CLEAR CHAT
# =========================================================

def test_clear_chat(
    client,
):

    session_id = (
        create_test_session(
            client
        )
    )


    # -----------------------------------------------------
    # ADD RESOURCE
    # -----------------------------------------------------

    upload_response = client.post(

        (
            f"/api/v1/sessions/"
            f"{session_id}"
            f"/datasets/upload"
        ),

        files={
            "file": (
                "sample.csv",

                (
                    b"name,value\n"
                    b"A,10\n"
                ),

                "text/csv",
            )
        },
    )


    assert (
        upload_response.status_code
        == 200
    )


    # -----------------------------------------------------
    # CREATE CHAT HISTORY
    # -----------------------------------------------------

    chat_response = client.post(

        (
            f"/api/v1/sessions/"
            f"{session_id}/chat"
        ),

        json={
            "question":
                "Test question"
        },
    )


    assert (
        chat_response.status_code
        == 200
    )


    # -----------------------------------------------------
    # DELETE CHAT HISTORY
    # -----------------------------------------------------

    delete_response = client.delete(

        (
            f"/api/v1/sessions/"
            f"{session_id}/chat"
        )
    )


    assert (
        delete_response.status_code
        == 200
    )


    assert (
        delete_response.json()[
            "message"
        ]
        ==
        "Chat history cleared."
    )


    # -----------------------------------------------------
    # VERIFY EMPTY
    # -----------------------------------------------------

    history_response = client.get(

        (
            f"/api/v1/sessions/"
            f"{session_id}/chat"
        )
    )


    assert (
        history_response.status_code
        == 200
    )


    assert (
        history_response.json()[
            "messages"
        ]
        == []
    )


# =========================================================
# TEST 11 — DATASET STATUS IS SESSION-SPECIFIC
# =========================================================

def test_dataset_status_is_session_specific(
    client,
):

    session_a = (
        create_test_session(
            client
        )
    )


    session_b = (
        create_test_session(
            client
        )
    )


    # -----------------------------------------------------
    # ONLY SESSION A RECEIVES DATA
    # -----------------------------------------------------

    response = client.post(

        (
            f"/api/v1/sessions/"
            f"{session_a}"
            f"/datasets/upload"
        ),

        files={
            "file": (
                "session_a.csv",

                (
                    b"name,value\n"
                    b"A,1\n"
                    b"B,2\n"
                ),

                "text/csv",
            )
        },
    )


    assert (
        response.status_code
        == 200
    )


    # -----------------------------------------------------
    # GET STATUS FOR BOTH
    # -----------------------------------------------------

    status_a = client.get(

        (
            f"/api/v1/sessions/"
            f"{session_a}/status"
        )

    ).json()


    status_b = client.get(

        (
            f"/api/v1/sessions/"
            f"{session_b}/status"
        )

    ).json()


    assert (
        status_a[
            "dataset"
        ][
            "ready"
        ]
        is True
    )


    assert (
        status_a[
            "dataset"
        ][
            "file_name"
        ]
        == "session_a.csv"
    )


    assert (
        status_b[
            "dataset"
        ][
            "ready"
        ]
        is False
    )


# =========================================================
# TEST 12 — MALFORMED CHAT BODY
# =========================================================

def test_chat_question_is_required(
    client,
):

    session_id = (
        create_test_session(
            client
        )
    )


    # No question property.

    response = client.post(

        (
            f"/api/v1/sessions/"
            f"{session_id}/chat"
        ),

        json={},
    )


    assert (
        response.status_code
        == 422
    )


# =========================================================
# TEST 13 — QUESTION LENGTH LIMIT
# =========================================================

def test_chat_question_over_max_length_is_rejected(
    client,
):

    session_id = (
        create_test_session(
            client
        )
    )


    very_long_question = (
        "A"
        * 4001
    )


    response = client.post(

        (
            f"/api/v1/sessions/"
            f"{session_id}/chat"
        ),

        json={
            "question":
                very_long_question
        },
    )


    assert (
        response.status_code
        == 422
    )


# =========================================================
# TEST 14 — SECURITY:
# INTERNAL AGENT ERROR MUST NOT LEAK
# =========================================================

def test_agent_internal_error_is_not_exposed(
    client,
    monkeypatch,
):

    import app.api.main as api_main


    # -----------------------------------------------------
    # CREATE APPLICATION SESSION
    # -----------------------------------------------------

    session_id = (
        create_test_session(
            client
        )
    )


    # -----------------------------------------------------
    # ADD A RESOURCE
    #
    # Without this, FastAPI correctly returns 409
    # before it ever reaches the Agent.
    # -----------------------------------------------------

    upload_response = client.post(

        (
            f"/api/v1/sessions/"
            f"{session_id}"
            f"/datasets/upload"
        ),

        files={
            "file": (

                "sample.csv",

                (
                    b"name,value\n"
                    b"A,10\n"
                ),

                "text/csv",
            )
        },
    )


    assert (
        upload_response.status_code
        == 200
    )


    # -----------------------------------------------------
    # CREATE A FAKE BROKEN AGENT
    #
    # The exception intentionally contains information
    # that must NEVER appear in the HTTP response.
    # -----------------------------------------------------

    def broken_agent(
        question: str,
        session_id: str,
    ) -> str:

        raise RuntimeError(
            (
                "SUPER_SECRET_DATABASE_"
                "PASSWORD_123"
            )
        )


    # -----------------------------------------------------
    # OVERRIDE THE NORMAL FAKE AGENT PROVIDED BY conftest
    # -----------------------------------------------------

    monkeypatch.setattr(
        api_main,
        "run_document_agent",
        broken_agent,
    )


    # -----------------------------------------------------
    # CALL CHAT
    # -----------------------------------------------------

    response = client.post(

        (
            f"/api/v1/sessions/"
            f"{session_id}/chat"
        ),

        json={
            "question":
                "Trigger internal failure"
        },
    )


    # -----------------------------------------------------
    # SERVER MUST RETURN 500
    # -----------------------------------------------------

    assert (
        response.status_code
        == 500
    )


    body = (
        response.json()
    )


    # -----------------------------------------------------
    # CLIENT SHOULD RECEIVE ONLY GENERIC ERROR
    # -----------------------------------------------------

    assert (
        body[
            "detail"
        ]
        ==
        "Agent request failed."
    )


    # -----------------------------------------------------
    # SECRET INTERNAL ERROR MUST NOT LEAK
    # -----------------------------------------------------

    serialized_body = (
        str(
            body
        )
    )


    assert (
        "SUPER_SECRET"
        not in serialized_body
    )


    assert (
        "DATABASE_PASSWORD"
        not in serialized_body
    )


    assert (
        "PASSWORD_123"
        not in serialized_body
    )