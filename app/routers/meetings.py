import os
import json
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Meeting, MeetingParticipant, Task, Employee, TranscriptionStatus, TaskStatus
from app.schemas import MeetingCreate, MeetingUpdate, MeetingOut, MeetingParticipantCreate
from app.services.ollama_service import generate_protocol, identify_speakers, check_ollama_status
from app.config import UPLOAD_DIR

router = APIRouter(prefix="/api/meetings", tags=["meetings"])

ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a", ".flac", ".webm", ".mp4", ".wma"}


@router.get("/", response_model=list[MeetingOut])
def list_meetings(db: Session = Depends(get_db)):
    return db.query(Meeting).order_by(Meeting.meeting_date.desc()).all()


@router.get("/{meeting_id}", response_model=MeetingOut)
def get_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    return meeting


@router.post("/", response_model=MeetingOut)
def create_meeting(data: MeetingCreate, db: Session = Depends(get_db)):
    participants_data = data.participants
    meeting_dict = data.model_dump(exclude={"participants"})
    meeting = Meeting(**meeting_dict)
    db.add(meeting)
    db.flush()

    for p in participants_data:
        part = MeetingParticipant(meeting_id=meeting.id, **p.model_dump())
        if part.employee_id and not part.name:
            emp = db.query(Employee).filter(Employee.id == part.employee_id).first()
            if emp:
                part.name = emp.full_name
        db.add(part)

    db.commit()
    db.refresh(meeting)
    return meeting


@router.put("/{meeting_id}", response_model=MeetingOut)
def update_meeting(meeting_id: int, data: MeetingUpdate, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(meeting, key, value)
    db.commit()
    db.refresh(meeting)
    return meeting


@router.delete("/{meeting_id}")
def delete_meeting(meeting_id: int, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    # Delete audio file if exists
    if meeting.audio_file_path and os.path.exists(meeting.audio_file_path):
        os.remove(meeting.audio_file_path)
    db.delete(meeting)
    db.commit()
    return {"detail": "Мероприятие удалено"}


# --- Step 1: Upload audio ---
@router.post("/{meeting_id}/upload-audio")
async def upload_audio(
    meeting_id: int,
    file: UploadFile = File(...),
    speaker_count: int = Form(2),
    db: Session = Depends(get_db),
):
    """Шаг 3: Прикрепить аудиофайл к мероприятию."""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Формат {ext} не поддерживается. Допустимые: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}"
        )

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe_name = f"meeting_{meeting_id}_{int(datetime.now().timestamp())}{ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_name)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    meeting.audio_file_path = file_path
    meeting.speaker_count = speaker_count
    meeting.transcription_status = TranscriptionStatus.PENDING
    db.commit()

    return {
        "detail": "Аудиофайл загружен",
        "file_path": file_path,
        "size_mb": round(len(content) / 1024 / 1024, 2),
    }


# --- Step 2: Transcribe (Whisper) ---
@router.post("/{meeting_id}/transcribe")
async def transcribe_meeting(meeting_id: int, db: Session = Depends(get_db)):
    """Запустить сервис расшифровки (Whisper) — получить стенограмму."""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    if not meeting.audio_file_path or not os.path.exists(meeting.audio_file_path):
        raise HTTPException(status_code=400, detail="Аудиофайл не найден")

    meeting.transcription_status = TranscriptionStatus.PROCESSING
    db.commit()

    try:
        from app.services.whisper_service import transcribe_audio
        result = await transcribe_audio(
            meeting.audio_file_path,
            speaker_count=meeting.speaker_count,
        )

        meeting.transcript = result["text"]
        meeting.stenogram = result["stenogram"]
        meeting.transcription_status = TranscriptionStatus.DONE

        # Update duration if not set
        if result.get("duration_seconds") and not meeting.duration_minutes:
            meeting.duration_minutes = int(result["duration_seconds"] / 60)

        db.commit()
        db.refresh(meeting)
        return {
            "detail": "Расшифровка завершена",
            "duration_seconds": result.get("duration_seconds", 0),
            "language": result.get("language", ""),
            "transcript_length": len(meeting.transcript),
        }
    except Exception as e:
        meeting.transcription_status = TranscriptionStatus.ERROR
        db.commit()
        raise HTTPException(status_code=500, detail=f"Ошибка расшифровки: {e}")


# --- Step 3: Speaker diarization (Ollama) ---
@router.post("/{meeting_id}/diarize")
async def diarize_meeting(meeting_id: int, db: Session = Depends(get_db)):
    """Определить спикеров в транскрипте с помощью ИИ."""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    if not meeting.transcript:
        raise HTTPException(status_code=400, detail="Сначала выполните расшифровку")

    result = await identify_speakers(meeting.transcript, meeting.speaker_count)
    meeting.stenogram = result
    db.commit()
    return {"detail": "Диаризация завершена", "stenogram": result}


