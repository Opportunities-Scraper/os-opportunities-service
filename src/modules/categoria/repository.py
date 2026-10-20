from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.categoria.model import Categoria
from modules.repository import BaseRepository


class CategoriaRepository(BaseRepository):
    model = Categoria

    def __init__(self, session: Session):
        self.session = session

    def get_by_title(self, titulo: str) -> Categoria | None:
        return self.session.scalar(select(Categoria).where(Categoria.titulo == titulo))
