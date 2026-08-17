from typing import Annotated

from haystack.tools import tool

from app.semantic_search import (
    search_documents,
    document_store,
)


@tool
def search_document(
    query: Annotated[
        str,
        "Question or topic to search for inside the uploaded document."
    ],
    top_k: Annotated[
        int,
        "Maximum number of relevant document chunks to return."
    ] = 3,
) -> dict:
    """
    Search the uploaded document for information
    relevant to a question or topic.

    Use this tool whenever the user asks about the
    contents of the uploaded document.
    """

    print(
        f"\n[TOOL EXECUTED] search_document"
        f"\nQuery: {query}\n"
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
                "source": index,
                "content": document.content or "",
                "score": document.score,
                "metadata": document.meta,
            }
        )

    return {
        "query": query,
        "result_count": len(results),
        "results": results,
    }


@tool
def get_document_info() -> dict:
    """
    Get basic information about the currently
    indexed document.

    Use this tool when the user asks about
    document size, number of indexed chunks,
    or available document metadata.
    """

    print(
        "\n[TOOL EXECUTED] get_document_info\n"
    )

    documents = document_store.filter_documents()

    metadata_examples = [
        document.meta
        for document in documents[:3]
    ]

    return {
        "indexed_chunk_count": len(documents),
        "metadata_examples": metadata_examples,
    }