from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CommonSettings(BaseSettings):
    """Общие настройки"""
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra="allow"
    )

    ADMINS: str
    USERNAMES: str
    BOT_TOKEN: str
    OPENAI_API_KEY: str
    DRY_MODE: bool

    @field_validator("USERNAMES")
    def check_username(cls, usernames: str) -> str:
        names = [i.strip() for i in usernames.strip().split(",")]
        if len(names) == 0:
            raise ValueError("Не указаны имена пользователей")
        return " ".join(names)


class PGSettings(BaseSettings):
    """Настройки для подключения к БД"""
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra="allow"
    )

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_URL: str
    POSTGRES_DB: str
    PG_PORT: str

    def db_connection_sync(self) -> str:
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_URL}:{self.PG_PORT}/{self.POSTGRES_DB}"

    def db_connection_async(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_URL}:{self.PG_PORT}/{self.POSTGRES_DB}"
