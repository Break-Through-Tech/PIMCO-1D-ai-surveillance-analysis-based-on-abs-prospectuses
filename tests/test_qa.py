"""Tests for the Q/A backend in src/qa/.

They use a fake OpenAI client and a tiny index in a temporary folder, so they
need no API key and no real embeddings. Run from the repository root:

    python -m unittest tests/test_qa.py
"""

import json
import math
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import numpy as np
import openai

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from src.qa import answer, search
from src.qa.answer import answer_question, stream_answer
from src.qa.search import QAError


# (chunk_id, company, asset_type, filing_date, vector). With the query vector
# [1, 0, 0] the similarity order is t1, x1, f1, t2, b1, f2, w1.
RECORDS = [
    ("t1", "TOYOTA", "auto_loans", "2024-04-18", [1.0, 0.0, 0.0]),
    ("f1", "FORD", "auto_loans", "2024-03-11", [0.9, 0.1, 0.0]),
    ("t2", "TOYOTA", "auto_loans", "2025-01-15", [0.8, 0.2, 0.0]),
    ("b1", "BMW", "auto_leases", "2025-05-29", [0.7, 0.3, 0.0]),
    ("f2", "FORD", "auto_loans", "2025-09-18", [0.6, 0.4, 0.0]),
    ("w1", "WELLS_FARGO", "cmbs", "2026-02-11", [0.0, 1.0, 0.0]),
    # Missing metadata comes through as NaN, as in the real index.
    ("x1", math.nan, math.nan, math.nan, [0.95, 0.05, 0.0]),
]
QUERY_VECTOR = [1.0, 0.0, 0.0]


def openai_failure(error_class, message):
    """An OpenAI error built without a real HTTP request or response, since the
    constructors' arguments differ between openai versions."""
    error = error_class.__new__(error_class)
    Exception.__init__(error, message)
    return error


def write_index(folder: Path, records=RECORDS, model="fake-embedding-model", texts=None) -> None:
    texts = texts or {}
    metadata = [
        {
            "chunk_id": chunk_id,
            "filing_stem": f"{chunk_id}_filing",
            "page_num": number + 1,
            "printed_label": str(number + 1),
            "toc_section": "RISK FACTORS",
            "embed_text": texts.get(chunk_id, f"Passage {chunk_id}"),
            "company": company,
            "deal_name": f"Deal {chunk_id}",
            "asset_type": asset_type,
            "filing_date": filing_date,
        }
        for number, (chunk_id, company, asset_type, filing_date, _) in enumerate(records)
    ]
    np.save(folder / "vectors.npy", np.asarray([r[4] for r in records], dtype=np.float32))
    (folder / "metadata.jsonl").write_text(
        "\n".join(json.dumps(record) for record in metadata), encoding="utf-8"
    )
    (folder / "manifest.json").write_text(json.dumps({"model": model}), encoding="utf-8")


class FakeEmbeddings:
    def __init__(self, vector, error=None):
        self.vector = vector
        self.error = error
        self.calls = []

    def create(self, model, input):
        self.calls.append((model, input))
        if self.error:
            raise self.error
        return SimpleNamespace(data=[SimpleNamespace(embedding=list(self.vector))])


class FakeCompletions:
    """Answers with `pieces` joined (or streamed one by one). `error` is raised
    on the call; `error_after` is raised while streaming, after the first piece."""

    def __init__(self, pieces, error=None, error_after=None):
        self.pieces = pieces
        self.error = error
        self.error_after = error_after
        self.calls = []

    def create(self, model, messages, stream=False):
        self.calls.append({"model": model, "messages": messages, "stream": stream})
        if self.error:
            raise self.error
        if not stream:
            message = SimpleNamespace(content="".join(self.pieces))
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])
        return self._stream()

    def _stream(self):
        for number, piece in enumerate(self.pieces):
            if self.error_after and number == 1:
                raise self.error_after
            yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=piece))])


