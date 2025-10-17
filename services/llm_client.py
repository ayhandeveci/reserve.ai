# services/llm_client.py
import json
from typing import Union
import streamlit as st

def _extract_text(res) -> str | None:
    """
    SDK farklarına dayanıklı metin çıkarıcı.
    - Responses API: res.output_text (varsa) ya da res.output[*].content[*].text
    - Chat Completions: res.choices[0].message.content
    """
    # 1) OpenAI Responses API (kolay özellik)
    text = getattr(res, "output_text", None)
    if isinstance(text, str) and text.strip():
        return text

    # 2) Responses API (ham yapı)
    try:
        out = getattr(res, "output", None)
        if out:
            parts = []
            for item in out:
                content = getattr(item, "content", None)
                if content:
                    for c in content:
                        # bazı SDK sürümlerinde type "output_text" ya da "text" olabilir
                        t = getattr(c, "text", None)
                        if isinstance(t, str):
                            parts.append(t)
            if parts:
                return "\n".join(parts)
    except Exception:
        pass

    # 3) Chat Completions fallback
    try:
        return res.choices[0].message.content
    except Exception:
        return None


def call_llm(api_key: str, model: str, prompt: str) -> Union[dict, str, None]:
    """
    Güçlü wrapper:
    1) OpenAI Responses API'yi dener.
    2) Olmazsa Chat Completions'a düşer.
    3) Yanıt metnini JSON'a parse etmeye çalışır; olmazsa string döner.
    4) Hataları Streamlit üzerinde gösterir (sessizce yutmaz).
    """
    if not api_key or not model or not prompt:
        st.error("LLM çağrısı için API key / model / prompt eksik.")
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        # 1) Responses API
        try:
            res = client.responses.create(
                model=model,
                input=prompt,
                temperature=0.2,
                max_output_tokens=900,
            )
        except Exception as e1:
            # 2) Chat Completions fallback
            try:
                res = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=900,
                )
            except Exception as e2:
                st.error(f"LLM çağrısı başarısız: {e2 or e1}")
                return None

        text = _extract_text(res)
        if not text or not isinstance(text, str):
            st.error("LLM yanıtı boş veya beklenmeyen formatta geldi.")
            return None

        # JSON parse denemesi
        try:
            return json.loads(text)
        except Exception:
            return text

    except Exception as e:
        st.error(f"LLM istemci hatası: {e}")
        return None
