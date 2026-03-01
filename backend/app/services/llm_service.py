import requests
from typing import Dict, Any
from ..config import settings


def generate_report_with_ollama(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calls Ollama chat and asks for a compact JSON report.
    """
    prompt = (
        "You are a codebase analyst.\n"
        "Return ONLY strict JSON.\n"
        "Schema:\n"
        "{"
        "\"overview\":{\"one_liner\":str,\"what_it_does\":str,\"primary_language\":str},"
        "\"architecture\":{\"style\":str,\"entrypoints\":list,\"key_modules\":list,\"data_flow\":list},"
        "\"dependencies\":{\"summary\":str,\"high_impact\":list},"
        "\"improvements\":{\"quick_wins\":list,\"risks\":list},"
        "\"important_files\":list"
        "}\n"
        "Use the provided analysis to fill this.\n"
    )

    payload = {
        "model": settings.OLLAMA_MODEL,
        "format": "json",
        "stream": False,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"analysis:\n{analysis}"},
        ],
    }

    r = requests.post(f"{settings.OLLAMA_URL}/api/chat", json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()

    # Ollama returns JSON as a string inside message.content
    content = data.get("message", {}).get("content", "")
    if not content:
        raise RuntimeError("Empty LLM response")

    # content is JSON string; parse it
    try:
        import json
        return json.loads(content)
    except Exception as e:
        raise RuntimeError(f"LLM returned non-JSON: {e}")