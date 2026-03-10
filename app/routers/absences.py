from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Absence
from app.schemas import AbsenceCreate, AbsenceUpdate, AbsenceOut

router = APIRouter(prefix="/api/absences", tags=["absences"])


@router.get("/", response_model=list[AbsenceOut])
def list_absences(
    employee_id: Optional[int] = None,
    absence_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Absence)
    if employee_id:
        q = q.filter(Absence.employee_id == employee_id)
    if absence_type:
        q = q.filter(Absence.absence_type == absence_type)
    if status:
        q = q.filter(Absence.status == status)
    return q.order_by(Absence.start_date.desc()).all()


@router.post("/", response_model=AbsenceOut)
def create_absence(data: AbsenceCreate, db: Session = Depends(get_db)):
    absence = Absence(**data.model_dump())
    db.add(absence)
    db.commit()
    db.refresh(absence)
    return absence


@router.put("/{absence_id}", response_model=AbsenceOut)
def update_absence(absence_id: int, data: AbsenceUpdate, db: Session = Depends(get_db)):
    absence = db.query(Absence).filter(Absence.id == absence_id).first()
    if not absence:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(absence, key, value)
    db.commit()
    db.refresh(absence)
    return absence


@router.delete("/{absence_id}")
def delete_absence(absence_id: int, db: Session = Depends(get_db)):
    absence = db.query(Absence).filter(Absence.id == absence_id).first()
    if not absence:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    db.delete(absence)
    db.commit()
    return {"detail": "Запись удалена"}
