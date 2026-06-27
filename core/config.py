from urllib.parse import quote_plus
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    '''configurations class'''

    # PostgreSQL
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str

    # AmoCRM
    amo_client_id: str
    amo_subdomain: str
    amo_redirect_uri: str
    amo_access_token: str
    amo_refresh_token: str
    amo_client_secret: str
    amo_authorization_code: str

    # Telegram
    tg_chat_id: int
    tg_bot_token: str

    # Pipeline
    amo_stage_id: int
    amo_pipeline_id: int

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    @property
    def database_url(self) -> str: # getter
        # We're escaping the password so that special characters (@, #, &, +) don't break the URL.
        safe_password = quote_plus(self.db_password)
        return (
            f"postgresql+asyncpg://{self.db_user}:{safe_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

settings = Settings()  # type: ignore