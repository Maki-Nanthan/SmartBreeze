from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Smart Classroom Edge AI System")
    api_prefix: str = os.getenv("API_PREFIX", "/api")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    cors_origins: list[str] = field(default_factory=lambda: os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
    ).split(","))
    medium_threshold: int = int(os.getenv("OCCUPANCY_MEDIUM_THRESHOLD", "3"))
    high_threshold: int = int(os.getenv("OCCUPANCY_HIGH_THRESHOLD", "10"))
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./smartclassroom.db")


settings = Settings()
