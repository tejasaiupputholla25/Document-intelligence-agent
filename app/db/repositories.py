from uuid import UUID

from sqlalchemy import (
    select,
)

from app.db.database import (
    SessionLocal,
)

from app.db.models import (
    ChatMessageRecord,
    DatasetRecord,
    DocumentRecord,
    SessionRecord,
)


# =========================================================
# SESSION REPOSITORY
# =========================================================

def create_session() -> SessionRecord:

    with SessionLocal() as database:

        record = SessionRecord()

        database.add(
            record
        )

        database.commit()

        database.refresh(
            record
        )

        return record


def get_session(
    session_id: UUID,
) -> SessionRecord | None:

    with SessionLocal() as database:

        return database.get(
            SessionRecord,
            session_id,
        )


# =========================================================
# DOCUMENT REPOSITORY
# =========================================================

def create_document(
    document: DocumentRecord,
) -> DocumentRecord:

    with SessionLocal() as database:

        database.add(
            document
        )

        database.commit()

        database.refresh(
            document
        )

        return document


def get_latest_document(
    session_id: UUID,
) -> DocumentRecord | None:

    with SessionLocal() as database:

        statement = (

            select(
                DocumentRecord
            )

            .where(
                DocumentRecord.session_id
                == session_id
            )

            .order_by(
                DocumentRecord.created_at.desc()
            )

            .limit(1)
        )


        return (
            database
            .scalars(
                statement
            )
            .first()
        )


# =========================================================
# DATASET REPOSITORY
# =========================================================

def create_dataset(
    dataset: DatasetRecord,
) -> DatasetRecord:

    with SessionLocal() as database:

        database.add(
            dataset
        )

        database.commit()

        database.refresh(
            dataset
        )

        return dataset


def get_latest_dataset(
    session_id: UUID,
) -> DatasetRecord | None:

    with SessionLocal() as database:

        statement = (

            select(
                DatasetRecord
            )

            .where(
                DatasetRecord.session_id
                == session_id
            )

            .order_by(
                DatasetRecord.created_at.desc()
            )

            .limit(1)
        )


        return (
            database
            .scalars(
                statement
            )
            .first()
        )


# =========================================================
# CHAT REPOSITORY
# =========================================================

def save_chat_message(
    session_id: UUID,
    role: str,
    content: str,
) -> ChatMessageRecord:

    with SessionLocal() as database:

        message = ChatMessageRecord(

            session_id=
                session_id,

            role=
                role,

            content=
                content,
        )


        database.add(
            message
        )

        database.commit()

        database.refresh(
            message
        )


        return message


def get_chat_messages(
    session_id: UUID,
) -> list[ChatMessageRecord]:

    with SessionLocal() as database:

        statement = (

            select(
                ChatMessageRecord
            )

            .where(
                ChatMessageRecord.session_id
                == session_id
            )

            .order_by(
                ChatMessageRecord.created_at.asc()
            )
        )


        return list(

            database.scalars(
                statement
            )
        )