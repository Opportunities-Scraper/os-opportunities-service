from sqlalchemy import select
from sqlalchemy.orm import joinedload

from modules.favoritos.model import Favoritos
from modules.repository import BaseRepository


class FavoritosRepository(BaseRepository[Favoritos]):
    model = Favoritos

    def get_favorito(self, usuario_id: int, oportunidade_id: int) -> Favoritos | None:
        # Chave primária composta: session.get recebe os valores na ordem das colunas
        return self.session.get(Favoritos, (usuario_id, oportunidade_id))

    
    def get_usuario_oportunidade(self, usuario_id: int) -> list[Favoritos]:
        # joinedload traz as oportunidades no mesmo SELECT, evitando uma consulta por favorito
        return list(
            self.session.scalars(
                select(Favoritos)
                .options(joinedload(Favoritos.oportunidade, inner_join=True))
                .where(Favoritos.usuario_id == usuario_id)
                .order_by(Favoritos.data_criacao.desc())
            )
        )

