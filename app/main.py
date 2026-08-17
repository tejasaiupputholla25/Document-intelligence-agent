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


def main():

    # =====================================================
    # LOCAL DEVELOPMENT FILES
    # =====================================================

    pdf_path = (
        "data/sample.pdf"
    )

    #structured_file_path = (
    #    "data/sample_data.csv"
    #)
    structured_file_path = (
            "data/sample_data.xlsx"
        )

    # =====================================================
    # PHASE 2 + PHASE 3
    # PROCESS AND INDEX PDF
    # =====================================================

    print(
        "\n" + "=" * 80
    )

    print(
        "DOCUMENT PROCESSING"
    )

    print(
        "=" * 80
    )

    print(
        f"\nProcessing PDF: "
        f"{pdf_path}"
    )


    # -----------------------------------------------------
    # PDF -> chunks
    # -----------------------------------------------------

    chunks = process_pdf(
        pdf_path
    )


    print(
        f"PDF chunks created: "
        f"{len(chunks)}"
    )


    # -----------------------------------------------------
    # chunks -> embeddings -> document store
    # -----------------------------------------------------

    index_documents(
        chunks
    )


    print(
        "PDF indexed successfully."
    )


    # =====================================================
    # PHASE 6
    # LOAD STRUCTURED DATA
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
        f"\nLoading structured data: "
        f"{structured_file_path}"
    )


    data_info = load_structured_data(
        structured_file_path
    )


    print(
        "\nStructured data loaded successfully."
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
        "Column names:"
    )


    for column in data_info[
        "column_names"
    ]:

        print(
            f"  - {column}"
        )


    # =====================================================
    # PHASE 5 + PHASE 6
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
        "\nCurrent capabilities:"
    )


    print(
        "- Search information inside the PDF"
    )

    print(
        "- Inspect PDF document information"
    )

    print(
        "- Inspect CSV/XLSX data"
    )

    print(
        "- Calculate aggregates"
    )

    print(
        "- Perform grouped calculations"
    )

    print(
        "- Filter structured data"
    )


    # =====================================================
    # CHAT LOOP
    # =====================================================

    while True:

        question = input(
            "\nAsk a question "
            "(or type 'exit'): "
        )


        # -------------------------------------------------
        # Exit command
        # -------------------------------------------------

        if question.strip().lower() == "exit":

            print(
                "\nExiting Document "
                "Intelligence Agent."
            )

            break


        # -------------------------------------------------
        # Ignore empty input
        # -------------------------------------------------

        if not question.strip():

            print(
                "Please enter a question."
            )

            continue


        # -------------------------------------------------
        # Send to Agent
        # -------------------------------------------------

        try:

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


        except Exception as error:

            print(
                "\nAn error occurred while "
                "processing your request."
            )


            print(
                f"Error: {error}"
            )


if __name__ == "__main__":

    main()