"""All database access: plain SQL with psycopg, vectors stored with pgvector."""
import psycopg

import config


def connect():
    return psycopg.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        autocommit=True,
    )


def to_vector(values: list[float]) -> str:
    """pgvector accepts a text literal like '[0.1,0.2,...]'."""
    return "[" + ",".join(str(v) for v in values) + "]"


def init_schema(conn):
    """Create the extension and table, and empty the table for a fresh load."""
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chunks (
            id            SERIAL PRIMARY KEY,
            source        TEXT NOT NULL,
            doc_type      TEXT NOT NULL,
            owner_user_id TEXT,              -- set only for customer records
            content       TEXT NOT NULL,
            embedding     vector(768) NOT NULL
        )
        """
    )
    conn.execute("TRUNCATE chunks RESTART IDENTITY")


def insert_chunk(conn, source, doc_type, owner_user_id, content, embedding):
    conn.execute(
        "INSERT INTO chunks (source, doc_type, owner_user_id, content, embedding) "
        "VALUES (%s, %s, %s, %s, %s::vector)",
        (source, doc_type, owner_user_id, content, to_vector(embedding)),
    )


def search(query_embedding: list[float], k: int, user_id: str | None = None):
    """Return the k closest chunks by cosine distance (<=>).

    If user_id is given (guardrails ON), only shared policy chunks and the
    caller's own customer record can be returned. If it is None (guardrails
    OFF), every chunk is searchable - including other customers' records.
    """
    sql = "SELECT source, doc_type, owner_user_id, content FROM chunks "
    params: list = []
    if user_id is not None:
        sql += "WHERE owner_user_id IS NULL OR owner_user_id = %s "
        params.append(user_id)
    sql += "ORDER BY embedding <=> %s::vector LIMIT %s"
    params += [to_vector(query_embedding), k]

    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [
        {"source": r[0], "doc_type": r[1], "owner_user_id": r[2], "content": r[3]}
        for r in rows
    ]
