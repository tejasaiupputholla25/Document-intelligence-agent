from haystack.document_stores.in_memory import (
    InMemoryDocumentStore,
)

from haystack.components.embedders import (
    SentenceTransformersDocumentEmbedder,
    SentenceTransformersTextEmbedder,
)

from haystack.components.retrievers.in_memory import (
    InMemoryEmbeddingRetriever,
)


EMBEDDING_MODEL = (
    "sentence-transformers/all-mpnet-base-v2"
)


# Create the temporary vector/document store
document_store = InMemoryDocumentStore(
    embedding_similarity_function="cosine"
)


# Converts document chunks into vectors
document_embedder = SentenceTransformersDocumentEmbedder(
    model=EMBEDDING_MODEL
)


# Converts user questions into vectors
text_embedder = SentenceTransformersTextEmbedder(
    model=EMBEDDING_MODEL
)


# Searches the document store using embeddings
retriever = InMemoryEmbeddingRetriever(
    document_store=document_store
)



def index_documents(documents):
    """
    Create embeddings for document chunks and
    store them in the document store.
    """

    document_embedder.warm_up()

    result = document_embedder.run(
        documents=documents
    )

    embedded_documents = result["documents"]

    document_store.write_documents(
        embedded_documents
    )

    return embedded_documents

def search_documents(
    query: str,
    top_k: int = 3,
):
    """
    Search for document chunks that are
    semantically related to the query.
    """

    text_embedder.warm_up()

    query_result = text_embedder.run(
        text=query
    )

    query_embedding = query_result["embedding"]

    result = retriever.run(
        query_embedding=query_embedding,
        top_k=top_k,
    )

    return result["documents"]