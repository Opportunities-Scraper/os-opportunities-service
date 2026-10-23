from sqlalchemy import select
from sqlalchemy.orm import joinedload

from modules.exceptions import NaoEncontradoError
from modules.favoritos.model import Favoritos
from modules.repository import BaseRepository


class FavoritosRepository(BaseRepository[Favoritos]):
    model = Favoritos

    # Equivalente ao get_or_raise da base, para a chave composta
    def get_favorito_or_raise(self, usuario_id: int, oportunidade_id: int) -> Favoritos:
        favorito = self.session.get(Favoritos, (usuario_id, oportunidade_id))
        if favorito is None:
            raise NaoEncontradoError("Oportunidade não está nos favoritos")
        return favorito

    
    def get_usuario_oportunidade(self, usuario_id: int) -> list[Favoritos]:
        # joinedload traz as oportunidades no mesmo SELECT, evitando uma consulta por favorito
        return list(
            self.session.scalars(
                select(Favoritos)
                .options(joinedload(Favoritos.oportunidade, innerjoin=True))
                .where(Favoritos.usuario_id == usuario_id)
                .order_by(Favoritos.data_criacao.desc())
            )
        )

