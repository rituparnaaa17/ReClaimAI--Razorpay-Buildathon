"""
Gemini client — uses the new google.genai SDK with gemini-2.5-flash.
Runs blocking SDK calls in a thread pool so the async event loop stays free.
"""
from google import genai
from app.config import get_settings
from functools import lru_cache
import asyncio

GEMINI_MODEL = "gemini-3.6-flash"


@lru_cache()
def get_gemini_client() -> genai.Client:
    settings = get_settings()
    return genai.Client(api_key=settings.gemini_api_key)


def _sync_generate(prompt: str) -> str:
    """Synchronous Gemini call — always called from a thread."""
    client = get_gemini_client()
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )
    return response.text.strip()


async def generate_text(prompt: str) -> str:
    """Non-blocking wrapper — runs the sync SDK call in a thread executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_generate, prompt)
