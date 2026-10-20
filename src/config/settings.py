from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Ex.: mysql+pymysql://usuario:senha@localhost:3306/opportunities
    database_url: str


settings = Settings()
