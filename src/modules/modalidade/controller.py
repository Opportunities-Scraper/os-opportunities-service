from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from db.database import get_session
from db.unit_of_work import UnitOfWork
from modules.modalidade.dto import ModalidadeDTORequest, ModalidadeDTOResponse
from modules.modalidade.repository import ModalidadeRepository
from modules.modalidade.service import ModalidadeService

router = APIRouter(prefix="/modalidade", tags=["Modalidade"])


def get_modalidade_service(session: Annotated[Session, Depends(get_session)],) -> ModalidadeService:
    return ModalidadeService(ModalidadeRepository(session), UnitOfWork(session))


ServiceMap = Annotated[ModalidadeService, Depends(get_modalidade_service)]
ModalidadeId = Annotated[int, Path(gt=0)]
ModalidadeTitulo = Annotated[str, Path(min_length=1, max_length=45)]


@router.get("", response_model=list[ModalidadeDTOResponse])
def listar_modalidades(service: ServiceMap):
    return service.listar()


@router.get("/{modalidade_id}", response_model=ModalidadeDTOResponse)
def buscar_modalidade_id(modalidade_id: ModalidadeId, service: ServiceMap):
    return service.buscar_por_id(modalidade_id)


# Prefixo /titulo evita conflito com /{modalidade_id}, que capturaria qualquer texto
@router.get("/titulo/{modalidade_titulo}", response_model=ModalidadeDTOResponse)
def buscar_modalidade_titulo(modalidade_titulo: ModalidadeTitulo, service: ServiceMap):
    return service.buscar_por_titulo(modalidade_titulo)


@router.post("", response_model=ModalidadeDTOResponse, status_code=status.HTTP_201_CREATED)
def criar_modalidade(dados: ModalidadeDTORequest, service: ServiceMap):
    return service.criar(dados)


@router.put("/{modalidade_id}", response_model=ModalidadeDTOResponse)
def atualizar_modalidade(modalidade_id: ModalidadeId, dados: ModalidadeDTORequest, service: ServiceMap):
    return service.atualizar(modalidade_id, dados)


@router.delete("/{modalidade_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_modalidade(modalidade_id: ModalidadeId, service: ServiceMap):
    service.deletar(modalidade_id)
