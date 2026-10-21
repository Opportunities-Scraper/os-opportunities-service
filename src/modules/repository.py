from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.database import Base


class BaseRepository[Model: Base]:
    model: type[Model]

    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> list[Model]:
        return list(self.session.scalars(select(self.model)))

    def get_by_id(self, id: int) -> Model | None:
        return self.session.get(self.model, id)

    # Os métodos de escrita não fazem commit: o flush só envia o SQL dentro da
    # transação aberta. Quem grava ou desfaz é o service, pela UnitOfWork.
    # O flush também faz erros do banco (ex.: FK inválida) aparecerem aqui, dentro
    # do bloco do service, e não só no commit.

    def insert(self, obj: Model) -> Model:
        self.session.add(obj)
        self.session.flush()
        # Carrega valores gerados pelo banco, como o id e o data_criacao de favoritos
        self.session.refresh(obj)
        return obj

    def update(self, obj: Model, valores: dict[str, Any]) -> Model:
        for campo, valor in valores.items():
            # Sem essa checagem, setattr com nome errado não falha nem salva nada
            if not hasattr(self.model, campo):
                raise AttributeError(f"{self.model.__name__} não tem o campo '{campo}'")
            setattr(obj, campo, valor)

        self.session.flush()
        return obj

    def delete(self, obj: Model) -> None:
        self.session.delete(obj)
        self.session.flush()
