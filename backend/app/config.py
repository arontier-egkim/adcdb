from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+asyncmy://adcdb:adcdb_pass@127.0.0.1:3306/adcdb"
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000", "http://localhost:3001"]
    PORT: int = 8001
    STRUCTURES_DIR: str = "structures"

    model_config = {"env_prefix": "ADCDB_"}


settings = Settings()
