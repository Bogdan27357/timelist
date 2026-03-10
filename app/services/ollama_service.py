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
    prompt = f"""Ты — ИИ-ассистент, создающий официальные протоколы совещаний в стиле 1С:Документооборот.
На основе стенограммы создай полный, красиво оформленный протокол мероприятия.

Название мероприятия: {title}
Дата: {meeting_date}
Участники и роли: {participants_info}

Стенограмма:
---
{transcript}
---

Верни ответ СТРОГО в формате JSON (без markdown, без ```):
{{
    "protocol_header": {{
        "title": "Название мероприятия",
        "number": "Номер протокола (придумай)",
        "date": "{meeting_date}",
        "location": "Место проведения",
        "chairman": "ФИО председателя (определи из контекста или укажи первого участника)",
        "secretary": "ФИО секретаря (определи из контекста или укажи)",
        "attendees": ["ФИО — должность/роль"]
    }},
    "agenda": ["Пункт повестки дня 1", "Пункт повестки дня 2"],
    "discussion": [
        {{
            "topic": "Тема обсуждения",
            "speaker": "Докладчик",
            "summary": "Краткое содержание выступления/обсуждения (2-4 предложения)"
        }}
    ],
    "decisions": [
        {{
            "number": 1,
            "text": "Формулировка решения",
            "responsible": "Ответственный",
            "deadline": "Срок исполнения"
        }}
    ],
    "action_items": [
        {{
            "task": "Описание задачи",
            "assignee": "Ответственный исполнитель",
            "deadline": "Срок"
        }}
    ],
    "summary": "Краткое резюме совещания (2-3 предложения)",
    "key_topics": "ключевые темы через запятую",
    "sentiment": "positive/neutral/negative"
}}"""

    try:
        text = await _ollama_generate(prompt, max_tokens=5000)
        parsed = _parse_json(text)
        if parsed:
            # Build formatted protocol text from structured data
            protocol_text = _build_protocol_text(parsed)
            # Build decisions text
            decisions_list = parsed.get("decisions", [])
            if isinstance(decisions_list, list):
                decisions_text = "\n".join(
                    f"{d.get('number', i+1)}. {d.get('text', d) if isinstance(d, dict) else d}"
                    + (f" — {d['responsible']}" if isinstance(d, dict) and d.get('responsible') else "")
                    + (f" (срок: {d['deadline']})" if isinstance(d, dict) and d.get('deadline') else "")
                    for i, d in enumerate(decisions_list)
                )
            else:
                decisions_text = str(decisions_list)

            return {
                "protocol": protocol_text,
                "protocol_data": parsed,
                "summary": parsed.get("summary", ""),
                "action_items": parsed.get("action_items", []),
                "key_topics": parsed.get("key_topics", ""),
                "decisions": decisions_text,
                "sentiment": parsed.get("sentiment", "neutral"),
            }
        return {
            "protocol": text,
            "protocol_data": {},
            "summary": "",
            "action_items": [],
            "key_topics": "",
            "decisions": "",
            "sentiment": "neutral",
        }
    except Exception as e:
        return {
            "protocol": f"Ошибка: {e}",
            "protocol_data": {},
            "summary": "",
            "action_items": [],
            "key_topics": "",
            "decisions": "",
            "sentiment": "neutral",
            "error": str(e),
        }


