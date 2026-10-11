import json
import re


class JSONParser:
    """
    Extract and parse JSON returned by an LLM.

    If the optional `json-repair` package is installed, use it as a fallback
    for common model formatting mistakes. Strict JSON parsing remains the
    first choice.
    """

    @staticmethod
    def parse(text: str):
        if not text or not text.strip():
            raise ValueError("Empty response received.")

        text = text.strip()

        # Remove Markdown fences without assuming the opening fence is at
        # character zero after provider formatting.
        text = re.sub(r"^\\s*```(?:json)?\\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\\s*```\\s*$", "", text)
        text = text.strip()

        # First: accept a complete JSON value exactly as returned.
        try:
            return json.loads(text)
        except json.JSONDecodeError as original_error:
            pass

        # Second: try each plausible object/array start. This avoids the
        # greedy {.*} extraction that can swallow multiple JSON fragments.
        candidates = []
        for opening, closing in (("{", "}"), ("[", "]")):
            start = text.find(opening)
            end = text.rfind(closing)
            if start >= 0 and end > start:
                candidates.append(text[start:end + 1])

        for candidate in candidates:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

        # Third: optional best-effort repair for missing commas/closing
        # brackets and other common LLM JSON mistakes.
        try:
            from json_repair import repair_json
            repaired = repair_json(text, return_objects=True)
            if isinstance(repaired, (dict, list)):
                return repaired
        except ImportError:
            pass
        except Exception as repair_error:
            raise ValueError(
                f"JSON repair failed: {repair_error}. "
                f"Original JSON error: {original_error}"
            ) from repair_error

        preview = text[:1200]
        raise ValueError(
            "No valid JSON found in the model response. The response may be "
            "malformed or truncated by the output-token limit. "
            f"Original JSON error: {original_error}. "
            f"Response preview: {preview}"
        )
