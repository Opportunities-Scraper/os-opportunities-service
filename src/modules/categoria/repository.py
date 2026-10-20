from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.categoria.model import Categoria


class CategoriaRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> list[Categoria]:
        return list(self.session.scalars(select(Categoria).order_by(Categoria.titulo)))

    def get_by_id(self, categoria_id: int) -> Categoria | None:
        return self.session.get(Categoria, categoria_id)

    def get_by_title(self, titulo: str) -> Categoria | None:
        return self.session.scalar(select(Categoria).where(Categoria.titulo == titulo))

    def insert(self, categoria: Categoria) -> Categoria:
        self.session.add(categoria)
        self.session.commit()
        self.session.refresh(categoria)
        return categoria

    def delete(self, categoria: Categoria) -> None:
        self.session.delete(categoria)
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
