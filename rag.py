"""The RAG pipeline: embed question -> retrieve chunks -> build prompt -> ask llama3.1."""
import config
import db
import guardrails
import ollama_client


def build_user_prompt(user_id: str, chunks: list[dict], question: str) -> str:
    context = "\n\n".join(
        f"[Document {i + 1}: {c['source']}]\n{c['content']}" for i, c in enumerate(chunks)
    )
    return (
        f"Caller user_id: {user_id}\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {question}"
    )


def answer(user_id: str, message: str, guardrails_on: bool) -> dict:
    # 1. Input filter (guardrails ON only)
    if guardrails_on and guardrails.check_input(message):
        return {"answer": guardrails.BLOCKED_MESSAGE, "sources": [], "blocked": True}

    # 2. Retrieve: with guardrails ON, restrict to policy docs + the caller's own record
    #    The caller's id is added to the search text so "my card" questions find
    #    the caller's record. With guardrails OFF nothing stops other records matching too.
    query_vec = ollama_client.embed(f"search_query: Customer {user_id} asks: {message}")
    owner_filter = user_id if guardrails_on else None
    chunks = db.search(query_vec, k=config.TOP_K, user_id=owner_filter)

    # 3. Generate
    system_prompt = (
        guardrails.HARDENED_SYSTEM_PROMPT if guardrails_on else guardrails.WEAK_SYSTEM_PROMPT
    )
    reply = ollama_client.chat(system_prompt, build_user_prompt(user_id, chunks, message))

    # 4. Output filter (guardrails ON only)
    if guardrails_on:
        reply = guardrails.mask_output(reply)

    sources = [
        {"source": c["source"], "doc_type": c["doc_type"], "owner_user_id": c["owner_user_id"]}
        for c in chunks
    ]
    return {"answer": reply, "sources": sources, "blocked": False}
