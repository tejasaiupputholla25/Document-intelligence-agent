import hashlib

from pathlib import Path


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


from app.db.models import (
    DatasetRecord,
    DocumentRecord,
)

from app.db.repositories import (
    create_dataset,
    create_document,
    create_session,
)


# =========================================================
# DEVELOPMENT FILES
# =========================================================

PDF_PATH = Path(
    "data/sample.pdf"
)


DATASET_PATH = Path(
    "data/sample_sales.csv"
)


# =========================================================
# FILE HASH
# =========================================================

def calculate_sha256(
    file_path: Path,
) -> str:

    sha256 = hashlib.sha256()


    with file_path.open(
        "rb"
    ) as file:

        for chunk in iter(
            lambda:
                file.read(
                    1024 * 1024
                ),
            b"",
        ):

            sha256.update(
                chunk
            )


    return sha256.hexdigest()


# =========================================================
# MAIN
# =========================================================

def main():

    print(
        "\n" + "=" * 80
    )

    print(
        "DOCUMENT INTELLIGENCE AGENT"
    )

    print(
        "PHASE 9C - SESSION-AWARE CLI"
    )

    print(
        "=" * 80
    )


    # =====================================================
    # CREATE APPLICATION SESSION
    # =====================================================

    session = (
        create_session()
    )


    session_id = str(
        session.id
    )


    print(
        "\nSession created."
    )

    print(
        f"Session ID: "
        f"{session_id}"
    )


    # =====================================================
    # PDF
    # =====================================================

    if PDF_PATH.exists():

        print(
            "\nProcessing PDF..."
        )


        chunks = (
            process_pdf(
                str(
                    PDF_PATH
                )
            )
        )


        print(
            f"Chunks created: "
            f"{len(chunks)}"
        )


        # -------------------------------------------------
        # Store application metadata first.
        # -------------------------------------------------

        document_record = (
            DocumentRecord(

                session_id=
                    session.id,

                file_name=
                    PDF_PATH.name,

                stored_path=
                    str(
                        PDF_PATH.resolve()
                    ),

                sha256=
                    calculate_sha256(
                        PDF_PATH
                    ),

                chunk_count=
                    len(chunks),

                status=
                    "ready",
            )
        )


        document_record = (
            create_document(
                document_record
            )
        )


        # -------------------------------------------------
        # Store session-tagged vectors
        # -------------------------------------------------

        index_documents(

            documents=
                chunks,

            session_id=
                session_id,

            document_id=
                str(
                    document_record.id
                ),

            source_file=
                PDF_PATH.name,
        )


        print(
            "PDF indexed into "
            "session-aware pgvector storage."
        )


    else:

        print(
            "\nPDF not found:"
        )

        print(
            PDF_PATH
        )


    # =====================================================
    # DATASET
    # =====================================================

    if DATASET_PATH.exists():

        print(
            "\nLoading dataset..."
        )


        data_info = (
            load_structured_data(
                str(
                    DATASET_PATH
                )
            )
        )


        dataset_record = (
            DatasetRecord(

                session_id=
                    session.id,

                file_name=
                    DATASET_PATH.name,

                stored_path=
                    str(
                        DATASET_PATH.resolve()
                    ),

                sha256=
                    calculate_sha256(
                        DATASET_PATH
                    ),

                row_count=
                    data_info[
                        "rows"
                    ],

                column_count=
                    data_info[
                        "columns"
                    ],

                column_names=
                    data_info[
                        "column_names"
                    ],

                status=
                    "ready",
            )
        )


        create_dataset(
            dataset_record
        )


        print(
            "Dataset registered "
            "for this session."
        )

        print(
            f"Rows: "
            f"{data_info['rows']}"
        )

        print(
            f"Columns: "
            f"{data_info['columns']}"
        )


    else:

        print(
            "\nDataset not found:"
        )

        print(
            DATASET_PATH
        )


    # =====================================================
    # CHAT LOOP
    # =====================================================

    print(
        "\n" + "=" * 80
    )

    print(
        "READY"
    )

    print(
        "Type 'exit' to stop."
    )

    print(
        "=" * 80
    )


    while True:

        question = input(
            "\nAsk a question: "
        ).strip()


        if question.lower() in {
            "exit",
            "quit",
        }:

            print(
                "\nGoodbye."
            )

            break


        if not question:

            continue


        try:

            answer = (
                run_document_agent(

                    question=
                        question,

                    session_id=
                        session_id,
                )
            )


            print(
                "\n" + "=" * 80
            )

            print(
                "AGENT ANSWER:"
            )

            print()

            print(
                answer
            )

            print(
                "=" * 80
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