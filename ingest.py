"""Load the markdown docs in data/ into Postgres/pgvector.

Usage:
    python ingest.py                        # includes the poisoned doc (default)
    python ingest.py --no-include-poisoned  # clean knowledge base
"""
import argparse
from pathlib import Path

import db
import ollama_client

DATA_DIR = Path(__file__).parent / "data"
POISONED_DOC = "dispute_process_update.md"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def read_doc(path: Path) -> tuple[dict, str]:
    """Split a doc into its front matter (doc_type, owner_user_id) and body text."""
    text = path.read_text()
    _, header, body = text.split("---", 2)
    meta = {}
    for line in header.strip().splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip() or None
    return meta, body.strip()


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Cut text into ~size-char pieces, breaking at a space, with a small overlap."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            space = text.rfind(" ", start, end)
            if space > start:
                end = space
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        "--include-poisoned",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=f"include {POISONED_DOC} (default: on)",
    )
    args = parser.parse_args()

    with db.connect() as conn:
        db.init_schema(conn)
        total = 0
        for path in sorted(DATA_DIR.glob("*.md")):
            if path.name == POISONED_DOC and not args.include_poisoned:
                print(f"skip  {path.name} (poisoned doc excluded)")
                continue
            meta, body = read_doc(path)
            pieces = chunk_text(body)
            for piece in pieces:
                vec = ollama_client.embed("search_document: " + piece)
                db.insert_chunk(conn, path.name, meta["doc_type"], meta.get("owner_user_id"), piece, vec)
            total += len(pieces)
            print(f"load  {path.name:32} {meta['doc_type']:16} {len(pieces)} chunk(s)")
    print(f"\nDone: {total} chunks stored.")


if __name__ == "__main__":
    main()
