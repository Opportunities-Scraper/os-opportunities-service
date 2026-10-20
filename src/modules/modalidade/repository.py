from sqlalchemy import select
from sqlalchemy.orm import Session

from db.database import Base

from modules.modalidade.model import Modalidade
from modules.repository import BaseRepository


class ModalidadeRepository(BaseRepository):
    model = Modalidade

    def __init__(self, session: Session):
        self.session = session


    def get_by_title(self, titulo:str) -> Modalidade | None:
        return self.session.scalar(select(Modalidade).where(Modalidade.titulo==titulo))

        