from datetime import datetime
from typing import Annotated, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


class FavoritosBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    data_criacao:datetime


class FavoritosDTORequest(FavoritosBase):
    model_config = ConfigDict(extra="forbid")


class FavoritosDTOResponse(FavoritosBase):
    model_config = ConfigDict(from_attributes=True)

    usuario_id:int 
    oportunidade_id:int 