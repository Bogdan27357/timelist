from datetime import date, datetime, time
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, Integer, String, Date, Time, DateTime, Text, Float,
    ForeignKey, Enum, Boolean,
)
from sqlalchemy.orm import relationship

from app.database import Base


class AbsenceType(str, PyEnum):
    VACATION = "vacation"
    SICK_LEAVE = "sick_leave"
    BUSINESS_TRIP = "business_trip"
    REMOTE = "remote"
    DAY_OFF = "day_off"
    OTHER = "other"


class AbsenceStatus(str, PyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class TaskStatus(str, PyEnum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskPriority(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TranscriptionStatus(str, PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    position = Column(String(255), default="")
    department = Column(String(255), default="")
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(50), default="")
    hire_date = Column(Date, default=date.today)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    timesheet_entries = relationship("TimesheetEntry", back_populates="employee")
    absences = relationship("Absence", back_populates="employee")
    calls = relationship("Call", back_populates="employee")
    meeting_participations = relationship("MeetingParticipant", back_populates="employee")
    assigned_tasks = relationship("Task", back_populates="assignee", foreign_keys="Task.assignee_id")


class TimesheetEntry(Base):
    __tablename__ = "timesheet_entries"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    date = Column(Date, nullable=False)
    clock_in = Column(Time, nullable=True)
    clock_out = Column(Time, nullable=True)
    break_minutes = Column(Integer, default=0)
    total_hours = Column(Float, default=0.0)
    overtime_hours = Column(Float, default=0.0)
    note = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="timesheet_entries")


class Absence(Base):
    __tablename__ = "absences"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    absence_type = Column(Enum(AbsenceType), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(Enum(AbsenceStatus), default=AbsenceStatus.PENDING)
    reason = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="absences")


class Meeting(Base):
    """Мероприятие / совещание — карточка встречи как в 1С:ДО."""
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, default="")
    meeting_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=60)
    location = Column(String(255), default="")
    organizer_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    # Audio & transcription
    audio_file_path = Column(String(500), default="")
    speaker_count = Column(Integer, default=2)
    transcription_status = Column(Enum(TranscriptionStatus), default=TranscriptionStatus.PENDING)
    transcript = Column(Text, default="")
    stenogram = Column(Text, default="")
    # AI protocol
    ai_protocol = Column(Text, default="")
    ai_summary = Column(Text, default="")
    ai_action_items = Column(Text, default="")
    ai_key_topics = Column(Text, default="")
    ai_decisions = Column(Text, default="")
    ai_sentiment = Column(String(50), default="")
    is_protocol_generated = Column(Boolean, default=False)
    is_protocol_transferred = Column(Boolean, default=False)
    # Final protocol
    final_protocol = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    participants = relationship("MeetingParticipant", back_populates="meeting", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="meeting", cascade="all, delete-orphan")


class MeetingParticipant(Base):
    """Участник мероприятия с ролью (как спикер в Таймлист)."""
    __tablename__ = "meeting_participants"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    name = Column(String(255), default="")
    role = Column(String(100), default="Участник")
    speaker_label = Column(String(50), default="")

    meeting = relationship("Meeting", back_populates="participants")
    employee = relationship("Employee", back_populates="meeting_participations")


class Task(Base):
    """Задача из протокола — постановка на контроль."""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, default="")
    assignee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    assignee_name = Column(String(255), default="")
    status = Column(Enum(TaskStatus), default=TaskStatus.NEW)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    due_date = Column(Date, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    meeting = relationship("Meeting", back_populates="tasks")
    assignee = relationship("Employee", back_populates="assigned_tasks", foreign_keys=[assignee_id])


class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    title = Column(String(500), default="")
    call_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=0)
    participants = Column(Text, default="")
    transcript = Column(Text, default="")
    audio_file_path = Column(String(500), default="")
    # AI analysis results
    ai_summary = Column(Text, default="")
    ai_action_items = Column(Text, default="")
    ai_sentiment = Column(String(50), default="")
    ai_key_topics = Column(Text, default="")
    ai_decisions = Column(Text, default="")
    is_analyzed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="calls")
