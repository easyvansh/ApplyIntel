from __future__ import annotations

import json
import logging
import os
import re
import time
import uuid
from contextlib import asynccontextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Generator, Literal

from alembic import command
from alembic.config import Config
from fastapi import Depends, FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Date, DateTime, Integer, String, Text, and_, create_engine, func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


Status = Literal["saved", "applied", "interview", "rejected", "offer"]
SortOrder = Literal["asc", "desc"]
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]+$")

request_logger = logging.getLogger("applyintel.requests")
if not request_logger.handlers:
    request_handler = logging.StreamHandler()
    request_handler.setFormatter(logging.Formatter("%(message)s"))
    request_logger.addHandler(request_handler)
request_logger.setLevel(logging.INFO)
request_logger.propagate = False
error_logger = logging.getLogger("applyintel.errors")


class APIError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)

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


ALEMBIC_INI_PATH = Path(__file__).with_name("alembic.ini")
ALEMBIC_SCRIPT_PATH = Path(__file__).with_name("alembic")


def run_database_migrations() -> None:
    config = Config(str(ALEMBIC_INI_PATH))
    config.set_main_option("script_location", str(ALEMBIC_SCRIPT_PATH))
    command.upgrade(config, "head")


@asynccontextmanager
async def lifespan(_: FastAPI):
    run_database_migrations()
    yield



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


app = FastAPI(title="ApplyIntel API", version="2.0.0", lifespan=lifespan)

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
    expose_headers=["X-Request-ID"],
)


def request_id_from_state(request: Request) -> str:
    return getattr(request.state, "request_id", str(uuid.uuid4()))


def error_response(request: Request, status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id_from_state(request),
            }
        },
    )


@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    return error_response(request, exc.status_code, exc.code, exc.message)


@app.exception_handler(Exception)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    error_logger.exception(
        "Unhandled API error request_id=%s path=%s",
        request_id_from_state(request),
        request.url.path,
        exc_info=exc,
    )
    return error_response(
        request,
        500,
        "INTERNAL_ERROR",
        "An unexpected error occurred.",
    )


def get_request_id(request: Request) -> str:
    supplied_request_id = request.headers.get("X-Request-ID", "").strip()
    if (
        supplied_request_id
        and len(supplied_request_id) <= 128
        and REQUEST_ID_PATTERN.fullmatch(supplied_request_id)
    ):
        return supplied_request_id
    return str(uuid.uuid4())


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = get_request_id(request)
    request.state.request_id = request_id
    started_at = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        log_method = request_logger.error if status_code >= 500 else request_logger.info
        log_method(
            json.dumps(
                {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": status_code,
                    "duration_ms": duration_ms,
                },
                separators=(",", ":"),
            )
        )


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.get("/health/live")
def health_live() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/health/ready")
def health_ready(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(select(1))
    except SQLAlchemyError as exc:
        raise APIError(503, "DATABASE_UNAVAILABLE", "Database is unavailable.") from exc

    return {"status": "ready", "database": "connected"}


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
        raise APIError(
            404,
            "APPLICATION_NOT_FOUND",
            f"Application {application_id} was not found.",
        )

    application.status = payload.status
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@app.delete("/applications/{application_id}", response_model=ApplicationOut)
def delete_application(application_id: int, db: Session = Depends(get_db)) -> Application:
    application = db.get(Application, application_id)
    if application is None or application.deleted_at is not None:
        raise APIError(
            404,
            "APPLICATION_NOT_FOUND",
            f"Application {application_id} was not found.",
        )

    application.deleted_at = datetime.utcnow()
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@app.post("/applications/{application_id}/restore", response_model=ApplicationOut)
def restore_application(application_id: int, db: Session = Depends(get_db)) -> Application:
    application = db.get(Application, application_id)
    if application is None:
        raise APIError(
            404,
            "APPLICATION_NOT_FOUND",
            f"Application {application_id} was not found.",
        )
    if application.deleted_at is None:
        raise APIError(
            409,
            "APPLICATION_NOT_DELETED",
            f"Application {application_id} is not deleted.",
        )

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
