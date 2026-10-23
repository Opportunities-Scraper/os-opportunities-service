from sqlalchemy import inspect

from config.settings import settings
from db.database import Base, engine


def handle_db_schema() -> None:
    # Em bancos locais, cria as tabelas que faltam (create_all não altera as que já existem)
    if engine.dialect.name == "sqlite" or settings.banco_local:
        Base.metadata.create_all(engine)
        return

    # No banco compartilhado o schema é mantido fora deste serviço: só confere se está
    # tudo lá, para falhar na inicialização em vez de na primeira requisição
    existentes = set(inspect(engine).get_table_names())
    faltando = sorted(set(Base.metadata.tables) - existentes)

    if faltando:
        raise RuntimeError(
            f"Tabelas ausentes no banco '{engine.url.database}': {', '.join(faltando)}. "
            "Crie o schema no banco ou, se ele for local e descartável (ex.: MySQL no "
            "Docker), defina BANCO_LOCAL=true no .env para a API criá-las."
        )
