from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config.settings import settings

# pool_pre_ping evita erros com conexões que o MySQL já fechou por inatividade
engine = create_engine(settings.database_url, pool_pre_ping=True)


if engine.dialect.name == "sqlite":

    @event.listens_for(engine, "connect")
    def  ativar_foreign_keys(db_api_connection, connection_record):
        cursor = db_api_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_session() -> Generator[Session]:
    with SessionLocal() as session:
        yield session
