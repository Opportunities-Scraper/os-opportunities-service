from pydantic import BaseModel, ConfigDict, Field


class CategoriaBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    titulo: str = Field(min_length=1, max_length=45)


class CategoriaDTORequest(CategoriaBase):
    model_config = ConfigDict(extra="forbid")


class CategoriaDTOResponse(CategoriaBase):
    model_config = ConfigDict(from_attributes=True)

    categoria_id: int
