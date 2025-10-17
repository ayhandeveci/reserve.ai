
import json
from typing import Optional, Union

def call_llm(api_key: str, model: str, prompt: str) -> Union[dict, str, None]:
    """
    Minimal wrapper. Uses OpenAI Responses API if key is provided.
    Falls back to None if import/HTTP fails (so app runs without internet).
    """
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        res = client.responses.create(
            model=model,
            input=prompt,
            temperature=0.2,
            max_output_tokens=900
        )
        # Try to parse text into JSON
        text = res.output_text
        try:
            return json.loads(text)
        except Exception:
            return text
    except Exception:
        return None
