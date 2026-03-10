from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TimesheetEntry
from app.schemas import TimesheetCreate, TimesheetUpdate, TimesheetOut

router = APIRouter(prefix="/api/timesheet", tags=["timesheet"])

STANDARD_HOURS = 8.0


def _calc_hours(entry: TimesheetEntry):
    if entry.clock_in and entry.clock_out:
        dt_in = datetime.combine(date.today(), entry.clock_in)
        dt_out = datetime.combine(date.today(), entry.clock_out)
        diff = (dt_out - dt_in).total_seconds() / 3600.0
        total = max(0, diff - entry.break_minutes / 60.0)
        entry.total_hours = round(total, 2)
        entry.overtime_hours = round(max(0, total - STANDARD_HOURS), 2)


@router.get("/", response_model=list[TimesheetOut])
def list_entries(
    employee_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
):
    q = db.query(TimesheetEntry)
    if employee_id:
        q = q.filter(TimesheetEntry.employee_id == employee_id)
    if date_from:
        q = q.filter(TimesheetEntry.date >= date_from)
    if date_to:
        q = q.filter(TimesheetEntry.date <= date_to)
    return q.order_by(TimesheetEntry.date.desc()).all()


@router.get("/{entry_id}", response_model=TimesheetOut)
def get_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(TimesheetEntry).filter(TimesheetEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return entry


@router.post("/", response_model=TimesheetOut)
def create_entry(data: TimesheetCreate, db: Session = Depends(get_db)):
    entry = TimesheetEntry(**data.model_dump())
    _calc_hours(entry)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.put("/{entry_id}", response_model=TimesheetOut)
def update_entry(entry_id: int, data: TimesheetUpdate, db: Session = Depends(get_db)):
    entry = db.query(TimesheetEntry).filter(TimesheetEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(entry, key, value)
    _calc_hours(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}")
def delete_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(TimesheetEntry).filter(TimesheetEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    db.delete(entry)
    db.commit()
    return {"detail": "Запись удалена"}


@router.post("/clock-in")
def clock_in(employee_id: int, db: Session = Depends(get_db)):
    """Quick clock-in for today."""
    today = date.today()
    existing = db.query(TimesheetEntry).filter(
        TimesheetEntry.employee_id == employee_id,
        TimesheetEntry.date == today,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Уже отмечен приход на сегодня")
    entry = TimesheetEntry(
        employee_id=employee_id,
        date=today,
        clock_in=datetime.now().time(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"detail": "Приход отмечен", "id": entry.id}


@router.post("/clock-out")
def clock_out(employee_id: int, db: Session = Depends(get_db)):
    """Quick clock-out for today."""
    today = date.today()
    entry = db.query(TimesheetEntry).filter(
        TimesheetEntry.employee_id == employee_id,
        TimesheetEntry.date == today,
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Нет записи прихода на сегодня")
    entry.clock_out = datetime.now().time()
    _calc_hours(entry)
    db.commit()
    return {"detail": "Уход отмечен", "total_hours": entry.total_hours}
