from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "AGENT_", "env_file": ".env", "extra": "ignore"}

    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = "sk-placeholder"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.0

    java_base_url: str = "http://app:8080"

    session_ttl_minutes: int = 30
    max_relax_rounds: int = 3


settings = Settings()
