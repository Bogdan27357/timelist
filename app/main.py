import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.database import engine, Base
from app.routers import employees, timesheet, absences, calls, dashboard

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Таймлист",
    description="Учёт рабочего времени и ИИ-анализ созвонов",
    version="1.0.0",
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(employees.router)
app.include_router(timesheet.router)
app.include_router(absences.router)
app.include_router(calls.router)
app.include_router(dashboard.router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


def run():
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    run()
