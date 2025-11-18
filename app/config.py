from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: Optional[str] = None
    database_url: Optional[str] = None
    whatsapp_verify_token: Optional[str] = None

    # Diz para o Pydantic pegar as variáveis do arquivo .env
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
