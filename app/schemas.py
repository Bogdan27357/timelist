from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel


# --- Employee ---
class EmployeeCreate(BaseModel):
    full_name: str
    position: str = ""
    department: str = ""
    email: str
    phone: str = ""
    hire_date: Optional[date] = None


class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    position: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class EmployeeOut(BaseModel):
    id: int
    full_name: str
    position: str
    department: str
    email: str
    phone: str
    hire_date: Optional[date]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Timesheet ---
class TimesheetCreate(BaseModel):
    employee_id: int
    date: date
    clock_in: Optional[time] = None
    clock_out: Optional[time] = None
    break_minutes: int = 0
    note: str = ""


class TimesheetUpdate(BaseModel):
    clock_in: Optional[time] = None
    clock_out: Optional[time] = None
    break_minutes: Optional[int] = None
    note: Optional[str] = None


class TimesheetOut(BaseModel):
    id: int
    employee_id: int
    date: date
    clock_in: Optional[time]
    clock_out: Optional[time]
    break_minutes: int
    total_hours: float
    overtime_hours: float
    note: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Absence ---
class AbsenceCreate(BaseModel):
    employee_id: int
    absence_type: str
    start_date: date
    end_date: date
    reason: str = ""


class AbsenceUpdate(BaseModel):
    status: Optional[str] = None
    reason: Optional[str] = None


class AbsenceOut(BaseModel):
    id: int
    employee_id: int
    absence_type: str
    start_date: date
    end_date: date
    status: str
    reason: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Meeting Participant ---
class MeetingParticipantCreate(BaseModel):
    employee_id: Optional[int] = None
    name: str = ""
    role: str = "Участник"
    speaker_label: str = ""


class MeetingParticipantOut(BaseModel):
    id: int
    meeting_id: int
    employee_id: Optional[int]
    name: str
    role: str
    speaker_label: str

    model_config = {"from_attributes": True}


# --- Meeting ---
class MeetingCreate(BaseModel):
    title: str
    description: str = ""
    meeting_date: datetime
    duration_minutes: int = 60
    location: str = ""
    organizer_id: Optional[int] = None
    speaker_count: int = 2
    participants: list[MeetingParticipantCreate] = []


class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    meeting_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    location: Optional[str] = None
    speaker_count: Optional[int] = None
    final_protocol: Optional[str] = None


class MeetingOut(BaseModel):
    id: int
    title: str
    description: str
    meeting_date: datetime
    duration_minutes: int
    location: str
    organizer_id: Optional[int]
    audio_file_path: str
    speaker_count: int
    transcription_status: str
    transcript: str
    stenogram: str
    ai_protocol: str
    ai_summary: str
    ai_action_items: str
    ai_key_topics: str
    ai_decisions: str
    ai_sentiment: str
    is_protocol_generated: bool
    is_protocol_transferred: bool
    final_protocol: str
    created_at: datetime
    participants: list[MeetingParticipantOut] = []

    model_config = {"from_attributes": True}


# --- Task ---
class TaskCreate(BaseModel):
    meeting_id: Optional[int] = None
    title: str
    description: str = ""
    assignee_id: Optional[int] = None
    assignee_name: str = ""
    priority: str = "medium"
    due_date: Optional[date] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    assignee_name: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None


class TaskOut(BaseModel):
    id: int
    meeting_id: Optional[int]
    title: str
    description: str
    assignee_id: Optional[int]
    assignee_name: str
    status: str
    priority: str
    due_date: Optional[date]
    completed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Call ---
class CallCreate(BaseModel):
    employee_id: Optional[int] = None
    title: str = ""
    call_date: datetime
    duration_minutes: int = 0
    participants: str = ""
    transcript: str = ""


class CallOut(BaseModel):
    id: int
    employee_id: Optional[int]
    title: str
    call_date: datetime
    duration_minutes: int
    participants: str
    transcript: str
    ai_summary: str
    ai_action_items: str
    ai_sentiment: str
    ai_key_topics: str
    ai_decisions: str
    is_analyzed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Dashboard ---
class DashboardStats(BaseModel):
    total_employees: int
    active_today: int
    on_vacation: int
    on_sick_leave: int
    total_calls_this_month: int
    analyzed_calls: int
    avg_hours_today: float
    total_meetings: int
    total_tasks: int
    tasks_overdue: int
