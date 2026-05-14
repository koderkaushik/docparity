import json
import re
from src.shared.schema import DriftType


def parse_response(response: str) -> dict:
    """Parse an LLM response into a structured result.

    Tries JSON parsing first, falls back to regex extraction.
    """
    # Try JSON parse
    try:
        result = json.loads(response.strip())
        if "drift_type" in result:
            result["drift_type"] = _normalize_drift_type(result["drift_type"])
            return result
    except json.JSONDecodeError:
        pass

    # Try to find JSON embedded in text
    json_match = re.search(r'\{[^}]+\}', response)
    if json_match:
        try:
            result = json.loads(json_match.group())
            if "drift_type" in result:
                result["drift_type"] = _normalize_drift_type(result["drift_type"])
                return result
        except json.JSONDecodeError:
            pass

    # Fallback: regex extraction
    drift_type = _extract_drift_type_from_text(response)
    description = _extract_description_from_text(response)
    return {"drift_type": drift_type, "description": description}


def _normalize_drift_type(raw: str) -> str:
    raw_lower = raw.strip().lower()
    if raw_lower in ("syntactic", "syntax"):
        return "syntactic"
    if raw_lower in ("semantic", "behavioral"):
        return "semantic"
    if raw_lower in ("no-drift", "no_drift", "none", "consistent"):
        return "no-drift"
    return raw_lower


def _extract_drift_type_from_text(text: str) -> str:
    text_lower = text.lower()
    if "syntactic" in text_lower or "syntax" in text_lower or "parameter" in text_lower:
        return "syntactic"
    if "semantic" in text_lower or "behavioral" in text_lower or "behavior" in text_lower:
        return "semantic"
    return "no-drift"


def _extract_description_from_text(text: str) -> str:
    sentences = re.split(r'[.!?]', text)
    return sentences[0].strip() if sentences else ""