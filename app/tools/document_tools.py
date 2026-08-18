from typing import Annotated

from haystack.tools import tool

from app.semantic_search import (
    search_documents,
    document_store,
)


# =========================================================
# TOOL 1
# SEARCH DOCUMENT
# =========================================================

@tool
def search_document(
    query: Annotated[
        str,
        (
            "Question or topic to search for "
            "inside the uploaded document."
        ),
    ],

    top_k: Annotated[
        int,
        (
            "Maximum number of relevant "
            "document chunks to return."
        ),
    ] = 3,

) -> dict:
    """
    Search the uploaded PDF/document for information.

    Use this tool whenever the user asks about
    facts or information contained inside the
    uploaded document.
    """

    print(
        "\n[TOOL EXECUTED] search_document"
    )

    print(
        f"Query: {query}\n"
    )

    documents = search_documents(
        query=query,
        top_k=top_k,
    )

    results = []

    for index, document in enumerate(
        documents,
        start=1,
    ):

        results.append(
            {
                "source":
                    index,

                "content":
                    document.content or "",

                "score":
                    document.score,

                "metadata":
                    document.meta,
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
# TOOL 2
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
) -> dict:
    """
    Get technical information about the
    currently indexed PDF/document.

    Always provide the request argument.

    Use:

    request='chunk_count'
    for the number of indexed document chunks.

    request='metadata'
    for document metadata.

    request='summary'
    for general technical information about
    the indexed document.
    """

    print(
        "\n[TOOL EXECUTED] get_document_info"
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
            "error": (
                f"Unsupported request "
                f"'{request}'."
            ),

            "allowed_requests":
                sorted(
                    allowed_requests
                ),
        }

    # -----------------------------------------------------
    # Get indexed documents
    # -----------------------------------------------------

    documents = (
        document_store.filter_documents()
    )

    # =====================================================
    # CHUNK COUNT
    # =====================================================

    if request == "chunk_count":

        return {
            "indexed_chunk_count":
                len(documents),
        }

    # =====================================================
    # METADATA
    # =====================================================

    if request == "metadata":

        metadata_examples = [
            document.meta
            for document
            in documents[:3]
        ]

        return {
            "metadata_examples":
                metadata_examples,
        }

    # =====================================================
    # SUMMARY
    # =====================================================

    metadata_examples = [
        document.meta
        for document
        in documents[:3]
    ]

    return {
        "indexed_chunk_count":
            len(documents),

        "metadata_examples":
            metadata_examples,
    }