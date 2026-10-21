from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from auth.dependencies import UsuarioId
from db.database import get_session
from modules.favoritos.dto import FavoritosDTORequest, FavoritosDTOResponse
from modules.favoritos.repository import FavoritosRepository
from modules.favoritos.service import FavoritosService
from modules.oportunidade.repository import OportunidadeRepository

router = APIRouter(prefix="/favoritos", tags=["Favoritos"])


def get_favoritos_service(session: Annotated[Session, Depends(get_session)],) -> FavoritosService:
    return FavoritosService(FavoritosRepository(session), OportunidadeRepository(session))


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
