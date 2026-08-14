from app.config import HF_TOKEN


#from app.semantic_search import test_embedding


from app.document_processing import process_pdf

from app.semantic_search import (
    index_documents,
    search_documents,
)


def main():

    file_path = "data/sample.pdf"

    print(
        f"\nProcessing document: {file_path}"
    )

    # PHASE 2
    chunks = process_pdf(
        file_path
    )

    print(
        f"Chunks created: {len(chunks)}"
    )

    # PHASE 3 - Index
    embedded_documents = index_documents(
        chunks
    )

    print(
        f"Documents indexed: "
        f"{len(embedded_documents)}"
    )

    print(
        "Embedding dimension:",
        len(
            embedded_documents[0].embedding
        ),
    )

    # User question
    query = input(
        "\nAsk a question about the document: "
    )

    # PHASE 3 - Retrieve
    retrieved_documents = search_documents(
        query=query,
        top_k=3,
    )

    print(
        "\nMOST RELEVANT CHUNKS:"
    )

    for index, document in enumerate(
        retrieved_documents,
        start=1,
    ):

        print(
            "\n" + "=" * 80
        )

        print(
            f"RESULT {index}"
        )

        print(
            f"Similarity score: "
            f"{document.score}"
        )

        print(
            f"Metadata: "
            f"{document.meta}"
        )

        print(
            "\nCONTENT:\n"
        )

        print(
            document.content
        )


if __name__ == "__main__":
    main()