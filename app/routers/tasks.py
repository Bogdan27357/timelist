from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Task, TaskStatus
from app.schemas import TaskCreate, TaskUpdate, TaskOut

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("/", response_model=list[TaskOut])
def list_tasks(
    meeting_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Task)
    if meeting_id:
        q = q.filter(Task.meeting_id == meeting_id)
    if assignee_id:
        q = q.filter(Task.assignee_id == assignee_id)
    if status:
        q = q.filter(Task.status == status)
    return q.order_by(Task.created_at.desc()).all()


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task


@router.post("/", response_model=TaskOut)
def create_task(data: TaskCreate, db: Session = Depends(get_db)):
    task = Task(**data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.put("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    if task.status == TaskStatus.DONE and not task.completed_at:
        task.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    db.delete(task)
    db.commit()
    return {"detail": "Задача удалена"}
