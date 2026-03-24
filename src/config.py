from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):

    # DATA GENERATION SETTINGS

    OPENROUTER_API_KEY: str = Field(..., validation_alias="OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1/chat/completions"
    MODEL: str = "deepseek/deepseek-chat"
    TEMPERATURE: float = 0.3
    REQUEST_TIMEOUT: int = 60
    MAX_RETRIES: int = 3
    CONCURRENCY: int = 50
    HTTP_REFERER: str = "http://localhost:3000"
    APP_TITLE: str = "AI Health Coach Dataset Generator"
    PROFILES_FILE: str = "src/data_generation/profiles.json"
    DATASET_FILE: str = "src/data_generation/dataset.jsonl"
    PROFILES_COUNT: int = 5000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
    )
