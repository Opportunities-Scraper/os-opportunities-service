from sqlalchemy import select

from modules.modalidade.model import Modalidade
from modules.repository import BaseRepository


class ModalidadeRepository(BaseRepository[Modalidade]):
    model = Modalidade

    def get_by_title(self, titulo: str) -> Modalidade | None:
        return self.session.scalar(select(Modalidade).where(Modalidade.titulo == titulo))
