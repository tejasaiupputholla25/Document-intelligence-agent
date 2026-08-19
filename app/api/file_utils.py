import hashlib

from pathlib import Path

from fastapi import (
    HTTPException,
    UploadFile,
)


# =========================================================
# SETTINGS
# =========================================================

UPLOAD_DIRECTORY = (
    Path("uploads")
    / "api"
)


UPLOAD_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)


MAX_FILE_SIZE_MB = 20


MAX_FILE_SIZE_BYTES = (
    MAX_FILE_SIZE_MB
    * 1024
    * 1024
)


# =========================================================
# SAVE FILE
# =========================================================

def save_upload(
    upload_file: UploadFile,
    allowed_extensions: set[str],
) -> tuple[Path, str]:
    """
    Validate and save an uploaded file.

    Returns:

    saved_path
    file_hash
    """

    # -----------------------------------------------------
    # Validate filename
    # -----------------------------------------------------

    if not upload_file.filename:

        raise HTTPException(
            status_code=400,
            detail=(
                "Uploaded file does not "
                "have a filename."
            ),
        )


    # -----------------------------------------------------
    # Strip path information
    #
    # ../../../something.pdf
    #
    # becomes:
    #
    # something.pdf
    # -----------------------------------------------------

    safe_file_name = Path(
        upload_file.filename
    ).name


    extension = (
        Path(
            safe_file_name
        )
        .suffix
        .lower()
    )


    # -----------------------------------------------------
    # Validate extension
    # -----------------------------------------------------

    if extension not in allowed_extensions:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type "
                f"'{extension}'. "
                f"Allowed types: "
                f"{sorted(allowed_extensions)}"
            ),
        )


    # -----------------------------------------------------
    # Read uploaded bytes
    # -----------------------------------------------------

    file_bytes = (
        upload_file
        .file
        .read()
    )


    # -----------------------------------------------------
    # Validate empty file
    # -----------------------------------------------------

    if not file_bytes:

        raise HTTPException(
            status_code=400,
            detail=(
                "Uploaded file is empty."
            ),
        )


    # -----------------------------------------------------
    # Validate size
    # -----------------------------------------------------

    if (
        len(file_bytes)
        > MAX_FILE_SIZE_BYTES
    ):

        raise HTTPException(
            status_code=413,
            detail=(
                f"File exceeds the "
                f"{MAX_FILE_SIZE_MB} MB limit."
            ),
        )


    # -----------------------------------------------------
    # Calculate hash
    # -----------------------------------------------------

    file_hash = (
        hashlib
        .sha256(
            file_bytes
        )
        .hexdigest()
    )


    # -----------------------------------------------------
    # Unique filename
    # -----------------------------------------------------

    stored_file_name = (
        f"{file_hash[:12]}_"
        f"{safe_file_name}"
    )


    saved_path = (
        UPLOAD_DIRECTORY
        / stored_file_name
    )


    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    saved_path.write_bytes(
        file_bytes
    )


    return (
        saved_path,
        file_hash,
    )