from __future__ import annotations

import os
from datetime import date, datetime
from typing import Generator, Literal

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Date, DateTime, Integer, String, Text, and_, create_engine, func, or_, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


Status = Literal["saved", "applied", "interview", "rejected", "offer"]
SortOrder = Literal["asc", "desc"]

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./jobtrackr.db",
)

engine_kwargs: dict[str, object] = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    date_applied: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    next_action_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)


Base.metadata.create_all(bind=engine)


def run_migrations() -> None:
    if not DATABASE_URL.startswith("sqlite"):
        return

    with engine.begin() as connection:
        columns = {
            row[1] for row in connection.exec_driver_sql("PRAGMA table_info(applications)").fetchall()
        }

        if "next_action_date" not in columns:
            connection.exec_driver_sql("ALTER TABLE applications ADD COLUMN next_action_date DATE")

        if "deleted_at" not in columns:
            connection.exec_driver_sql("ALTER TABLE applications ADD COLUMN deleted_at DATETIME")


run_migrations()


class ApplicationCreate(BaseModel):
    company: str = Field(min_length=1, max_length=200)
    role: str = Field(min_length=1, max_length=200)
    location: str | None = Field(default=None, max_length=200)
    url: str | None = Field(default=None, max_length=500)
    status: Status = "applied"
    date_applied: date
    next_action_date: date | None = None
    notes: str | None = None


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company: str
    role: str
    location: str | None
    url: str | None
    status: Status
    date_applied: date
    next_action_date: date | None
    notes: str | None
    created_at: datetime


class ApplicationListOut(BaseModel):
    items: list[ApplicationOut]
    total: int


class StatsOut(BaseModel):
    total: int
    counts: dict[str, int]
    response_rate: float
    due_today: int
    saved_jobs: int
    interviews: int


class ApplicationStatusUpdate(BaseModel):
    status: Status


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI(title="ApplyIntel API", version="1.0.0")

raw_origins = os.getenv("ALLOWED_ORIGINS")
if raw_origins:
    allowed_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
else:
    allowed_origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/applications", response_model=ApplicationOut, status_code=201)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)) -> Application:
    application = Application(**payload.model_dump())
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@app.get("/applications", response_model=ApplicationListOut)
def list_applications(
    q: str | None = Query(default=None, description="Search by company/role"),
    status: Status | None = Query(default=None, description="Filter by status"),
    has_link: bool | None = Query(default=None, description="Filter rows with link present/absent"),
    sort_order: SortOrder = Query(default="desc", description="Sort by date_applied"),
    limit: int = Query(default=20, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    include_deleted: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> list[Application]:
    query = select(Application)

    filters = []
    if not include_deleted:
        filters.append(Application.deleted_at.is_(None))

    if q:
        term = f"%{q.strip()}%"
        filters.append(or_(Application.company.ilike(term), Application.role.ilike(term)))

    if status:
        filters.append(Application.status == status)

    if has_link is True:
        filters.append(and_(Application.url.is_not(None), Application.url != ""))
    elif has_link is False:
        filters.append(or_(Application.url.is_(None), Application.url == ""))

    if filters:
        query = query.where(*filters)

    if sort_order == "asc":
        query = query.order_by(Application.date_applied.asc(), Application.created_at.asc())
    else:
        query = query.order_by(Application.date_applied.desc(), Application.created_at.desc())

    total_query = select(func.count()).select_from(Application)
    if filters:
        total_query = total_query.where(*filters)

    total = db.execute(total_query).scalar_one()

    query = query.limit(limit).offset(offset)
    items = list(db.scalars(query).all())

    return ApplicationListOut(items=items, total=total)


@app.patch("/applications/{application_id}", response_model=ApplicationOut)
def update_application_status(
    application_id: int,
    payload: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
) -> Application:
    application = db.get(Application, application_id)
    if application is None or application.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Application not found")

    application.status = payload.status
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@app.delete("/applications/{application_id}", response_model=ApplicationOut)
def delete_application(application_id: int, db: Session = Depends(get_db)) -> Application:
    application = db.get(Application, application_id)
    if application is None or application.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Application not found")

    application.deleted_at = datetime.utcnow()
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@app.post("/applications/{application_id}/restore", response_model=ApplicationOut)
def restore_application(application_id: int, db: Session = Depends(get_db)) -> Application:
    application = db.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    if application.deleted_at is None:
        raise HTTPException(status_code=400, detail="Application is not deleted")

    application.deleted_at = None
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@app.get("/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db)) -> StatsOut:
    rows = list(
        db.execute(
            select(Application.status, Application.next_action_date).where(Application.deleted_at.is_(None))
        ).all()
    )

    total = len(rows)
    counts: dict[str, int] = {}
    due_today = 0
    today = date.today()

    for status, next_action_date in rows:
        counts[status] = counts.get(status, 0) + 1
        if next_action_date == today:
            due_today += 1

    responded = counts.get("interview", 0) + counts.get("offer", 0) + counts.get("rejected", 0)
    response_rate = (responded / total) if total else 0.0

    return StatsOut(
        total=total,
        counts=counts,
        response_rate=round(response_rate, 4),
        due_today=due_today,
        saved_jobs=counts.get("saved", 0),
        interviews=counts.get("interview", 0),
    )
