from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.database import Base


class Oportunidade(Base):
    __tablename__ = "oportunidade"

    oportunidade_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column(String(255))
    descricao: Mapped[str] = mapped_column(Text)
    url_original: Mapped[str] = mapped_column(Text)
    pais: Mapped[str] = mapped_column(String(45))
    cidade: Mapped[str] = mapped_column(String(45))
    data_publicacao: Mapped[datetime] = mapped_column(DateTime)
    data_limite: Mapped[datetime] = mapped_column(DateTime)
    modalidade_id: Mapped[int] = mapped_column(ForeignKey("modalidade.modalidade_id"))
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categoria.categoria_id"))
