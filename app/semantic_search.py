from app import config

from haystack import Document

from haystack.document_stores.types import (
    DuplicatePolicy,
)

from haystack_integrations.components.embedders.sentence_transformers import (
    SentenceTransformersDocumentEmbedder,
    SentenceTransformersTextEmbedder,
)

from haystack_integrations.document_stores.pgvector import (
    PgvectorDocumentStore,
)

from haystack_integrations.components.retrievers.pgvector import (
    PgvectorEmbeddingRetriever,
)


# =========================================================
# EMBEDDING CONFIGURATION
# =========================================================

EMBEDDING_MODEL = (
    "sentence-transformers/all-mpnet-base-v2"
)

EMBEDDING_DIMENSION = 768


# =========================================================
# PGVECTOR DOCUMENT STORE
# =========================================================

document_store = PgvectorDocumentStore(

    table_name="haystack_documents",

    embedding_dimension=
        EMBEDDING_DIMENSION,

    vector_function=
        "cosine_similarity",

    recreate_table=False,

    search_strategy=
        "exact_nearest_neighbor",

    create_extension=False,
)


# =========================================================
# EMBEDDERS
# =========================================================

document_embedder = (
    SentenceTransformersDocumentEmbedder(
        model=EMBEDDING_MODEL
    )
)


text_embedder = (
    SentenceTransformersTextEmbedder(
        model=EMBEDDING_MODEL
    )
)


# =========================================================
# RETRIEVER
# =========================================================

retriever = PgvectorEmbeddingRetriever(
    document_store=document_store
)


# =========================================================
# FILTER BUILDERS
# =========================================================

def build_session_filter(
    session_id: str,
) -> dict:
    """
    Create a Haystack metadata filter that
    only allows documents belonging to one
    application session.
    """

    return {
        "operator": "AND",

        "conditions": [
            {
                "field":
                    "meta.session_id",

                "operator":
                    "==",

                "value":
                    str(session_id),
            }
        ],
    }


def build_document_filter(
    session_id: str,
    document_id: str,
) -> dict:
    """
    Filter one specific document
    belonging to one specific session.
    """

    return {
        "operator": "AND",

        "conditions": [

            {
                "field":
                    "meta.session_id",

                "operator":
                    "==",

                "value":
                    str(session_id),
            },

            {
                "field":
                    "meta.document_id",

                "operator":
                    "==",

                "value":
                    str(document_id),
            },
        ],
    }


# =========================================================
# INDEX DOCUMENTS
# =========================================================

def index_documents(
    documents,
    session_id: str,
    document_id: str,
    source_file: str,
):
    """
    Embed and persist document chunks while
    attaching session-specific metadata.

    Each stored Haystack Document receives:

    session_id
    document_id
    source_file
    chunk_index
    """

    if not documents:

        return []


    session_id = str(
        session_id
    )

    document_id = str(
        document_id
    )


    # -----------------------------------------------------
    # CREATE SESSION-SCOPED DOCUMENTS
    # -----------------------------------------------------

    scoped_documents = []


    for index, document in enumerate(
        documents
    ):

        metadata = dict(
            document.meta or {}
        )


        metadata.update(
            {
                "session_id":
                    session_id,

                "document_id":
                    document_id,

                "source_file":
                    source_file,

                "chunk_index":
                    index,
            }
        )


        # -------------------------------------------------
        # Important:
        #
        # The ID contains document_id.
        #
        # This means identical chunks uploaded by
        # different sessions will not overwrite
        # each other.
        # -------------------------------------------------

        scoped_document = Document(

            id=(
                f"{document_id}:"
                f"{index}"
            ),

            content=(
                document.content
                or ""
            ),

            meta=
                metadata,
        )


        scoped_documents.append(
            scoped_document
        )


    # -----------------------------------------------------
    # EMBED DOCUMENTS
    # -----------------------------------------------------

    document_embedder.warm_up()


    embedding_result = (
        document_embedder.run(
            documents=
                scoped_documents
        )
    )


    embedded_documents = (
        embedding_result[
            "documents"
        ]
    )


    # -----------------------------------------------------
    # PERSIST TO POSTGRESQL + PGVECTOR
    # -----------------------------------------------------

    document_store.write_documents(

        embedded_documents,

        policy=
            DuplicatePolicy.OVERWRITE,
    )


    return embedded_documents


