from db.transaction import Transaction
from modules.exceptions import ConflitoError, IntegridadeError
from modules.favoritos.dto import FavoritosDTORequest, FavoritosDTOResponse
from modules.favoritos.model import Favoritos


class FavoritosService:
    def __init__(self, transaction: Transaction):
        self.transaction = transaction

    def listar(self, usuario_id: int) -> list[FavoritosDTOResponse]:
        favoritos = self.transaction.favoritos.get_usuario_oportunidade(usuario_id)
        return [FavoritosDTOResponse.model_validate(f) for f in favoritos]

    def buscar_relacao(self, usuario_id: int, oportunidade_id: int) -> FavoritosDTOResponse:
        favorito = self.transaction.favoritos.get_favorito_or_raise(usuario_id, oportunidade_id)
        return FavoritosDTOResponse.model_validate(favorito)

    def adicionar(self, usuario_id: int, dados: FavoritosDTORequest) -> FavoritosDTOResponse:
        self.transaction.oportunidades.get_or_raise(dados.oportunidade_id)

        existente = self.transaction.favoritos.get_favorito(usuario_id, dados.oportunidade_id)

        if existente is not None:
            raise ConflitoError("Oportunidade já está nos favoritos")

        try:
            with self.transaction:
                favorito = self.transaction.favoritos.insert(
                    Favoritos(usuario_id=usuario_id, oportunidade_id=dados.oportunidade_id)
                )

        except IntegridadeError as erro:
            # Duas requisições simultâneas para o mesmo favorito, ou usuario_id que
            # não existe na tabela usuario (a FK existe no banco, mas não é mapeada aqui)
            raise ConflitoError("Não foi possível adicionar o favorito") from erro

        return FavoritosDTOResponse.model_validate(favorito)

    def remover(self, usuario_id: int, oportunidade_id: int) -> None:
        favorito = self.transaction.favoritos.get_favorito_or_raise(usuario_id, oportunidade_id)

        with self.transaction:
            self.transaction.favoritos.delete(favorito)
