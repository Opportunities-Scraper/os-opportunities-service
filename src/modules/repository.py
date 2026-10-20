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

    def insert(self, obj: Model) -> Model:
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj

    def delete(self, obj: Model) -> None:
        self.session.delete(obj)
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()