class FakeClient:
    def __init__(self, vector=QUERY_VECTOR, error=None, pieces=("Toyota uses ", "a reserve account ", "[Source 1]."),
                 chat_error=None, chat_error_after=None):
        self.embeddings = FakeEmbeddings(vector, error)
        self.chat = SimpleNamespace(completions=FakeCompletions(list(pieces), chat_error, chat_error_after))


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        write_index(self.folder)
        patcher = mock.patch.object(search, "EMBEDDINGS_DIR", self.folder)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = FakeClient()

    def ids(self, **kwargs):
        kwargs.setdefault("client", self.client)
        return [r["chunk_id"] for r in search.retrieve("reserve account", **kwargs)]

    def test_returns_top_k_best_first(self):
        self.assertEqual(self.ids(top_k=3), ["t1", "x1", "f1"])
        self.assertEqual(self.client.embeddings.calls, [("fake-embedding-model", ["reserve account"])])

    def test_passes_chunk_and_index_metadata_through(self):
        result = search.retrieve("q", top_k=1, client=self.client)[0]
        for field in ("chunk_id", "filing_stem", "page_num", "printed_label", "toc_section",
                      "embed_text", "company", "deal_name", "asset_type", "filing_date"):
            self.assertIn(field, result)
        self.assertAlmostEqual(result["similarity"], 1.0, places=5)

    def test_filters_apply_before_search(self):
        # t2 is only 4th overall, but it is the 2nd best TOYOTA chunk.
        self.assertEqual(self.ids(top_k=2, filters={"company": ["TOYOTA"]}), ["t1", "t2"])

    def test_or_within_a_filter_and_across_filters(self):
        filters = {"company": ["TOYOTA", "FORD"], "year": [2025]}
        self.assertEqual(self.ids(top_k=5, filters=filters), ["t2", "f2"])

    def test_single_values_and_string_years(self):
        self.assertEqual(self.ids(top_k=5, filters={"company": "BMW"}), ["b1"])
        self.assertEqual(self.ids(top_k=5, filters={"year": "2026"}), ["w1"])

    def test_fewer_than_top_k_only_when_fewer_chunks_match(self):
        self.assertEqual(len(self.ids(top_k=5)), 5)
        self.assertEqual(self.ids(top_k=5, filters={"asset_type": ["auto_leases"]}), ["b1"])

    def test_no_match_returns_nothing_and_skips_the_embedding_call(self):
        self.assertEqual(self.ids(top_k=5, filters={"company": ["NOT_A_COMPANY"]}), [])
        self.assertEqual(self.client.embeddings.calls, [])

    def test_empty_filters_mean_all(self):
        self.assertEqual(self.ids(top_k=7, filters={"company": [], "year": None}), self.ids(top_k=7))

    def test_missing_values_never_match_a_filter(self):
        everyone = {"company": ["TOYOTA", "FORD", "BMW", "WELLS_FARGO"]}
        self.assertNotIn("x1", self.ids(top_k=7, filters=everyone))
        self.assertNotIn("x1", self.ids(top_k=7, filters={"year": [2024, 2025, 2026]}))

    def test_unknown_filter_is_rejected(self):
        with self.assertRaises(ValueError):
            self.ids(top_k=5, filters={"colour": ["red"]})

    def test_filter_options_lists_index_values(self):
        self.assertEqual(search.filter_options(), {
            "company": ["BMW", "FORD", "TOYOTA", "WELLS_FARGO"],
            "asset_type": ["auto_leases", "auto_loans", "cmbs"],
            "year": [2024, 2025, 2026],
        })


class SearchErrorTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        patcher = mock.patch.object(search, "EMBEDDINGS_DIR", self.folder)
        patcher.start()
        self.addCleanup(patcher.stop)

    def assertQAError(self, text, **kwargs):
        with self.assertRaises(QAError) as caught:
            search.retrieve("q", **kwargs)
        self.assertIn(text, str(caught.exception))
        return caught.exception

    def test_missing_index(self):
        error = self.assertQAError("hasn't been built yet", client=FakeClient())
        self.assertIsInstance(error.__cause__, FileNotFoundError)

    def test_damaged_index(self):
        write_index(self.folder)
        np.save(self.folder / "vectors.npy", np.zeros((2, 3), dtype=np.float32))
        self.assertQAError("damaged", client=FakeClient())

    def test_wrong_embedding_size(self):
        write_index(self.folder)
        self.assertQAError("doesn't match the embedding model", client=FakeClient(vector=[1.0, 0.0]))

    def test_missing_api_key(self):
        write_index(self.folder)
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertQAError("API key isn't set")

    def test_openai_failures_become_plain_messages(self):
        write_index(self.folder)
        cases = [
            (openai_failure(openai.AuthenticationError, "bad key"), "rejected the API key"),
            (openai_failure(openai.RateLimitError, "slow down"), "limiting requests"),
            (openai_failure(openai.APIConnectionError, "no network"), "Couldn't reach OpenAI"),
        ]
        for original, text in cases:
            with self.subTest(text=text):
                error = self.assertQAError(text, client=FakeClient(error=original))
                self.assertIs(error.__cause__, original)


SOURCE_FIELDS = {
    "number", "deal_name", "company", "asset_type", "filing_date", "filing", "page",
    "page_label", "section", "chunk_id", "similarity", "snippet", "text",
}
LONG_TEXT = "The reserve account is funded at closing. " * 20


