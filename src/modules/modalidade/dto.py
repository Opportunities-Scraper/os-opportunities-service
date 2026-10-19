from pydantic import BaseModel, ConfigDict, Field


class ModalidadeBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    titulo: str = Field(min_length=1, max_length=45)


class ModalidadeDTORequest(ModalidadeBase):
    model_config = ConfigDict(extra="forbid")


class ModalidadeDTOResponse(ModalidadeBase):
    model_config = ConfigDict(from_attributes=True)

    modalidade_id: int
