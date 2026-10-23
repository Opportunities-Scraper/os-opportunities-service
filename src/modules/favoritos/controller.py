from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from auth.dependencies import UsuarioId
from db.transaction import Transaction, get_transaction
from modules.favoritos.dto import FavoritosDTORequest, FavoritosDTOResponse
from modules.favoritos.service import FavoritosService

router = APIRouter(prefix="/favoritos", tags=["Favoritos"])


def get_favoritos_service(transaction: Annotated[Transaction, Depends(get_transaction)]) -> FavoritosService:
    return FavoritosService(transaction)


ServiceMap = Annotated[FavoritosService, Depends(get_favoritos_service)]
OportunidadeId = Annotated[int, Path(gt=0)]


@router.get("", response_model=list[FavoritosDTOResponse])
def listar_favoritos(usuario_id: UsuarioId, service: ServiceMap):
    return service.listar(usuario_id)


# Útil para o frontend saber se a oportunidade já está favoritada (ex.: ícone de coração)
@router.get("/{oportunidade_id}", response_model=FavoritosDTOResponse)
def buscar_favorito(oportunidade_id: OportunidadeId, usuario_id: UsuarioId, service: ServiceMap):
    return service.buscar_relacao(usuario_id, oportunidade_id)


@router.post("", response_model=FavoritosDTOResponse, status_code=status.HTTP_201_CREATED)
def adicionar_favorito(dados: FavoritosDTORequest, usuario_id: UsuarioId, service: ServiceMap):
    return service.adicionar(usuario_id, dados)


@router.delete("/{oportunidade_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_favorito(oportunidade_id: OportunidadeId, usuario_id: UsuarioId, service: ServiceMap):
    service.remover(usuario_id, oportunidade_id)
