from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from db.unit_of_work import UnitOfWork
from modules.favoritos.dto import FavoritosDTORequest, FavoritosDTOResponse
from modules.favoritos.model import Favoritos
from modules.favoritos.repository import FavoritosRepository
from modules.oportunidade.repository import OportunidadeRepository


class FavoritosService:
    def __init__(self, repository: FavoritosRepository, oportunidade_repository: OportunidadeRepository, uow: UnitOfWork):
        self.repository = repository
        self.oportunidade_repository = oportunidade_repository
        self.uow = uow


    def listar(self, usuario_id: int) -> list[FavoritosDTOResponse]:
        favoritos = self.repository.get_usuario_oportunidade(usuario_id)
        return [FavoritosDTOResponse.model_validate(f) for f in favoritos]


    def buscar_relacao(self, usuario_id: int, oportunidade_id: int) -> FavoritosDTOResponse:
        favorito = self.repository.get_favorito(usuario_id, oportunidade_id)

        if favorito is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Oportunidade não está nos favoritos",
            )

        return FavoritosDTOResponse.model_validate(favorito)

    def adicionar(self, usuario_id: int, dados: FavoritosDTORequest) -> FavoritosDTOResponse:
        oportunidade = self.oportunidade_repository.get_by_id(dados.oportunidade_id)

        if oportunidade is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Oportunidade não encontrada",
            )

        existente = self.repository.get_favorito(usuario_id, dados.oportunidade_id)

        if existente is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Oportunidade já está nos favoritos",
            )

        try:
            with self.uow:
                favorito = self.repository.insert(Favoritos(usuario_id=usuario_id, oportunidade_id=dados.oportunidade_id))

        except IntegrityError:
            # Duas requisições simultâneas para o mesmo favorito, ou usuario_id que
            # não existe na tabela usuario (a FK existe no banco, mas não é mapeada aqui)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Não foi possível adicionar o favorito",
            )

        return FavoritosDTOResponse.model_validate(favorito)

    def remover(self, usuario_id: int, oportunidade_id: int) -> None:
        favorito = self.repository.get_favorito(usuario_id, oportunidade_id)

        if favorito is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Oportunidade não está nos favoritos",
            )

        with self.uow:
            self.repository.delete(favorito)