# --- Step 4: Generate auto-protocol (Ollama) ---
@router.post("/{meeting_id}/generate-protocol")
async def generate_protocol_endpoint(meeting_id: int, db: Session = Depends(get_db)):
    """Получить автопротокол — ИИ создаёт протокол с задачами."""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")

    transcript = meeting.stenogram or meeting.transcript
    if not transcript:
        raise HTTPException(status_code=400, detail="Нет транскрипта для генерации протокола")

    # Build participants info
    participants_info = ""
    if meeting.participants:
        parts = []
        for p in meeting.participants:
            name = p.name or f"Участник {p.id}"
            parts.append(f"{name} ({p.role})")
        participants_info = ", ".join(parts)

    result = await generate_protocol(
        transcript=transcript,
        title=meeting.title,
        participants_info=participants_info,
        meeting_date=meeting.meeting_date.strftime("%d.%m.%Y %H:%M") if meeting.meeting_date else "",
    )

    meeting.ai_protocol = result.get("protocol", "")
    meeting.ai_summary = result.get("summary", "")
    meeting.ai_key_topics = result.get("key_topics", "")
    meeting.ai_decisions = result.get("decisions", "")
    meeting.ai_sentiment = result.get("sentiment", "neutral")
    meeting.is_protocol_generated = True

    # Save action items as text
    action_items = result.get("action_items", [])
    if isinstance(action_items, list):
        items_text = []
        for item in action_items:
            if isinstance(item, dict):
                task_text = item.get("task", "")
                assignee = item.get("assignee", "")
                deadline = item.get("deadline", "")
                items_text.append(f"- {task_text} ({assignee}) [{deadline}]")
            else:
                items_text.append(f"- {item}")
        meeting.ai_action_items = "\n".join(items_text)
    else:
        meeting.ai_action_items = str(action_items)

    db.commit()
    db.refresh(meeting)
    return meeting


# --- Step 5: Transfer protocol & create tasks ---
@router.post("/{meeting_id}/transfer-protocol")
async def transfer_protocol(meeting_id: int, db: Session = Depends(get_db)):
    """Перенести автопротокол в итоговый и создать задачи на контроль."""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    if not meeting.ai_protocol:
        raise HTTPException(status_code=400, detail="Сначала сгенерируйте автопротокол")

    # Transfer protocol
    meeting.final_protocol = meeting.ai_protocol
    meeting.is_protocol_transferred = True

    # Parse action items and create tasks
    if meeting.ai_action_items:
        lines = meeting.ai_action_items.strip().split("\n")
        for line in lines:
            line = line.strip().lstrip("- ")
            if not line:
                continue
            # Try to extract assignee from parentheses
            assignee_name = ""
            title = line
            if "(" in line and ")" in line:
                idx_start = line.rfind("(")
                idx_end = line.rfind(")")
                assignee_name = line[idx_start + 1:idx_end].strip()
                title = line[:idx_start].strip()
                # Remove deadline brackets if present
                if "[" in title:
                    title = title[:title.rfind("[")].strip()

            # Try to find employee by name
            assignee_id = None
            if assignee_name:
                emp = db.query(Employee).filter(
                    Employee.full_name.ilike(f"%{assignee_name}%")
                ).first()
                if emp:
                    assignee_id = emp.id

            task = Task(
                meeting_id=meeting.id,
                title=title,
                assignee_id=assignee_id,
                assignee_name=assignee_name,
                status=TaskStatus.NEW,
            )
            db.add(task)

    db.commit()
    db.refresh(meeting)
    return {"detail": "Протокол перенесён, задачи созданы"}


# --- Add participant ---
@router.post("/{meeting_id}/participants")
def add_participant(meeting_id: int, data: MeetingParticipantCreate, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")

    part = MeetingParticipant(meeting_id=meeting_id, **data.model_dump())
    if part.employee_id and not part.name:
        emp = db.query(Employee).filter(Employee.id == part.employee_id).first()
        if emp:
            part.name = emp.full_name
    db.add(part)
    db.commit()
    db.refresh(part)
    return part


@router.delete("/{meeting_id}/participants/{participant_id}")
def remove_participant(meeting_id: int, participant_id: int, db: Session = Depends(get_db)):
    part = db.query(MeetingParticipant).filter(
        MeetingParticipant.id == participant_id,
        MeetingParticipant.meeting_id == meeting_id,
    ).first()
    if not part:
        raise HTTPException(status_code=404, detail="Участник не найден")
    db.delete(part)
    db.commit()
    return {"detail": "Участник удалён"}


# --- Upload transcript text ---
@router.post("/{meeting_id}/upload-transcript")
async def upload_transcript(
    meeting_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Загрузить текстовый транскрипт (.txt) вместо аудио."""
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")

    content = await file.read()
    text = content.decode("utf-8", errors="replace")
    meeting.transcript = text
    meeting.stenogram = text
    meeting.transcription_status = TranscriptionStatus.DONE
    db.commit()
    return {"detail": "Транскрипт загружен"}
