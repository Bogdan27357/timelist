import os
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Call
from app.schemas import CallCreate, CallOut
from app.services.ollama_service import analyze_call, check_ollama_status
from app.config import UPLOAD_DIR

router = APIRouter(prefix="/api/calls", tags=["calls"])


@router.get("/", response_model=list[CallOut])
def list_calls(
    employee_id: Optional[int] = None,
    analyzed_only: bool = False,
    db: Session = Depends(get_db),
):
    q = db.query(Call)
    if employee_id:
        q = q.filter(Call.employee_id == employee_id)
    if analyzed_only:
        q = q.filter(Call.is_analyzed == True)
    return q.order_by(Call.call_date.desc()).all()


@router.get("/ollama-status")
async def get_ollama_status():
    return await check_ollama_status()


@router.get("/{call_id}", response_model=CallOut)
def get_call(call_id: int, db: Session = Depends(get_db)):
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Созвон не найден")
    return call


@router.post("/", response_model=CallOut)
def create_call(data: CallCreate, db: Session = Depends(get_db)):
    call = Call(**data.model_dump())
    db.add(call)
    db.commit()
    db.refresh(call)
    return call


@router.post("/upload")
async def upload_transcript(
    file: UploadFile = File(...),
    title: str = Form(""),
    employee_id: Optional[int] = Form(None),
    participants: str = Form(""),
    call_date: str = Form(""),
    db: Session = Depends(get_db),
):
    """Upload a transcript file (.txt) for analysis."""
    content = await file.read()
    transcript = content.decode("utf-8", errors="replace")

    parsed_date = datetime.now()
    if call_date:
        try:
            parsed_date = datetime.fromisoformat(call_date)
        except ValueError:
            pass

    call = Call(
        employee_id=employee_id,
        title=title or file.filename or "Без названия",
        call_date=parsed_date,
        participants=participants,
        transcript=transcript,
    )
    db.add(call)
    db.commit()
    db.refresh(call)
    return {"detail": "Транскрипт загружен", "call_id": call.id}


@router.post("/{call_id}/analyze", response_model=CallOut)
async def analyze_call_endpoint(call_id: int, db: Session = Depends(get_db)):
    """Run AI analysis on a call transcript using Ollama."""
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Созвон не найден")
    if not call.transcript:
        raise HTTPException(status_code=400, detail="Нет транскрипта для анализа")

    result = await analyze_call(call.transcript, call.title, call.participants)

    call.ai_summary = result.get("summary", "")
    call.ai_action_items = result.get("action_items", "")
    call.ai_sentiment = result.get("sentiment", "neutral")
    call.ai_key_topics = result.get("key_topics", "")
    call.ai_decisions = result.get("decisions", "")
    call.is_analyzed = True

    db.commit()
    db.refresh(call)
    return call


@router.delete("/{call_id}")
def delete_call(call_id: int, db: Session = Depends(get_db)):
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(status_code=404, detail="Созвон не найден")
    db.delete(call)
    db.commit()
    return {"detail": "Созвон удалён"}
