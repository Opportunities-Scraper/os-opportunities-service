from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from db.database import get_session
from modules.oportunidade.dto import OportunidadeDTORequest, OportunidadeDTOResponse
from modules.oportunidade.repository import OportunidadeRepository
from modules.oportunidade.service import OportunidadeService

router = APIRouter(prefix="/oportunidade", tags=["Oportunidade"])


def get_oportunidade_service(session: Annotated[Session, Depends(get_session)],) -> OportunidadeService:
    return OportunidadeService(OportunidadeRepository(session))


ServiceMap = Annotated[OportunidadeService, Depends(get_oportunidade_service)]
OportunidadeId = Annotated[int, Path(gt=0)]
ModalidadeId = Annotated[int, Path(gt=0)]
CategoriaId = Annotated[int, Path(gt=0)]

# GET ======================================================================
@router.get("", response_model=list[OportunidadeDTOResponse])
def listar_oportunidades(service: ServiceMap):
    return service.listar()


@router.get("/{oportunidade_id}", response_model=OportunidadeDTOResponse)
def buscar_oportunidade_id(oportunidade_id: OportunidadeId, service: ServiceMap):
    return service.buscar_por_id(oportunidade_id)


@router.get("/modalidade/{modalidade_id}", response_model=list[OportunidadeDTOResponse])
def buscar_oportunidades_modalidade(modalidade_id: ModalidadeId, service: ServiceMap):
    return service.buscar_por_modalidade_id(modalidade_id)


@router.get("/categoria/{categoria_id}", response_model=list[OportunidadeDTOResponse])
def buscar_oportunidades_categoria(categoria_id: CategoriaId, service: ServiceMap):
    return service.buscar_por_categoria_id(categoria_id)
# ===============================================================================


# POST =====================================================================================
@router.post("", response_model=OportunidadeDTOResponse, status_code=status.HTTP_201_CREATED)
def criar_oportunidade(dados: OportunidadeDTORequest, service: ServiceMap):
    return service.criar(dados)
# ==========================================================================================


# PUT =========================================================================================
@router.put("/{oportunidade_id}", response_model=OportunidadeDTOResponse)
def atualizar_oportunidade(oportunidade_id: OportunidadeId, dados: OportunidadeDTORequest, service: ServiceMap):
    return service.atualizar(oportunidade_id, dados)
# ===========================================================================================



# DELETE ===================================================================================
@router.delete("/{oportunidade_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_oportunidade(oportunidade_id: OportunidadeId, service: ServiceMap):
    service.deletar(oportunidade_id)
# ==========================================================================================