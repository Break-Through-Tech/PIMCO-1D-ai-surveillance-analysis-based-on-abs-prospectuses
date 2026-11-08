"""Answer questions from retrieved filing passages, with [Source N] citations.

Part of the Q/A backend in src/qa/. The command line for this module is
notebooks/answer_questions.py.

The completion model receives only the retrieved passages, never the whole
corpus. [Source N] in an answer refers to sources[N - 1].
"""

import math
from collections.abc import Iterator

import openai
from openai import OpenAI

from src.qa.search import QAError, openai_client, openai_error, retrieve


DEFAULT_MODEL = "gpt-6-luna"
SNIPPET_LENGTH = 300
NO_MATCH_ANSWER = "No filing passages match this question and these filters, so there is no evidence to answer from."
EMPTY_ANSWER_MESSAGE = "The model returned an empty answer. Please try again."
SYSTEM_PROMPT = (
    "You are a careful financial-document research assistant. "
    "Use only the retrieved evidence and always cite claims."
)


def _value(record: dict, field: str):
    """A metadata value, with NaN (how the index stores missing values) as None."""
    value = record.get(field)
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _snippet(text: str) -> str:
    text = " ".join(text.split())
    if len(text) <= SNIPPET_LENGTH:
        return text
    return text[:SNIPPET_LENGTH].rsplit(" ", 1)[0] + "…"


def to_source(number: int, record: dict) -> dict:
    """The source entry the frontend receives for one retrieved chunk."""
    text = _value(record, "embed_text") or ""
    return {
        "number": number,
        "deal_name": _value(record, "deal_name"),
        "company": _value(record, "company"),
        "asset_type": _value(record, "asset_type"),
        "filing_date": _value(record, "filing_date"),
        "filing": _value(record, "filing_stem"),
        "page": _value(record, "page_num"),
        "page_label": _value(record, "printed_label"),
        "section": _value(record, "toc_section"),
        "chunk_id": _value(record, "chunk_id"),
        "similarity": record["similarity"],
        "snippet": _snippet(text),
        "text": text,
    }


def _details(source: dict) -> str:
    page = f"page {source['page']}"
    if source["page_label"]:
        page = f"printed page {source['page_label']} ({page})"
    parts = [
        source["deal_name"] or source["company"],
        source["filing"],
        f"filed {source['filing_date']}" if source["filing_date"] else None,
        page,
        f"section {source['section']}" if source["section"] else None,
    ]
    return " | ".join(part for part in parts if part)


def build_prompt(question: str, sources: list[dict]) -> str:
    evidence = [
        f"[Source {source['number']}]\n{_details(source)}\n{source['text']}"
        for source in sources
    ]
    return (
        "Answer the user's question using only the supplied evidence. "
        "Do not rely on outside knowledge and do not invent facts. "
        "If the evidence is insufficient or conflicting, say so clearly. "
        "Cite every substantive claim with the short label of its source, "
        "exactly in the form [Source 1], and only cite sources listed below. "
        "Keep the answer concise.\n\n"
        f"User question:\n{question}\n\n"
        "Retrieved evidence:\n"
        + "\n\n".join(evidence)
    )


def _messages(question: str, sources: list[dict]) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_prompt(question, sources)},
    ]


def _find_sources(question: str, top_k: int, filters: dict | None, client: OpenAI | None) -> list[dict]:
    records = retrieve(question, top_k=top_k, filters=filters, client=client)
    return [to_source(number, record) for number, record in enumerate(records, start=1)]


def answer_question(
    question: str,
    *,
    top_k: int = 5,
    filters: dict | None = None,
    model: str = DEFAULT_MODEL,
    client: OpenAI | None = None,
) -> dict:
    """Return {"answer": text, "sources": [...]} with the complete answer.

    Raises QAError with a plain-language message when something goes wrong.
    """
    sources = _find_sources(question, top_k, filters, client)
    if not sources:
        return {"answer": NO_MATCH_ANSWER, "sources": []}

    client = client or openai_client()
    try:
        response = client.chat.completions.create(model=model, messages=_messages(question, sources))
    except openai.OpenAIError as error:
        raise openai_error(error) from error
    answer = response.choices[0].message.content
    if not answer or not answer.strip():
        raise QAError(EMPTY_ANSWER_MESSAGE)
    return {"answer": answer.strip(), "sources": sources}


def _stream_pieces(client: OpenAI, model: str, messages: list[dict]) -> Iterator[str]:
    received = False
    try:
        stream = client.chat.completions.create(model=model, messages=messages, stream=True)
        for chunk in stream:
            piece = chunk.choices[0].delta.content if chunk.choices else None
            if piece:
                received = True
                yield piece
    except openai.OpenAIError as error:
        raise openai_error(error) from error
    if not received:
        raise QAError(EMPTY_ANSWER_MESSAGE)


def stream_answer(
    question: str,
    *,
    top_k: int = 5,
    filters: dict | None = None,
    model: str = DEFAULT_MODEL,
    client: OpenAI | None = None,
) -> dict:
    """Return {"answer": iterator of text pieces, "sources": [...]}.

    The search runs straight away, so sources are ready before any text
    arrives. The answer is requested when the iterator is first read, so a
    QAError can also be raised while reading it.
    """
    sources = _find_sources(question, top_k, filters, client)
    if not sources:
        return {"answer": iter([NO_MATCH_ANSWER]), "sources": []}

    client = client or openai_client()
    return {"answer": _stream_pieces(client, model, _messages(question, sources)), "sources": sources}
