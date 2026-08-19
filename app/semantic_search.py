from app import config


# =========================================================
# SENTENCE TRANSFORMERS EMBEDDERS
# =========================================================

from haystack_integrations.components.embedders.sentence_transformers import (
    SentenceTransformersDocumentEmbedder,
    SentenceTransformersTextEmbedder,
)


# =========================================================
# HAYSTACK TYPES
# =========================================================

from haystack.document_stores.types import (
    DuplicatePolicy,
)


# =========================================================
# PGVECTOR
# =========================================================

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
# DOCUMENT STORE
# =========================================================

document_store = PgvectorDocumentStore(

    table_name=(
        "haystack_documents"
    ),

    embedding_dimension=(
        EMBEDDING_DIMENSION
    ),

    vector_function=(
        "cosine_similarity"
    ),

    recreate_table=False,

    search_strategy=(
        "exact_nearest_neighbor"
    ),

    create_extension=False,
)


# =========================================================
# DOCUMENT EMBEDDER
# =========================================================

document_embedder = (
    SentenceTransformersDocumentEmbedder(
        model=EMBEDDING_MODEL
    )
)


# =========================================================
# QUERY EMBEDDER
# =========================================================

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
# INDEX DOCUMENTS
# =========================================================

def index_documents(
    documents,
):

    if not documents:
        return []

    document_embedder.warm_up()

    embedding_result = (
        document_embedder.run(
            documents=documents
        )
    )

    embedded_documents = (
        embedding_result[
            "documents"
        ]
    )

    document_store.write_documents(
        embedded_documents,
        policy=DuplicatePolicy.OVERWRITE,
    )

    return embedded_documents


# =========================================================
# SEARCH DOCUMENTS
# =========================================================

def search_documents(
    query: str,
    top_k: int = 3,
    score_threshold: float = 0.30,
):

    query = query.strip()

    if not query:
        return []

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

    retrieval_result = (
        retriever.run(
            query_embedding=
                query_embedding,
            top_k=
                top_k,
        )
    )

    documents = (
        retrieval_result[
            "documents"
        ]
    )

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
# CLEAR DOCUMENT STORE
# =========================================================

def clear_document_store() -> None:

    document_store.delete_all_documents()


# =========================================================
# DOCUMENT COUNT
# =========================================================

def get_document_count() -> int:

    return (
        document_store.count_documents()
    )