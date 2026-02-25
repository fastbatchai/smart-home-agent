from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    ROOT_PATH: Path = Path(__file__).parent.parent.absolute()

    model_config = SettingsConfigDict(
        env_file=f"{ROOT_PATH}/.env", extra="ignore", env_file_encoding="utf-8"
    )
    # --------------------------------#
    # LLM Provider Configuration    #
    # --------------------------------#
    LLM_PROVIDER: str = "openai"
    GROQ_LLM_MODEL: str
    GROQ_API_KEY: str

    OPENAI_API_KEY: str
    OPENAI_MODEL_NAME: str

    OLLAMA_MODEL_NAME: str

    # --------------------------------#
    # Memory Configuration          #
    # --------------------------------#
    MEM0_API_KEY: str
    MEM0_ORG_ID: str
    MEM0_PROJECT_ID: str
    SKIP_MEMORY: bool = False

    SESSION_WINDOW_SECONDS: int = 600  # 10 minutes
    REDIS_DB_URI: str
    REDIS_ENDPOINT: str
    REDIS_PORT: int
    REDIS_USERNAME: str
    REDIS_PASSWORD: str

    # --------------------------------#
    # Home Configuration          #
    # --------------------------------#
    HOME_TEMPLATE_PATH: str = f"{ROOT_PATH}/data/home_templates/h1.json"


config = Config()
