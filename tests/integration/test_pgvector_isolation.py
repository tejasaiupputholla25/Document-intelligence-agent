from uuid import uuid4

import pytest

from haystack import (
    Document,
)

from haystack.document_stores.types import (
    DuplicatePolicy,
)

from app.semantic_search import (
    build_session_filter,
    delete_session_documents,
    document_store,
    get_session_document_count,
    retriever,
)


pytestmark = pytest.mark.integration


# =========================================================
# CONSTANT
# =========================================================

EMBEDDING_DIMENSION = 768


# =========================================================
# SYNTHETIC VECTOR
# =========================================================

def make_test_vector() -> list[float]:
    """
    Create a deterministic 768-dimensional vector.

    Both sessions intentionally receive the same vector.

    Therefore metadata filtering is the only thing
    separating their retrieval results.
    """

    vector = (
        [0.0]
        * EMBEDDING_DIMENSION
    )


    vector[0] = 1.0


    return vector


# =========================================================
# TEST 1
# RETRIEVAL MUST BE SESSION-SCOPED
# =========================================================

def test_pgvector_retrieval_is_session_scoped(
    clean_vector_store,
):

    session_a = str(
        uuid4()
    )

    session_b = str(
        uuid4()
    )


    document_a_id = str(
        uuid4()
    )

    document_b_id = str(
        uuid4()
    )


    # -----------------------------------------------------
    # SESSION A DOCUMENT
    # -----------------------------------------------------

    document_a = (
        Document(

            id=
                f"{document_a_id}:0",

            content=(
                "The confidential project "
                "codename is ORION."
            ),

            embedding=
                make_test_vector(),

            meta={
                "session_id":
                    session_a,

                "document_id":
                    document_a_id,

                "source_file":
                    "orion.pdf",

                "chunk_index":
                    0,
            },
        )
    )


    # -----------------------------------------------------
    # SESSION B DOCUMENT
    # -----------------------------------------------------

    document_b = (
        Document(

            id=
                f"{document_b_id}:0",

            content=(
                "The confidential project "
                "codename is NEBULA."
            ),

            embedding=
                make_test_vector(),

            meta={
                "session_id":
                    session_b,

                "document_id":
                    document_b_id,

                "source_file":
                    "nebula.pdf",

                "chunk_index":
                    0,
            },
        )
    )


    # -----------------------------------------------------
    # STORE BOTH
    # -----------------------------------------------------

    document_store.write_documents(

        [
            document_a,
            document_b,
        ],

        policy=
            DuplicatePolicy.OVERWRITE,
    )


    # =====================================================
    # SESSION A SEARCH
    # =====================================================

    result_a = (
        retriever.run(

            query_embedding=
                make_test_vector(),

            filters=
                build_session_filter(
                    session_a
                ),

            top_k=
                10,
        )
    )


    documents_a = (
        result_a[
            "documents"
        ]
    )


    assert (
        len(
            documents_a
        )
        == 1
    )


    assert (
        documents_a[
            0
        ]
        .meta[
            "session_id"
        ]
        == session_a
    )


    assert (
        "ORION"
        in documents_a[
            0
        ].content
    )


    assert (
        "NEBULA"
        not in documents_a[
            0
        ].content
    )


    # =====================================================
    # SESSION B SEARCH
    # =====================================================

    result_b = (
        retriever.run(

            query_embedding=
                make_test_vector(),

            filters=
                build_session_filter(
                    session_b
                ),

            top_k=
                10,
        )
    )


    documents_b = (
        result_b[
            "documents"
        ]
    )


    assert (
        len(
            documents_b
        )
        == 1
    )


    assert (
        documents_b[
            0
        ]
        .meta[
            "session_id"
        ]
        == session_b
    )


    assert (
        "NEBULA"
        in documents_b[
            0
        ].content
    )


    assert (
        "ORION"
        not in documents_b[
            0
        ].content
    )