from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from modules.oportunidade.dto import OportunidadeDTOResponse


class FavoritosDTORequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # O usuario_id não vem no corpo: é sempre o do usuário autenticado
    oportunidade_id: int = Field(gt=0)


class FavoritosDTOResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    usuario_id: int
    oportunidade_id: int
    # Gerada pelo banco (server_default), por isso só aparece na resposta
    data_criacao: datetime
    oportunidade: OportunidadeDTOResponse