def _build_protocol_text(data: dict) -> str:
    """Build a beautifully formatted protocol text from structured JSON data."""
    lines = []
    header = data.get("protocol_header", {})

    lines.append("=" * 60)
    lines.append("ПРОТОКОЛ")
    lines.append(f"совещания: {header.get('title', '')}")
    if header.get("number"):
        lines.append(f"N {header['number']}")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Дата: {header.get('date', '')}")
    if header.get("location"):
        lines.append(f"Место: {header['location']}")
    lines.append("")
    if header.get("chairman"):
        lines.append(f"Председатель: {header['chairman']}")
    if header.get("secretary"):
        lines.append(f"Секретарь:    {header['secretary']}")
    lines.append("")

    attendees = header.get("attendees", [])
    if attendees:
        lines.append("Присутствовали:")
        for a in attendees:
            lines.append(f"  - {a}")
        lines.append("")

    # Agenda
    agenda = data.get("agenda", [])
    if agenda:
        lines.append("-" * 40)
        lines.append("ПОВЕСТКА ДНЯ:")
        lines.append("-" * 40)
        for i, item in enumerate(agenda, 1):
            lines.append(f"  {i}. {item}")
        lines.append("")

    # Discussion
    discussion = data.get("discussion", [])
    if discussion:
        lines.append("-" * 40)
        lines.append("ХОД СОВЕЩАНИЯ:")
        lines.append("-" * 40)
        for item in discussion:
            if isinstance(item, dict):
                lines.append(f"\n  СЛУШАЛИ: {item.get('topic', '')}")
                if item.get("speaker"):
                    lines.append(f"  Докладчик: {item['speaker']}")
                lines.append(f"  {item.get('summary', '')}")
            else:
                lines.append(f"  {item}")
        lines.append("")

    # Decisions
    decisions = data.get("decisions", [])
    if decisions:
        lines.append("-" * 40)
        lines.append("РЕШЕНИЯ:")
        lines.append("-" * 40)
        for d in decisions:
            if isinstance(d, dict):
                num = d.get("number", "")
                lines.append(f"  {num}. {d.get('text', '')}")
                if d.get("responsible"):
                    lines.append(f"     Ответственный: {d['responsible']}")
                if d.get("deadline"):
                    lines.append(f"     Срок: {d['deadline']}")
            else:
                lines.append(f"  - {d}")
        lines.append("")

    # Action items
    actions = data.get("action_items", [])
    if actions:
        lines.append("-" * 40)
        lines.append("ЗАДАЧИ НА КОНТРОЛЕ:")
        lines.append("-" * 40)
        lines.append(f"  {'N':<4} {'Задача':<35} {'Ответственный':<20} {'Срок':<15}")
        lines.append(f"  {'—'*4} {'—'*35} {'—'*20} {'—'*15}")
        for i, a in enumerate(actions, 1):
            if isinstance(a, dict):
                lines.append(
                    f"  {i:<4} {a.get('task', ''):<35} "
                    f"{a.get('assignee', ''):<20} {a.get('deadline', ''):<15}"
                )
            else:
                lines.append(f"  {i}. {a}")
        lines.append("")

    lines.append("=" * 60)
    if header.get("chairman"):
        lines.append(f"Председатель: _____________ / {header['chairman']} /")
    if header.get("secretary"):
        lines.append(f"Секретарь:    _____________ / {header['secretary']} /")
    lines.append("=" * 60)

    return "\n".join(lines)


async def identify_speakers(
    transcript: str,
    speaker_count: int = 2,
    participant_names: list[str] = None,
) -> str:
    """Use Ollama to identify and label speakers in a transcript."""
    names_hint = ""
    if participant_names:
        names_hint = f"\nИзвестные участники: {', '.join(participant_names)}. Используй их реальные имена вместо 'Спикер N', если можешь определить кто говорит."

    prompt = f"""Ты — ИИ-ассистент для распознавания спикеров в стенограммах совещаний.
В совещании участвовали {speaker_count} спикера(ов).{names_hint}

Проанализируй транскрипт и перепиши его, разбив по репликам каждого спикера.
Каждая реплика должна быть на новой строке в формате:

[ЧЧ:ММ:СС] Имя_Спикера: текст реплики

Если в транскрипте есть таймкоды — сохрани их. Если нет — не добавляй.
Определи смену спикера по контексту: вопросы/ответы, смена темы, обращения по имени.

Транскрипт:
---
{transcript}
---

Верни ТОЛЬКО переписанный транскрипт с метками спикеров (без пояснений)."""

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
