from datetime import datetime

from sqlalchemy import TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from src.app.database import Base


class Favoritos(Base):
    __tablename__ = "favoritos"

    # A tabela usuario não é mapeada neste serviço, por isso não há FK aqui
    usuario_id: Mapped[int] = mapped_column(primary_key=True)
    oportunidade_id: Mapped[int] = mapped_column(
        ForeignKey("oportunidade.oportunidade_id"), primary_key=True
    )
    data_criacao: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.current_timestamp()
    )
