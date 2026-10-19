from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FavoritosBase(BaseModel):
    usuario_id: int = Field(gt=0)
    oportunidade_id: int = Field(gt=0)


class FavoritosDTORequest(FavoritosBase):
    model_config = ConfigDict(extra="forbid")


class FavoritosDTOResponse(FavoritosBase):
    model_config = ConfigDict(from_attributes=True)

    # Gerada pelo banco (server_default), por isso só aparece na resposta
    data_criacao: datetime
