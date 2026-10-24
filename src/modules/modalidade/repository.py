from sqlalchemy import select

from modules.modalidade.model import Modalidade
from modules.base_repository import BaseRepository


class ModalidadeRepository(BaseRepository[Modalidade]):
    model = Modalidade
    nao_encontrado = "Modalidade não encontrada"

    def get_by_title(self, titulo: str) -> Modalidade | None:
        return self.session.scalar(select(Modalidade).where(Modalidade.titulo == titulo))
