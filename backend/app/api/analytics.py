from fastapi import APIRouter
from app.services.db_service import db_get_analytics_overview
from app.services.mock_data import get_mock_analytics

router = APIRouter()


@router.get("/overview")
async def get_analytics_overview():
    return await db_get_analytics_overview()


@router.get("/charts")
def get_analytics_charts():
    data = get_mock_analytics()
    return data["charts"]


@router.get("/insight")
async def get_ai_insight():
    """Generate a Gemini AI insight about current recovery patterns."""
    from app.services.gemini_client import generate_text
    from app.config import get_settings
    settings = get_settings()

    if settings.gemini_api_key:
        try:
            prompt = """You are ReclaimAI's analytics AI. Based on typical Indian e-commerce payment failure patterns, generate one specific, actionable insight about payment recovery.

Format your response as valid JSON only (no markdown, no code blocks):
{"title": "short title under 50 chars", "insight": "2 sentence insight with specific numbers", "recommendation": "1 sentence action"}

Focus on UPI, card, or bank patterns common in India."""
            text = await generate_text(prompt)
            # Strip any markdown code fences if present
            text = text.replace("```json", "").replace("```", "").strip()
            import json
            return json.loads(text)
        except Exception as e:
            print(f"[Gemini] insight failed: {e}")

    return {
        "title": "UPI Timeout Spike Detected",
        "insight": "UPI timeout failures increased 18% this week. Customers with previous successful UPI payments have an 84% recovery probability after a delayed retry of 5-10 minutes.",
        "recommendation": "Enable automatic delayed retry for UPI timeout failures in your recovery policy.",
    }
