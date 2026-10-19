from datetime import datetime
from typing import Annotated, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


class ModalidadeBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    titulo:str = Field(min_length=1, max_length=45)


class ModalidadeDTORequest(ModalidadeBase):
    model_config = ConfigDict(extra="forbid")


class ModalidadeDTORequest: 
    model_config = ConfigDict(from_attributes=True)

    modalidade_id: int 