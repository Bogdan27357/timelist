import json
import httpx

from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL


async def _ollama_generate(prompt: str, max_tokens: int = 3000) -> str:
    """Send prompt to Ollama and return raw text response."""
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": max_tokens,
                },
            },
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "")


def _parse_json(text: str) -> dict:
    """Try to parse JSON from LLM response, stripping markdown fences."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


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
        text = await _ollama_generate(prompt)
        parsed = _parse_json(text)
        if parsed:
            return {
                "summary": parsed.get("summary", ""),
                "action_items": parsed.get("action_items", ""),
                "sentiment": parsed.get("sentiment", "neutral"),
                "key_topics": parsed.get("key_topics", ""),
                "decisions": parsed.get("decisions", ""),
            }
        return {
            "summary": text,
            "action_items": "",
            "sentiment": "neutral",
            "key_topics": "",
            "decisions": "",
        }
    except Exception as e:
        return {
            "summary": f"Ошибка подключения к Ollama: {e}",
            "action_items": "",
            "sentiment": "neutral",
            "key_topics": "",
            "decisions": "",
            "error": str(e),
        }


async def generate_protocol(
    transcript: str,
    title: str = "",
    participants_info: str = "",
    meeting_date: str = "",
) -> dict:
    """Generate a formal meeting protocol from transcript using Ollama."""
    prompt = f"""Ты — ИИ-ассистент, создающий официальные протоколы совещаний.
На основе стенограммы/транскрипта создай полный протокол мероприятия.

Название мероприятия: {title}
Дата: {meeting_date}
Участники и роли: {participants_info}

Стенограмма:
---
{transcript}
---

Верни ответ СТРОГО в формате JSON (без markdown, без ```):
{{
    "protocol": "Полный текст протокола в формате:\\n\\nПРОТОКОЛ\\nМероприятие: ...\\nДата: ...\\nПрисутствовали: ...\\n\\nПОВЕСТКА ДНЯ:\\n1. ...\\n\\nХОД СОВЕЩАНИЯ:\\n...\\n\\nРЕШЕНИЯ:\\n1. ...\\n\\nЗАДАЧИ:\\n1. задача — ответственный — срок",
    "summary": "Краткое резюме (2-3 предложения)",
    "action_items": [
        {{"task": "описание задачи", "assignee": "ответственный", "deadline": "срок или пусто"}}
    ],
    "key_topics": "ключевые темы через запятую",
    "decisions": "- решение 1\\n- решение 2",
    "sentiment": "positive/neutral/negative"
}}"""

    try:
        text = await _ollama_generate(prompt, max_tokens=4000)
        parsed = _parse_json(text)
        if parsed:
            return {
                "protocol": parsed.get("protocol", ""),
                "summary": parsed.get("summary", ""),
                "action_items": parsed.get("action_items", []),
                "key_topics": parsed.get("key_topics", ""),
                "decisions": parsed.get("decisions", ""),
                "sentiment": parsed.get("sentiment", "neutral"),
            }
        return {
            "protocol": text,
            "summary": "",
            "action_items": [],
            "key_topics": "",
            "decisions": "",
            "sentiment": "neutral",
        }
    except Exception as e:
        return {
            "protocol": f"Ошибка: {e}",
            "summary": "",
            "action_items": [],
            "key_topics": "",
            "decisions": "",
            "sentiment": "neutral",
            "error": str(e),
        }


async def identify_speakers(transcript: str, speaker_count: int = 2) -> str:
    """Use Ollama to identify and label speakers in a transcript."""
    prompt = f"""Ты — ИИ-ассистент для распознавания спикеров.
Вот транскрипт совещания. В нём участвовали {speaker_count} спикера(ов).
Попробуй определить, где говорит каждый спикер, и перепиши транскрипт,
добавив метки спикеров (Спикер 1, Спикер 2 и т.д.).

Транскрипт:
---
{transcript}
---

Верни переписанный транскрипт с метками спикеров. Каждая реплика с новой строки:
Спикер 1: текст
Спикер 2: текст
..."""

    try:
        return await _ollama_generate(prompt, max_tokens=4000)
    except Exception as e:
        return f"Ошибка диаризации: {e}"


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
