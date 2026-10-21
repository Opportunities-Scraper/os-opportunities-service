from sqlalchemy import select

from modules.oportunidade.model import Oportunidade
from modules.repository import BaseRepository


class OportunidadeRepository(BaseRepository[Oportunidade]):
    model = Oportunidade
    nao_encontrado = "Oportunidade não encontrada"

    def get_by_url(self, url_original: str) -> Oportunidade | None:
        return self.session.scalar(select(Oportunidade).where(Oportunidade.url_original == url_original))

    def get_by_modalidade_id(self, modalidade_id: int) -> list[Oportunidade]:
        return list(self.session.scalars(select(Oportunidade).where(Oportunidade.modalidade_id == modalidade_id)))

    def get_by_categoria_id(self, categoria_id: int) -> list[Oportunidade]:
        return list(self.session.scalars(select(Oportunidade).where(Oportunidade.categoria_id == categoria_id)))
