from datetime import date, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Employee, TimesheetEntry, Absence, Call, AbsenceType, AbsenceStatus
from app.schemas import DashboardStats

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    today = date.today()
    month_start = today.replace(day=1)

    total_employees = db.query(Employee).filter(Employee.is_active == True).count()

    active_today = db.query(TimesheetEntry).filter(
        TimesheetEntry.date == today
    ).count()

    on_vacation = db.query(Absence).filter(
        Absence.absence_type == AbsenceType.VACATION,
        Absence.status == AbsenceStatus.APPROVED,
        Absence.start_date <= today,
        Absence.end_date >= today,
    ).count()

    on_sick_leave = db.query(Absence).filter(
        Absence.absence_type == AbsenceType.SICK_LEAVE,
        Absence.status == AbsenceStatus.APPROVED,
        Absence.start_date <= today,
        Absence.end_date >= today,
    ).count()

    total_calls = db.query(Call).filter(
        Call.call_date >= datetime.combine(month_start, datetime.min.time())
    ).count()

    analyzed_calls = db.query(Call).filter(
        Call.call_date >= datetime.combine(month_start, datetime.min.time()),
        Call.is_analyzed == True,
    ).count()

    avg_hours_result = db.query(func.avg(TimesheetEntry.total_hours)).filter(
        TimesheetEntry.date == today
    ).scalar()

    return DashboardStats(
        total_employees=total_employees,
        active_today=active_today,
        on_vacation=on_vacation,
        on_sick_leave=on_sick_leave,
        total_calls_this_month=total_calls,
        analyzed_calls=analyzed_calls,
        avg_hours_today=round(avg_hours_result or 0, 2),
    )


@router.get("/calendar")
def get_calendar_data(
    year: int = None,
    month: int = None,
    db: Session = Depends(get_db),
):
    """Get calendar data with absences and calls for a given month."""
    today = date.today()
    year = year or today.year
    month = month or today.month

    month_start = date(year, month, 1)
    if month == 12:
        month_end = date(year + 1, 1, 1)
    else:
        month_end = date(year, month + 1, 1)

    absences = db.query(Absence).filter(
        Absence.start_date < month_end,
        Absence.end_date >= month_start,
        Absence.status == AbsenceStatus.APPROVED,
    ).all()

    calls = db.query(Call).filter(
        Call.call_date >= datetime.combine(month_start, datetime.min.time()),
        Call.call_date < datetime.combine(month_end, datetime.min.time()),
    ).all()

    events = []
    for a in absences:
        emp = db.query(Employee).filter(Employee.id == a.employee_id).first()
        events.append({
            "type": "absence",
            "absence_type": a.absence_type.value if hasattr(a.absence_type, 'value') else a.absence_type,
            "start": a.start_date.isoformat(),
            "end": a.end_date.isoformat(),
            "employee": emp.full_name if emp else "—",
        })
    for c in calls:
        events.append({
            "type": "call",
            "title": c.title,
            "date": c.call_date.isoformat(),
            "duration": c.duration_minutes,
            "analyzed": c.is_analyzed,
        })

    return {"year": year, "month": month, "events": events}
