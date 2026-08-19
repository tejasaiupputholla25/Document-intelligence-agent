import hashlib

from pathlib import Path

from fastapi import (
    HTTPException,
    UploadFile,
)

from app.config import (
    BASE_DIR,
)


# =========================================================
# UPLOAD LOCATION
# =========================================================

UPLOAD_ROOT = (
    BASE_DIR
    / "uploads"
    / "api"
)


UPLOAD_ROOT.mkdir(
    parents=True,
    exist_ok=True,
)


# =========================================================
# SIZE LIMIT
# =========================================================

MAX_FILE_SIZE_MB = 20


MAX_FILE_SIZE_BYTES = (
    MAX_FILE_SIZE_MB
    * 1024
    * 1024
)


# =========================================================
# SAVE UPLOAD
# =========================================================

def save_upload(
    upload_file: UploadFile,
    allowed_extensions: set[str],
    session_id: str,
) -> tuple[
    Path,
    str,
    str,
]:
    """
    Validate and save a file into:

    uploads/api/<session_id>/

    Returns:

    saved_path
    sha256
    safe_file_name
    """

    # -----------------------------------------------------
    # FILENAME
    # -----------------------------------------------------

    if not upload_file.filename:

        raise HTTPException(
            status_code=400,
            detail=(
                "Uploaded file does not "
                "have a filename."
            ),
        )


    safe_file_name = (
        Path(
            upload_file.filename
        )
        .name
    )


    # -----------------------------------------------------
    # EXTENSION
    # -----------------------------------------------------

    extension = (
        Path(
            safe_file_name
        )
        .suffix
        .lower()
    )


    if extension not in (
        allowed_extensions
    ):

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
    # READ FILE
    # -----------------------------------------------------

    file_bytes = (
        upload_file
        .file
        .read()
    )


    if not file_bytes:

        raise HTTPException(
            status_code=400,
            detail=(
                "Uploaded file is empty."
            ),
        )


    # -----------------------------------------------------
    # SIZE
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
    # HASH
    # -----------------------------------------------------

    file_hash = (
        hashlib
        .sha256(
            file_bytes
        )
        .hexdigest()
    )


    # -----------------------------------------------------
    # SESSION DIRECTORY
    # -----------------------------------------------------

    session_directory = (
        UPLOAD_ROOT
        / str(
            session_id
        )
    )


    session_directory.mkdir(
        parents=True,
        exist_ok=True,
    )


    # -----------------------------------------------------
    # STORED NAME
    # -----------------------------------------------------

    stored_file_name = (
        f"{file_hash[:12]}_"
        f"{safe_file_name}"
    )


    saved_path = (
        session_directory
        / stored_file_name
    )


    saved_path.write_bytes(
        file_bytes
    )


    return (
        saved_path.resolve(),
        file_hash,
        safe_file_name,
    )