# =========================================================
# SEARCH DOCUMENTS
# =========================================================

def search_documents(
    query: str,
    session_id: str,
    top_k: int = 3,
    score_threshold: float = 0.30,
):
    """
    Search only the PDF/document chunks
    belonging to the supplied session.
    """

    query = (
        query.strip()
    )


    if not query:

        return []


    if not session_id:

        raise ValueError(
            "session_id is required "
            "for document retrieval."
        )


    # -----------------------------------------------------
    # QUERY EMBEDDING
    # -----------------------------------------------------

    text_embedder.warm_up()


    query_result = (
        text_embedder.run(
            text=query
        )
    )


    query_embedding = (
        query_result[
            "embedding"
        ]
    )


    # -----------------------------------------------------
    # SESSION FILTER
    # -----------------------------------------------------

    filters = (
        build_session_filter(
            session_id
        )
    )


    # -----------------------------------------------------
    # PGVECTOR SEARCH
    # -----------------------------------------------------

    retrieval_result = (
        retriever.run(

            query_embedding=
                query_embedding,

            filters=
                filters,

            top_k=
                top_k,
        )
    )


    documents = (
        retrieval_result[
            "documents"
        ]
    )


    # -----------------------------------------------------
    # SCORE FILTER
    # -----------------------------------------------------

    return [

        document

        for document
        in documents

        if (
            document.score
            is not None

            and

            document.score
            >= score_threshold
        )
    ]


# =========================================================
# GET SESSION DOCUMENTS
# =========================================================

def get_session_documents(
    session_id: str,
):
    """
    Return every stored chunk belonging
    to one session.
    """

    if not session_id:

        return []


    return (
        document_store.filter_documents(

            filters=
                build_session_filter(
                    session_id
                )
        )
    )


# =========================================================
# SESSION CHUNK COUNT
# =========================================================

def get_session_document_count(
    session_id: str,
) -> int:

    documents = (
        get_session_documents(
            session_id
        )
    )


    return len(
        documents
    )


# =========================================================
# GET ONE DOCUMENT'S CHUNKS
# =========================================================

def get_document_chunks(
    session_id: str,
    document_id: str,
):

    return (
        document_store.filter_documents(

            filters=
                build_document_filter(

                    session_id=
                        session_id,

                    document_id=
                        document_id,
                )
        )
    )


# =========================================================
# DELETE ONE DOCUMENT
# =========================================================

def delete_document_chunks(
    session_id: str,
    document_id: str,
) -> None:
    """
    Delete only one document's chunks.
    """

    documents = (
        get_document_chunks(

            session_id=
                session_id,

            document_id=
                document_id,
        )
    )


    if not documents:

        return


    document_ids = [

        document.id

        for document
        in documents
    ]


    document_store.delete_documents(
        document_ids
    )


# =========================================================
# DELETE ONE SESSION'S DOCUMENTS
# =========================================================

def delete_session_documents(
    session_id: str,
) -> None:
    """
    Delete only chunks belonging to
    one application session.
    """

    documents = (
        get_session_documents(
            session_id
        )
    )


    if not documents:

        return


    document_ids = [

        document.id

        for document
        in documents
    ]


    document_store.delete_documents(
        document_ids
    )


# =========================================================
# TOTAL DOCUMENT COUNT
# =========================================================

def get_document_count() -> int:
    """
    Development/debugging helper.

    Counts all stored chunks from all sessions.
    """

    return (
        document_store.count_documents()
    )


# =========================================================
# LEGACY GLOBAL CLEAR
# =========================================================

def clear_document_store() -> None:
    """
    Global deletion is intentionally disabled
    after Phase 9C.

    Use delete_session_documents() or
    delete_document_chunks() instead.
    """

    raise RuntimeError(
        "Global document-store clearing is disabled "
        "in session-aware mode. "
        "Use delete_session_documents(session_id) "
        "or delete_document_chunks(session_id, document_id)."
    )