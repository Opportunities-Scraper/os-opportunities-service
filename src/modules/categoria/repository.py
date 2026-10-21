from sqlalchemy import select

from modules.categoria.model import Categoria
from modules.repository import BaseRepository


class CategoriaRepository(BaseRepository[Categoria]):
    model = Categoria
    nao_encontrado = "Categoria não encontrada"

    def get_by_title(self, titulo: str) -> Categoria | None:
        return self.session.scalar(select(Categoria).where(Categoria.titulo == titulo))
