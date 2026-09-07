import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api import categorize, chat, users
from src.config import settings
from src.exceptions import AppError

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Bootcamp Python AI Powered v1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


@app.middleware("http")
async def add_request_id(
    request: Request,
    call_next: Callable[[Request], Awaitable[JSONResponse]]
    ) -> JSONResponse:
    request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response


@app.exception_handler(AppError)
async def app_exception_handler(req: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "timestamp": datetime.now(UTC).isoformat(),
            "status": exc.status_code,
            "error": exc.code,
            "message": exc.message,
            "path": req.url.path,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    req: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "timestamp": datetime.now(UTC).isoformat(),
            "status": 422,
            "error": "VALIDATION_ERROR",
            "message": "Input non valido",
            "path": req.url.path,
            "details": [f"{e['loc'][-1]}: {e['msg']}" for e in exc.errors()],
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(req: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "timestamp": datetime.now(UTC).isoformat(),
            "status": 500,
            "error": "INTERNAL_ERROR",
            "message": "Errore inatteso",
            "path": req.url.path,
        },
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "UP"}


app.include_router(chat.router)
app.include_router(categorize.router)
app.include_router(users.router)
