from datetime import UTC, datetime
from typing import Annotated, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    PlainSerializer,
    model_validator,
)

# Valida o formato da URL, mas mantém o valor como str para persistir direto na coluna Text
UrlStr = Annotated[HttpUrl, AfterValidator(str), PlainSerializer(str, return_type=str)]


def _para_utc_sem_fuso(valor: datetime) -> datetime:
    if valor.tzinfo is not None:
        return valor.astimezone(UTC).replace(tzinfo=None)
    return valor


# A coluna DATETIME do MySQL não guarda fuso: datas com fuso são convertidas para UTC
# e datas sem fuso são tratadas como já estando em UTC. Isso também permite comparar
# as duas datas no validador sem TypeError quando só uma delas vem com fuso.
DataUTC = Annotated[datetime, AfterValidator(_para_utc_sem_fuso)]


class OportunidadeBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    # Os limites de tamanho espelham as colunas do model Oportunidade
    titulo: str = Field(min_length=1, max_length=255)
    descricao: str = Field(min_length=1)
    url_original: UrlStr
    pais: str = Field(min_length=1, max_length=45)
    cidade: str = Field(min_length=1, max_length=45)
    data_publicacao: DataUTC
    data_limite: DataUTC
    modalidade_id: int = Field(gt=0)
    categoria_id: int = Field(gt=0)


class OportunidadeDTORequest(OportunidadeBase):
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validar_datas(self) -> Self:
        if self.data_limite < self.data_publicacao:
            raise ValueError("data_limite não pode ser anterior a data_publicacao")
        return self


class OportunidadeDTOResponse(OportunidadeBase):
    model_config = ConfigDict(from_attributes=True)

    oportunidade_id: int
