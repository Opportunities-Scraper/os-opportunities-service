from sqlalchemy import delete, select
from sqlalchemy.orm import joinedload

from modules.exceptions import NaoEncontradoError
from modules.favoritos.model import Favoritos
from modules.repository import BaseRepository


class FavoritosRepository(BaseRepository[Favoritos]):
    model = Favoritos

    def get_favorito(self, usuario_id: int, oportunidade_id: int) -> Favoritos | None:
        # Chave primária composta: session.get recebe os valores na ordem das colunas
        return self.session.get(Favoritos, (usuario_id, oportunidade_id))

    # Equivalente ao get_or_raise da base, para a chave composta
    def get_favorito_or_raise(self, usuario_id: int, oportunidade_id: int) -> Favoritos:
        favorito = self.get_favorito(usuario_id, oportunidade_id)
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

    def delete_by_oportunidade(self, oportunidade_id: int) -> None:
        # Um único DELETE para os favoritos de todos os usuários, em vez de um por favorito
        self.session.execute(
            delete(Favoritos).where(Favoritos.oportunidade_id == oportunidade_id)
        )
        self.session.flush()

