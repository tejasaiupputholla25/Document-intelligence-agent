from app.config import HF_TOKEN

from app.document_processing import process_pdf


def main():

    file_path = "data/sample.pdf"
    #file_path = "data/does_not_exist.pdf"

    print(
        f"\nProcessing: {file_path}"
    )

    chunks = process_pdf(
        file_path
    )

    print(
        "\nDocument processing completed."
    )

    print(
        f"Total chunks: {len(chunks)}"
    )

    for index, chunk in enumerate(
        chunks[:3],
        start=1
    ):

        content = chunk.content or ""

        print("\n" + "=" * 80)

        print(
            f"CHUNK {index}"
        )

        print(
            f"Words: {len(content.split())}"
        )

        print(
            f"Metadata: {chunk.meta}"
        )

        print("\nCONTENT:\n")

        print(content)


if __name__ == "__main__":
    main()