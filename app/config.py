from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    database_url: str
    environment: str = "local"
    log_level: str = "INFO"
    self_ad_enabled: bool = True
    self_ad_chat_username: str = "baraholka_pt"
    self_ad_topic_id: int = 429
    self_ad_every_n: int = 9
    self_ad_state_path: str = "data/self_ad_counter.json"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
