from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Bancos que o projeto sabe usar, com o prefixo de URL esperado pelo SQLAlchemy
BANCOS_SUPORTADOS = ("sqlite://", "mysql+pymysql://")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Ex.: sqlite:///mock.sqlite  ou  mysql+pymysql://usuario:senha@127.0.0.1:3307/banco
    database_url: str

    # Marca o banco como local e descartável (ex.: MySQL no Docker): a API cria as tabelas
    # que faltam e o seed pode populá-lo. O SQLite é sempre tratado como local.
    # Nunca ative apontando para o banco compartilhado: ligue com BANCO_LOCAL=true no .env.
    banco_local: bool = False


    @field_validator("database_url")
    @classmethod
    def validar_database_url(cls, url: str) -> str:
        if url.startswith(BANCOS_SUPORTADOS):
            return url

        # "mysql://" faria o SQLAlchemy procurar o driver MySQLdb, que não está instalado
        if url.startswith("mysql://"):
            raise ValueError("use o prefixo 'mysql+pymysql://' em vez de 'mysql://'")

        raise ValueError(f"banco não suportado; a URL deve começar com {' ou '.join(BANCOS_SUPORTADOS)}")


settings = Settings()
