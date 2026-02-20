from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    BASE_URL: str = "http://localhost:8000"
    DATABASE_URL: str = "sqlite+aiosqlite:///data/db.sqlite3"

    # Admin
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "changeme"

    # JWT
    JWT_SECRET: str = "change-this-to-a-random-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 5
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Short codes
    SHORT_CODE_LENGTH: int = 8

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
