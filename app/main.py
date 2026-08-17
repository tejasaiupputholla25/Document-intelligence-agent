from app.document_processing import (
    process_pdf,
)

from app.semantic_search import (
    index_documents,
)

from app.rag import (
    ask_document,
)


def main():

    file_path = "data/sample.pdf"

    print(
        f"\nProcessing document: {file_path}"
    )

    # ---------------------------------
    # PHASE 2
    # PDF → chunks
    # ---------------------------------

    chunks = process_pdf(
        file_path
    )

    print(
        f"Chunks created: {len(chunks)}"
    )

    # ---------------------------------
    # PHASE 3
    # chunks → embeddings → vector store
    # ---------------------------------

    index_documents(
        chunks
    )

    print(
        "Document indexed successfully."
    )

    # ---------------------------------
    # PHASE 4
    # RAG question answering
    # ---------------------------------

    while True:

        question = input(
            "\nAsk a question "
            "(or type 'exit'): "
        )

        if question.lower() == "exit":

            print(
                "\nExiting document Q&A."
            )

            break

        result = ask_document(
            question=question,
            top_k=3,
        )

        print(
            "\n" + "=" * 80
        )

        print(
            "\nANSWER:\n"
        )

        print(
            result["answer"]
        )

        print(
            "\nSOURCES:\n"
        )

        for index, document in enumerate(
            result["documents"],
            start=1,
        ):

            print(
                f"SOURCE {index}"
            )

            print(
                f"Score: "
                f"{document.score}"
            )

            print(
                f"Metadata: "
                f"{document.meta}"
            )

            print(
                "\nContent Preview:"
            )

            print(
                (document.content or "")[
                    :300
                ]
            )

            print(
                "\n" + "-" * 60
            )


if __name__ == "__main__":
    main()