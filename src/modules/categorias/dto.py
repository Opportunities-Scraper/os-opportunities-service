from datetime import datetime
from typing import Annotated, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)



class CategoriasBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    titulo:str = Field(min_length=1, max_length=45)



class CategoriasDTORequest(CategoriasBase):
    model_config = ConfigDict(extra="forbid")



class CategoriasDTOResponse(CategoriasBase):
    model_config = ConfigDict(from_attributes=True)

    categoria_id:int