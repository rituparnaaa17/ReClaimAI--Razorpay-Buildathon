"""
conftest.py — Mocks heavy optional dependencies so tests can be collected
without requiring google-generativeai, razorpay, or langchain to be installed
in the test environment.

The tests themselves mock all service calls — these stubs only exist to prevent
ImportError during collection.
"""
import sys
from unittest.mock import MagicMock

# ── Stub google.genai ─────────────────────────────────────────────────────────
google_mock = MagicMock()
genai_mock = MagicMock()
google_mock.genai = genai_mock

sys.modules.setdefault("google", google_mock)
sys.modules.setdefault("google.genai", genai_mock)

# ── Stub razorpay ─────────────────────────────────────────────────────────────
class MockBadRequestError(Exception): pass
class MockServerError(Exception): pass

razorpay_mock = MagicMock()
razorpay_mock.errors = MagicMock()
razorpay_mock.errors.BadRequestError = MockBadRequestError
razorpay_mock.errors.ServerError = MockServerError
sys.modules.setdefault("razorpay", razorpay_mock)

# ── Stub langgraph / langchain ─────────────────────────────────────────────────
for mod in [
    "langgraph", "langgraph.graph", "langgraph.prebuilt",
    "langchain", "langchain.schema", "langchain_google_genai",
]:
    sys.modules.setdefault(mod, MagicMock())
