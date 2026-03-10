from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, EmailStr


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
