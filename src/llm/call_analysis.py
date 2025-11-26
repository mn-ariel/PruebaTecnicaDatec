import json
import logging

from src.llm.openai_client import get_client
from src.llm.prompts import CALL_ANALYSIS_SYSTEM_PROMPT, CALL_ANALYSIS_USER_TEMPLATE

logger = logging.getLogger(__name__)
client = get_client()


def analyze_call_text(transcript: str, model: str = "gpt-4.1-mini") -> dict:
    # Caso borde: transcript vacío
    if not isinstance(transcript, str) or not transcript.strip():
        return {
            "sentiment": None,
            "call_type": None,
            "summary": "",
            "sentiment_start": None,
            "sentiment_end": None,
            "has_risk_phrases": False,
            "risk_phrases": [],
            "complexity_score": None,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

    user_content = CALL_ANALYSIS_USER_TEMPLATE.format(transcript=transcript)

    try:
        # SIN response_format (tu SDK no lo soporta)
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": CALL_ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )

        # El modelo devuelve el JSON como texto
        content = response.output[0].content[0].text
        data = json.loads(content)

        # Base fields
        sentiment = (data.get("sentiment") or "").lower() or None
        call_type = (data.get("call_type") or "").lower() or None
        summary = data.get("summary") or ""

        # New sentiment flow
        sentiment_start = (data.get("sentiment_start") or "").lower() or None
        sentiment_end = (data.get("sentiment_end") or "").lower() or None

        # Risk phrases
        has_risk = bool(data.get("has_risk_phrases", False))
        risk_phrases = data.get("risk_phrases") or []
        if not isinstance(risk_phrases, list):
            risk_phrases = [str(risk_phrases)]

        # Complexity
        complexity = data.get("complexity_score")
        try:
            complexity = int(complexity) if complexity is not None else None
        except (TypeError, ValueError):
            complexity = None

        usage = getattr(response, "usage", None)
        prompt_tokens = getattr(usage, "input_tokens", 0) if usage else 0
        completion_tokens = getattr(usage, "output_tokens", 0) if usage else 0
        total_tokens = prompt_tokens + completion_tokens

        return {
            "sentiment": sentiment,
            "call_type": call_type,
            "summary": summary,
            "sentiment_start": sentiment_start,
            "sentiment_end": sentiment_end,
            "has_risk_phrases": has_risk,
            "risk_phrases": risk_phrases,
            "complexity_score": complexity,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }

    except Exception as exc:
        logger.error("Error calling OpenAI for call analysis: %s", exc)
        return {
            "sentiment": None,
            "call_type": None,
            "summary": "",
            "sentiment_start": None,
            "sentiment_end": None,
            "has_risk_phrases": False,
            "risk_phrases": [],
            "complexity_score": None,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
