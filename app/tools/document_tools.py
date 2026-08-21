from typing import Annotated

from haystack.components.agents import (
    State,
)

from haystack.tools import (
    tool,
)

from app.semantic_search import (
    get_session_documents,
    search_documents,
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
# SEARCH DOCUMENT
# =========================================================

@tool
def search_document(

    query: Annotated[
        str,
        (
            "Question or topic to search for "
            "inside the current session's "
            "uploaded PDF/document."
        ),
    ],

    state: State,

    top_k: Annotated[
        int,
        (
            "Maximum number of relevant "
            "document chunks to return."
        ),
    ] = 3,

) -> dict:
    """
    Search the current session's indexed PDF
    for relevant information.
    """

    session_id = (
        _get_session_id(
            state
        )
    )


    print(
        "\n[TOOL EXECUTED] search_document"
    )

    print(
        f"Session: {session_id}"
    )

    print(
        f"Query: {query}\n"
    )


    documents = (
        search_documents(

            query=
                query,

            session_id=
                session_id,

            top_k=
                top_k,
        )
    )


    results = []


    for index, document in enumerate(
        documents,
        start=1,
    ):

        # -------------------------------------------------
        # SECURITY:
        # DO NOT SEND INTERNAL SESSION ID TO LLM
        # -------------------------------------------------

        metadata = dict(
            document.meta or {}
        )


        metadata.pop(
            "session_id",
            None,
        )


        results.append(
            {
                "source":
                    index,

                "content":
                    document.content
                    or "",

                "score":
                    document.score,

                "metadata":
                    metadata,
            }
        )


    return {

        "query":
            query,

        "result_count":
            len(results),

        "results":
            results,
    }


# =========================================================
# DOCUMENT INFORMATION
# =========================================================

@tool
def get_document_info(

    request: Annotated[
        str,
        (
            "Type of document information requested. "
            "Use exactly one of: "
            "chunk_count, metadata, summary."
        ),
    ],

    state: State,

) -> dict:
    """
    Get technical information about the current
    session's indexed PDF.

    Always provide request.
    """

    session_id = (
        _get_session_id(
            state
        )
    )


    print(
        "\n[TOOL EXECUTED] get_document_info"
    )

    print(
        f"Session: {session_id}"
    )

    print(
        f"Request: {request}\n"
    )


    request = (
        request
        .strip()
        .lower()
    )


    allowed_requests = {
        "chunk_count",
        "metadata",
        "summary",
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


    documents = (
        get_session_documents(
            session_id
        )
    )


    # =====================================================
    # CHUNK COUNT
    # =====================================================

    if request == "chunk_count":

        return {

            "indexed_chunk_count":
                len(
                    documents
                )
        }


    # =====================================================
    # SAFE METADATA
    # =====================================================

    metadata_examples = []


    for document in documents[
        :3
    ]:

        metadata = dict(
            document.meta or {}
        )


        # Never expose internal workspace/session ID
        # back to the language model.

        metadata.pop(
            "session_id",
            None,
        )


        metadata_examples.append(
            metadata
        )


    # =====================================================
    # METADATA
    # =====================================================

    if request == "metadata":

        return {

            "metadata_examples":
                metadata_examples,
        }


    # =====================================================
    # SUMMARY
    # =====================================================

    return {

        "indexed_chunk_count":
            len(
                documents
            ),

        "metadata_examples":
            metadata_examples,
    }