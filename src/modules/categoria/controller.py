from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from db.database import get_session
from modules.categoria.dto import CategoriaDTORequest, CategoriaDTOResponse
from modules.categoria.repository import CategoriaRepository
from modules.categoria.service import CategoriaService

router = APIRouter(prefix="/categorias", tags=["Categorias"])



def get_categoria_service(session: Annotated[Session, Depends(get_session)]) -> CategoriaService:
    return CategoriaService(CategoriaRepository(session))


ServiceDep = Annotated[CategoriaService, Depends(get_categoria_service)]
CategoriaId = Annotated[int, Path(gt=0)]


@router.get("", response_model=list[CategoriaDTOResponse])
def listar_categorias(service: ServiceDep):
    return service.listar()


@router.get("/{categoria_id}", response_model=CategoriaDTOResponse)
def buscar_categoria(categoria_id: CategoriaId, service: ServiceDep):
    return service.buscar_por_id(categoria_id)


@router.post("", response_model=CategoriaDTOResponse, status_code=status.HTTP_201_CREATED)
def criar_categoria(dados: CategoriaDTORequest, service: ServiceDep):
    return service.criar(dados)


@router.put("/{categoria_id}", response_model=CategoriaDTOResponse)
def atualizar_categoria(categoria_id: CategoriaId, dados: CategoriaDTORequest, service: ServiceDep):
    return service.atualizar(categoria_id, dados)


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_categoria(categoria_id: CategoriaId, service: ServiceDep):
    service.deletar(categoria_id)
