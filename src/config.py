from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    ROOT_PATH: Path = Path(__file__).parent.parent.absolute()

    model_config = SettingsConfigDict(
        env_file=f"{ROOT_PATH}/.env", extra="ignore", env_file_encoding="utf-8"
    )

    LLM_PROVIDER: str = "openai"
    GROQ_LLM_MODEL: str
    GROQ_API_KEY: str

    OPENAI_API_KEY: str
    OPENAI_MODEL_NAME: str

    OLLAMA_MODEL_NAME: str

    HOME_TEMPLATE_PATH: str = f"{ROOT_PATH}/data/home_templates/h1.json"


config = Config()
