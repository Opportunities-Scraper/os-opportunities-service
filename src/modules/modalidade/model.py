from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.app.database import Base


class Modalidade(Base):
    __tablename__ = "modalidade"

    modalidade_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column(String(45))
