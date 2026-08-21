import hashlib
import os
import zipfile

from pathlib import Path
from uuid import uuid4

from fastapi import (
    HTTPException,
    UploadFile,
)

from app.config import (
    BASE_DIR,
)


# =========================================================
# UPLOAD DIRECTORY
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
# LIMITS
# =========================================================

MAX_FILE_SIZE_MB = 20

MAX_FILE_SIZE_BYTES = (
    MAX_FILE_SIZE_MB
    * 1024
    * 1024
)


# Read uploads progressively instead
# of loading the entire file into memory.

UPLOAD_CHUNK_SIZE = (
    1024
    * 1024
)


# Protect against very large decompressed
# XLSX ZIP contents.

MAX_XLSX_UNCOMPRESSED_MB = 100

MAX_XLSX_UNCOMPRESSED_BYTES = (
    MAX_XLSX_UNCOMPRESSED_MB
    * 1024
    * 1024
)


# =========================================================
# SAFE FILE NAME
# =========================================================

def _safe_file_name(
    filename: str,
) -> str:

    # Normalize Windows and Unix path separators.

    normalized = (
        filename
        .replace("\\", "/")
    )


    safe_name = (
        Path(normalized)
        .name
        .strip()
    )


    if (
        not safe_name

        or

        safe_name in {
            ".",
            "..",
        }
    ):

        raise HTTPException(
            status_code=400,
            detail="Invalid filename.",
        )


    return safe_name


# =========================================================
# PDF VALIDATION
# =========================================================

def _validate_pdf(
    file_path: Path,
) -> None:

    with file_path.open(
        "rb"
    ) as file:

        header = file.read(
            8
        )


    if not header.startswith(
        b"%PDF-"
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "The uploaded file does not "
                "appear to be a valid PDF."
            ),
        )


# =========================================================
# CSV VALIDATION
# =========================================================

def _validate_csv(
    file_path: Path,
) -> None:

    with file_path.open(
        "rb"
    ) as file:

        sample = file.read(
            8192
        )


    # Null bytes strongly suggest a binary file.

    if b"\x00" in sample:

        raise HTTPException(
            status_code=400,
            detail=(
                "The uploaded CSV appears "
                "to contain binary data."
            ),
        )


    try:

        sample.decode(
            "utf-8-sig"
        )


    except UnicodeDecodeError as error:

        raise HTTPException(
            status_code=400,
            detail=(
                "CSV files must be UTF-8 encoded."
            ),
        ) from error


# =========================================================
# XLSX VALIDATION
# =========================================================

def _validate_xlsx(
    file_path: Path,
) -> None:

    if not zipfile.is_zipfile(
        file_path
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "The uploaded file does not "
                "appear to be a valid XLSX file."
            ),
        )


    try:

        with zipfile.ZipFile(
            file_path
        ) as archive:

            names = set(
                archive.namelist()
            )


            required_files = {
                "[Content_Types].xml",
                "xl/workbook.xml",
            }


            if not required_files.issubset(
                names
            ):

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "The uploaded ZIP file "
                        "is not a valid XLSX workbook."
                    ),
                )


            total_uncompressed_size = sum(

                item.file_size

                for item
                in archive.infolist()
            )


            if (
                total_uncompressed_size
                > MAX_XLSX_UNCOMPRESSED_BYTES
            ):

                raise HTTPException(
                    status_code=413,
                    detail=(
                        "The XLSX workbook expands "
                        "beyond the allowed size."
                    ),
                )


    except zipfile.BadZipFile as error:

        raise HTTPException(
            status_code=400,
            detail=(
                "The XLSX workbook is corrupted."
            ),
        ) from error


# =========================================================
# CONTENT VALIDATION
# =========================================================

def _validate_file_content(
    file_path: Path,
    extension: str,
) -> None:

    if extension == ".pdf":

        _validate_pdf(
            file_path
        )


    elif extension == ".csv":

        _validate_csv(
            file_path
        )


    elif extension == ".xlsx":

        _validate_xlsx(
            file_path
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

    if not upload_file.filename:

        raise HTTPException(
            status_code=400,
            detail=(
                "Uploaded file does not "
                "have a filename."
            ),
        )


    safe_name = (
        _safe_file_name(
            upload_file.filename
        )
    )


    extension = (
        Path(
            safe_name
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


    # =====================================================
    # SESSION DIRECTORY
    # =====================================================

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


    # =====================================================
    # TEMPORARY FILE
    # =====================================================

    temporary_path = (
        session_directory
        / (
            f".upload-"
            f"{uuid4().hex}.part"
        )
    )


    sha256 = hashlib.sha256()

    total_size = 0


    try:

        with temporary_path.open(
            "wb"
        ) as destination:

            while True:

                chunk = (
                    upload_file
                    .file
                    .read(
                        UPLOAD_CHUNK_SIZE
                    )
                )


                if not chunk:

                    break


                total_size += (
                    len(chunk)
                )


                if (
                    total_size
                    > MAX_FILE_SIZE_BYTES
                ):

                    raise HTTPException(
                        status_code=413,
                        detail=(
                            f"File exceeds the "
                            f"{MAX_FILE_SIZE_MB} MB limit."
                        ),
                    )


                sha256.update(
                    chunk
                )


                destination.write(
                    chunk
                )


        # =================================================
        # EMPTY FILE
        # =================================================

        if total_size == 0:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Uploaded file is empty."
                ),
            )


        # =================================================
        # CONTENT SIGNATURE CHECK
        # =================================================

        _validate_file_content(

            file_path=
                temporary_path,

            extension=
                extension,
        )


        file_hash = (
            sha256.hexdigest()
        )


        stored_file_name = (
            f"{file_hash[:12]}_"
            f"{safe_name}"
        )


        saved_path = (
            session_directory
            / stored_file_name
        )


        # Atomic move/replace inside same filesystem.

        os.replace(
            temporary_path,
            saved_path,
        )


        return (
            saved_path.resolve(),
            file_hash,
            safe_name,
        )


    except Exception:

        temporary_path.unlink(
            missing_ok=True
        )

        raise