class AnswerTestCase(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp())
        write_index(self.folder, texts={"t1": LONG_TEXT})
        patcher = mock.patch.object(search, "EMBEDDINGS_DIR", self.folder)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = FakeClient()

    def prompt(self):
        return self.client.chat.completions.calls[-1]["messages"][-1]["content"]


class AnswerTests(AnswerTestCase):
    def test_returns_answer_and_sources_only(self):
        result = answer_question("How are reserve accounts funded?", top_k=3, client=self.client)
        self.assertEqual(set(result), {"answer", "sources"})
        self.assertEqual(result["answer"], "Toyota uses a reserve account [Source 1].")

    def test_sources_follow_the_contract(self):
        sources = answer_question("q", top_k=3, client=self.client)["sources"]
        self.assertEqual([s["number"] for s in sources], [1, 2, 3])
        self.assertEqual([s["chunk_id"] for s in sources], ["t1", "x1", "f1"])
        for source in sources:
            self.assertEqual(set(source), SOURCE_FIELDS)
        first = sources[0]
        self.assertEqual((first["deal_name"], first["company"], first["filing"]), ("Deal t1", "TOYOTA", "t1_filing"))
        self.assertEqual((first["page"], first["page_label"], first["section"]), (1, "1", "RISK FACTORS"))

    def test_missing_values_become_none(self):
        missing = answer_question("q", top_k=3, client=self.client)["sources"][1]
        self.assertEqual(missing["chunk_id"], "x1")
        for field in ("company", "asset_type", "filing_date"):
            self.assertIsNone(missing[field])

    def test_snippet_is_short_and_text_is_full(self):
        first = answer_question("q", top_k=1, client=self.client)["sources"][0]
        self.assertEqual(first["text"], LONG_TEXT)
        self.assertLessEqual(len(first["snippet"]), answer.SNIPPET_LENGTH + 1)
        self.assertTrue(first["snippet"].endswith("…"))

    def test_prompt_uses_short_source_labels(self):
        sources = answer_question("q", top_k=3, client=self.client)["sources"]
        prompt = self.prompt()
        blocks = prompt.split("Retrieved evidence:\n")[1].split("\n\n")
        for number, (block, source) in enumerate(zip(blocks, sources), start=1):
            # [Source N] in the prompt is sources[N - 1].
            self.assertTrue(block.startswith(f"[Source {number}]\n"))
            self.assertIn(source["text"], block)
        self.assertNotIn("[Source 1:", prompt)
        self.assertIn("Deal t1 | t1_filing | filed 2024-04-18 | printed page 1 (page 1) | section RISK FACTORS", prompt)

    def test_filters_reach_the_search(self):
        sources = answer_question("q", top_k=5, filters={"company": ["FORD"]}, client=self.client)["sources"]
        self.assertEqual([s["chunk_id"] for s in sources], ["f1", "f2"])

    def test_no_match_answers_without_calling_openai(self):
        result = answer_question("q", filters={"company": ["NOT_A_COMPANY"]}, client=self.client)
        self.assertEqual(result, {"answer": answer.NO_MATCH_ANSWER, "sources": []})
        self.assertEqual(self.client.embeddings.calls, [])
        self.assertEqual(self.client.chat.completions.calls, [])

    def test_default_and_chosen_model(self):
        answer_question("q", client=self.client)
        self.assertEqual(self.client.chat.completions.calls[-1]["model"], answer.DEFAULT_MODEL)
        answer_question("q", model="other-model", client=self.client)
        self.assertEqual(self.client.chat.completions.calls[-1]["model"], "other-model")

    def test_empty_answer_is_an_error(self):
        with self.assertRaises(QAError) as caught:
            answer_question("q", client=FakeClient(pieces=["  "]))
        self.assertIn("empty answer", str(caught.exception))

    def test_openai_failure_is_an_error(self):
        original = openai_failure(openai.APIConnectionError, "no network")
        with self.assertRaises(QAError) as caught:
            answer_question("q", client=FakeClient(chat_error=original))
        self.assertIs(caught.exception.__cause__, original)

    def test_missing_api_key(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            for function in (answer_question, stream_answer):
                with self.subTest(function=function.__name__), self.assertRaises(QAError):
                    function("q")


class StreamTests(AnswerTestCase):
    def test_sources_are_ready_before_any_text(self):
        result = stream_answer("q", top_k=3, client=self.client)
        self.assertEqual(set(result), {"answer", "sources"})
        self.assertEqual([s["chunk_id"] for s in result["sources"]], ["t1", "x1", "f1"])
        self.assertEqual(self.client.chat.completions.calls, [])  # nothing requested yet
        self.assertEqual(list(result["answer"]), ["Toyota uses ", "a reserve account ", "[Source 1]."])
        self.assertTrue(self.client.chat.completions.calls[-1]["stream"])

    def test_pieces_join_up_to_the_full_answer(self):
        streamed = "".join(stream_answer("q", top_k=3, client=self.client)["answer"])
        full = answer_question("q", top_k=3, client=FakeClient())["answer"]
        self.assertEqual(streamed, full)

    def test_same_sources_and_prompt_as_answer_question(self):
        streamed = stream_answer("q", top_k=3, client=self.client)
        list(streamed["answer"])
        stream_prompt = self.prompt()
        full = answer_question("q", top_k=3, client=self.client)
        self.assertEqual(streamed["sources"], full["sources"])
        self.assertEqual(stream_prompt, self.prompt())

    def test_no_match_message_also_streams(self):
        result = stream_answer("q", filters={"year": [1999]}, client=self.client)
        self.assertEqual(result["sources"], [])
        self.assertEqual(list(result["answer"]), [answer.NO_MATCH_ANSWER])
        self.assertEqual(self.client.chat.completions.calls, [])

    def test_failure_mid_answer_is_an_error(self):
        original = openai_failure(openai.APIConnectionError, "dropped")
        pieces = stream_answer("q", client=FakeClient(chat_error_after=original))["answer"]
        self.assertEqual(next(pieces), "Toyota uses ")
        with self.assertRaises(QAError) as caught:
            next(pieces)
        self.assertIs(caught.exception.__cause__, original)

    def test_empty_stream_is_an_error(self):
        pieces = stream_answer("q", client=FakeClient(pieces=[]))["answer"]
        with self.assertRaises(QAError):
            list(pieces)


class CitationTests(AnswerTestCase):
    def test_grouped_citations_are_split(self):
        cases = {
            "A [Sources 1, 5].": "A [Source 1][Source 5].",
            "A [Sources 1,5] B": "A [Source 1][Source 5] B",
            "A [Source 1 and 3]": "A [Source 1][Source 3]",
            "A [Sources 2-4]": "A [Source 2][Source 3][Source 4]",
            "A [Sources 2–4, 6]": "A [Source 2][Source 3][Source 4][Source 6]",
            "A [Source 1; Source 5]": "A [Source 1][Source 5]",
            "A [Source 1, Source 2 & Source 3]": "A [Source 1][Source 2][Source 3]",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(answer.normalize_citations(text), expected)

    def test_other_text_is_left_alone(self):
        for text in ("A [Source 1].", "A [Source 1][Source 5].", "Class A-2 [as defined] notes", "[TABLE_3] 1, 5"):
            with self.subTest(text=text):
                self.assertEqual(answer.normalize_citations(text), text)

    def test_prompt_asks_for_separate_citations(self):
        answer_question("q", client=self.client)
        self.assertIn("never combine them as [Sources 1, 5]", self.prompt())

    def test_full_answer_is_normalized(self):
        client = FakeClient(pieces=["Servicer may be replaced [Sources 1, 5]."])
        result = answer_question("q", client=client)
        self.assertEqual(result["answer"], "Servicer may be replaced [Source 1][Source 5].")

    def test_streamed_citation_split_across_pieces_is_normalized(self):
        pieces = ["Servicer may ", "be replaced [Sour", "ces 1, ", "5] if ", "it fails [Source 2]."]
        streamed = list(stream_answer("q", client=FakeClient(pieces=pieces))["answer"])
        self.assertEqual("".join(streamed), "Servicer may be replaced [Source 1][Source 5] if it fails [Source 2].")
        for piece in streamed:  # no piece carries half a citation
            self.assertEqual(piece.count("["), piece.count("]"))
        full = answer_question("q", client=FakeClient(pieces=pieces))["answer"]
        self.assertEqual("".join(streamed), full)

    def test_unfinished_bracket_at_the_end_is_still_sent(self):
        streamed = list(stream_answer("q", client=FakeClient(pieces=["Done [Source"]))["answer"])
        self.assertEqual("".join(streamed), "Done [Source")


class FrontDoorTests(unittest.TestCase):
    def test_app_can_import_the_backend(self):
        # A fresh process in the repository root, as `streamlit run app.py` would be.
        code = (
            "from src.qa import QAError, answer_question, filter_options, stream_answer\n"
            "import src.qa\n"
            "print(sorted(src.qa.__all__))"
        )
        result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(),
                         "['QAError', 'answer_question', 'filter_options', 'stream_answer']")

    def test_front_door_is_the_same_code(self):
        import src.qa
        self.assertIs(src.qa.answer_question, answer_question)
        self.assertIs(src.qa.stream_answer, stream_answer)
        self.assertIs(src.qa.filter_options, search.filter_options)
        self.assertIs(src.qa.QAError, QAError)


if __name__ == "__main__":
    unittest.main()
