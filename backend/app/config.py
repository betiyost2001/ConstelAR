from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    # JWT
    JWT_SECRET: str
    JWT_ALG: str = "HS256"
    ACCESS_TTL_MIN: int = 15
    REFRESH_TTL_DAYS: int = 7
    # Cookies/CORS
    COOKIE_SECURE: bool = False
    ALLOWED_ORIGINS: str = "http://localhost:5173"
#    Email
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str | None = None
    SMTP_PASS: str | None = None
    MAIL_FROM: str
    FRONTEND_BASE_URL: str
# Misc
    APP_ENV: str = "dev"


    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()