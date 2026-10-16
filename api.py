"""FastAPI app.  Run:  uvicorn api:app --port 8001"""
from fastapi import FastAPI, Header
from pydantic import BaseModel

import config
import rag

app = FastAPI(title="Harbor Trust Bank - Support Assistant (RAG lab)")


class ChatRequest(BaseModel):
    user_id: str
    message: str


@app.get("/health")
def health():
    return {"status": "ok", "guardrails_default": "on" if config.GUARDRAILS_DEFAULT else "off"}


@app.post("/chat")
def chat(req: ChatRequest, x_guardrails: str | None = Header(default=None)):
    # Header X-Guardrails: on|off overrides the GUARDRAILS env var for this request.
    if x_guardrails is not None and x_guardrails.lower() in ("on", "off"):
        guardrails_on = x_guardrails.lower() == "on"
    else:
        guardrails_on = config.GUARDRAILS_DEFAULT

    result = rag.answer(req.user_id, req.message, guardrails_on)
    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "guardrails": "on" if guardrails_on else "off",
        "blocked": result["blocked"],
    }
