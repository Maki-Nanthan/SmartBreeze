from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import http_exception_handler, validation_exception_handler
from app.database.database import init_db
from app.routers.classroom import router as classroom_router
from app.routers.health import router as health_router
from app.routers.persistence import router as persistence_router
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Backend foundation for the Smart Classroom Edge AI System",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(classroom_router, prefix=settings.api_prefix)
app.include_router(persistence_router, prefix=settings.api_prefix)

init_db()
