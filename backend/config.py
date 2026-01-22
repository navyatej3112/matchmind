from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://matchmind:matchmind@db:5432/matchmind"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

