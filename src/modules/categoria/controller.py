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


ServiceMap = Annotated[CategoriaService, Depends(get_categoria_service)]
CategoriaId = Annotated[int, Path(gt=0)]
CategoriaNome = Annotated[str, Path(min_length=1, max_length=45)]


@router.get("", response_model=list[CategoriaDTOResponse])
def listar_categorias(service: ServiceMap):
    return service.listar()


@router.get("/{categoria_id}", response_model=CategoriaDTOResponse)
def buscar_categoria_id(categoria_id: CategoriaId, service: ServiceMap):
    return service.buscar_por_id(categoria_id)


# Prefixo /titulo evita conflito com /{categoria_id}, que capturaria qualquer texto
@router.get("/titulo/{categoria_nome}", response_model=CategoriaDTOResponse)
def buscar_categoria_nome(categoria_nome: CategoriaNome, service: ServiceMap) :
    return service.buscar_por_titulo(categoria_nome)


@router.post("", response_model=CategoriaDTOResponse, status_code=status.HTTP_201_CREATED)
def criar_categoria(dados: CategoriaDTORequest, service: ServiceMap):
    return service.criar(dados)


@router.put("/{categoria_id}", response_model=CategoriaDTOResponse)
def atualizar_categoria(categoria_id: CategoriaId, dados: CategoriaDTORequest, service: ServiceMap):
    return service.atualizar(categoria_id, dados)


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_categoria(categoria_id: CategoriaId, service: ServiceMap):
    service.deletar(categoria_id)
