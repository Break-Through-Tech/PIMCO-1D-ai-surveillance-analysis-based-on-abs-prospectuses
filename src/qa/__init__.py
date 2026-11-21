"""Q/A backend for the Streamlit app.

From app.py in the repository root:

    from src.qa import QAError, answer_question, filter_options, stream_answer

    result = answer_question("Which deals use physical custody?", filters={"year": [2024]})
    result["answer"]   # text with [Source N] citations
    result["sources"]  # [Source N] is result["sources"][N - 1]

stream_answer() returns the same sources straight away and the answer as text
pieces for st.write_stream(). Any problem the user should see raises QAError.
"""

from src.qa.answer import answer_question, stream_answer
from src.qa.search import QAError, filter_options

__all__ = ["QAError", "answer_question", "filter_options", "stream_answer"]
