from app.document_processing import (
    process_pdf,
)

from app.semantic_search import (
    index_documents,
)

from app.agent import (
    run_document_agent,
)


def main():

    file_path = "data/sample.pdf"

    print(
        f"\nProcessing document: {file_path}"
    )

    # --------------------------------
    # PHASE 2
    # PDF -> chunks
    # --------------------------------

    chunks = process_pdf(
        file_path
    )

    print(
        f"Chunks created: {len(chunks)}"
    )

    # --------------------------------
    # PHASE 3
    # chunks -> embeddings -> store
    # --------------------------------

    index_documents(
        chunks
    )

    print(
        "Document indexed successfully."
    )

    # --------------------------------
    # PHASE 5
    # Agent
    # --------------------------------

    print(
        "\nDocument Intelligence Agent is ready."
    )

    while True:

        question = input(
            "\nAsk a question "
            "(or type 'exit'): "
        )

        if question.lower() == "exit":

            print(
                "\nExiting Document Intelligence Agent."
            )

            break

        answer = run_document_agent(
            question
        )

        print(
            "\n" + "=" * 80
        )

        print(
            "\nAGENT ANSWER:\n"
        )

        print(
            answer
        )

        print(
            "\n" + "=" * 80
        )


if __name__ == "__main__":
    main()