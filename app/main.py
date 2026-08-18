from app.document_processing import (
    process_pdf,
)

from app.semantic_search import (
    index_documents,
)

from app.structured_data import (
    load_structured_data,
)

from app.agent import (
    run_document_agent,
)


# =========================================================
# MAIN
# =========================================================

def main():

    # =====================================================
    # LOCAL DEVELOPMENT FILES
    # =====================================================

    pdf_path = (
        "data/sample.pdf"
    )

    structured_file_path = (
        "data/sample_sales.csv"
    )


    # =====================================================
    # PDF PROCESSING
    # =====================================================

    print(
        "\n" + "=" * 80
    )

    print(
        "PDF PROCESSING"
    )

    print(
        "=" * 80
    )

    print(
        f"\nProcessing PDF: "
        f"{pdf_path}"
    )


    # Phase 2
    chunks = process_pdf(
        pdf_path
    )


    print(
        f"PDF chunks created: "
        f"{len(chunks)}"
    )


    # Phase 3
    index_documents(
        chunks
    )


    print(
        "PDF indexed successfully."
    )


    # =====================================================
    # STRUCTURED DATA
    # =====================================================

    print(
        "\n" + "=" * 80
    )

    print(
        "STRUCTURED DATA"
    )

    print(
        "=" * 80
    )


    print(
        f"\nLoading dataset: "
        f"{structured_file_path}"
    )


    data_info = load_structured_data(
        structured_file_path
    )


    print(
        "Dataset loaded successfully."
    )


    print(
        f"File: "
        f"{data_info['file_name']}"
    )


    print(
        f"Rows: "
        f"{data_info['rows']}"
    )


    print(
        f"Columns: "
        f"{data_info['columns']}"
    )


    print(
        "\nColumn names:"
    )


    for column in (
        data_info[
            "column_names"
        ]
    ):

        print(
            f"  - {column}"
        )


    # =====================================================
    # AGENT
    # =====================================================

    print(
        "\n" + "=" * 80
    )

    print(
        "DOCUMENT INTELLIGENCE AGENT"
    )

    print(
        "=" * 80
    )


    print(
        "\nAgent is ready."
    )


    print(
        "\nCapabilities:"
    )


    print(
        "- Search information inside PDF"
    )

    print(
        "- Inspect PDF metadata"
    )

    print(
        "- Inspect CSV/XLSX dataset"
    )

    print(
        "- Calculate aggregations"
    )

    print(
        "- Perform grouped calculations"
    )

    print(
        "- Filter dataset rows"
    )


    # =====================================================
    # QUESTION LOOP
    # =====================================================

    while True:

        question = input(
            "\nAsk a question "
            "(or type 'exit'): "
        )


        question = (
            question.strip()
        )


        if question.lower() == "exit":

            print(
                "\nExiting Document "
                "Intelligence Agent."
            )

            break


        if not question:

            print(
                "Please enter a question."
            )

            continue


        try:

            answer = (
                run_document_agent(
                    question
                )
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


        except Exception as error:

            print(
                "\nAn error occurred."
            )

            print(
                f"Error: {error}"
            )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    main()