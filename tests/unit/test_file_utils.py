from io import BytesIO

import pytest

from fastapi import (
    HTTPException,
    UploadFile,
)

import app.api.file_utils as file_utils


# =========================================================
# HELPER
# =========================================================

def make_upload(
    filename: str,
    content: bytes,
):

    return UploadFile(

        filename=
            filename,

        file=
            BytesIO(
                content
            ),
    )


# =========================================================
# VALID PDF
# =========================================================

def test_valid_pdf_is_saved(
    tmp_path,
    monkeypatch,
):

    monkeypatch.setattr(
        file_utils,
        "UPLOAD_ROOT",
        tmp_path,
    )


    upload = make_upload(

        "sample.pdf",

        (
            b"%PDF-1.4\n"
            b"1 0 obj\n"
            b"<<>>\n"
            b"endobj\n"
            b"%%EOF"
        ),
    )


    saved_path, file_hash, safe_name = (
        file_utils.save_upload(

            upload_file=
                upload,

            allowed_extensions={
                ".pdf"
            },

            session_id=
                "test-session",
        )
    )


    assert saved_path.exists()

    assert safe_name == (
        "sample.pdf"
    )

    assert len(
        file_hash
    ) == 64


# =========================================================
# FAKE PDF
# =========================================================

def test_fake_pdf_is_rejected(
    tmp_path,
    monkeypatch,
):

    monkeypatch.setattr(
        file_utils,
        "UPLOAD_ROOT",
        tmp_path,
    )


    upload = make_upload(

        "malicious.pdf",

        b"This is not actually a PDF.",
    )


    with pytest.raises(
        HTTPException
    ) as error:

        file_utils.save_upload(

            upload_file=
                upload,

            allowed_extensions={
                ".pdf"
            },

            session_id=
                "test-session",
        )


    assert (
        error.value.status_code
        == 400
    )


# =========================================================
# PATH TRAVERSAL
# =========================================================

def test_filename_path_is_removed(
    tmp_path,
    monkeypatch,
):

    monkeypatch.setattr(
        file_utils,
        "UPLOAD_ROOT",
        tmp_path,
    )


    upload = make_upload(

        "../../evil.pdf",

        (
            b"%PDF-1.4\n"
            b"%%EOF"
        ),
    )


    saved_path, _, safe_name = (
        file_utils.save_upload(

            upload_file=
                upload,

            allowed_extensions={
                ".pdf"
            },

            session_id=
                "abc",
        )
    )


    assert (
        safe_name
        == "evil.pdf"
    )


    assert (
        saved_path.parent
        == (
            tmp_path
            / "abc"
        )
    )


# =========================================================
# SIZE LIMIT
# =========================================================

def test_large_file_is_rejected(
    tmp_path,
    monkeypatch,
):

    monkeypatch.setattr(
        file_utils,
        "UPLOAD_ROOT",
        tmp_path,
    )


    monkeypatch.setattr(
        file_utils,
        "MAX_FILE_SIZE_BYTES",
        10,
    )


    upload = make_upload(

        "large.pdf",

        (
            b"%PDF-1.4\n"
            b"12345678901234567890"
        ),
    )


    with pytest.raises(
        HTTPException
    ) as error:

        file_utils.save_upload(

            upload_file=
                upload,

            allowed_extensions={
                ".pdf"
            },

            session_id=
                "test",
        )


    assert (
        error.value.status_code
        == 413
    )


# =========================================================
# BINARY CSV
# =========================================================

def test_binary_csv_is_rejected(
    tmp_path,
    monkeypatch,
):

    monkeypatch.setattr(
        file_utils,
        "UPLOAD_ROOT",
        tmp_path,
    )


    upload = make_upload(

        "fake.csv",

        b"\x00\x01\x02\x03",
    )


    with pytest.raises(
        HTTPException
    ):

        file_utils.save_upload(

            upload_file=
                upload,

            allowed_extensions={
                ".csv"
            },

            session_id=
                "test",
        )