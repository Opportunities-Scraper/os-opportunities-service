from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Ex.: sqlite:///mock.sqlite  ou  mysql+pymysql://usuario:senha@127.0.0.1:porta/banco
    database_url: str

    # Fleg para identificar se o banco de dados é local ou não
    banco_local: bool = False

    @field_validator("database_url")
    @classmethod
    def validar_database_url(cls, db_url: str) -> str:
        db_url = db_url.strip()

        try:
            url = make_url(db_url)

        except ArgumentError as exc:
            raise ValueError(
                "database_url não é uma URL válida"
            ) from exc

        if url.drivername == "mysql":
            raise ValueError("use o prefixo 'mysql+pymysql://' em vez de 'mysql://'")

        if url.drivername not in {"sqlite", "mysql+pymysql"}:
            raise ValueError("banco não suportado; use SQLite ou MySQL com PyMySQL")

        return db_url



# Responsável por toda a configuração referente a conexão com banco de dados
settings = Settings()