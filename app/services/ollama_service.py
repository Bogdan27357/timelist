import json
import httpx

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL


async def analyze_call(transcript: str, title: str = "", participants: str = "") -> dict:
    """Analyze a call transcript using Ollama local LLM."""

    prompt = f"""Ты — ИИ-ассистент для анализа рабочих созвонов и конференций.
Проанализируй следующую запись/транскрипт созвона и верни структурированный результат.

Название созвона: {title}
Участники: {participants}

Транскрипт:
---
{transcript}
---

Верни ответ СТРОГО в формате JSON (без markdown, без ```):
{{
    "summary": "Краткое резюме созвона (2-5 предложений)",
    "action_items": "Список задач и действий (каждое с новой строки, формат: - задача (ответственный))",
    "sentiment": "Общий тон встречи: positive/neutral/negative",
    "key_topics": "Ключевые темы обсуждения (через запятую)",
    "decisions": "Принятые решения (каждое с новой строки, формат: - решение)"
}}"""

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 2000,
                    },
                },
            )
            response.raise_for_status()
            result = response.json()
            text = result.get("response", "")

            # Try to parse JSON from response
            try:
                parsed = json.loads(text.strip())
                return {
                    "summary": parsed.get("summary", ""),
                    "action_items": parsed.get("action_items", ""),
                    "sentiment": parsed.get("sentiment", "neutral"),
                    "key_topics": parsed.get("key_topics", ""),
                    "decisions": parsed.get("decisions", ""),
                }
            except json.JSONDecodeError:
                # If JSON parsing fails, return raw text as summary
                return {
                    "summary": text,
                    "action_items": "",
                    "sentiment": "neutral",
                    "key_topics": "",
                    "decisions": "",
                }
    except httpx.HTTPError as e:
        return {
            "summary": f"Ошибка подключения к Ollama: {e}",
            "action_items": "",
            "sentiment": "neutral",
            "key_topics": "",
            "decisions": "",
            "error": str(e),
        }


async def check_ollama_status() -> dict:
    """Check if Ollama is running and the model is available."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
            data = response.json()
            models = [m["name"] for m in data.get("models", [])]
            return {
                "status": "online",
                "models": models,
                "current_model": OLLAMA_MODEL,
                "model_available": any(OLLAMA_MODEL in m for m in models),
            }
    except Exception as e:
        return {
            "status": "offline",
            "error": str(e),
            "current_model": OLLAMA_MODEL,
            "model_available": False,
        }
