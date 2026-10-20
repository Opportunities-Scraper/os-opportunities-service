from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from modules.oportunidade.dto import OportunidadeDTORequest, OportunidadeDTOResponse
from modules.oportunidade.model import Oportunidade
from modules.oportunidade.repository import OportunidadeRepository


class OportunidadeService:
    def __init__(self, repository: OportunidadeRepository):
        self.repository = repository

    def listar(self) -> list[OportunidadeDTOResponse]:
        oportunidades = self.repository.get_all()
        return [OportunidadeDTOResponse.model_validate(o) for o in oportunidades]

    def buscar_por_id(self, oportunidade_id: int) -> OportunidadeDTOResponse:
        oportunidade = self.repository.get_by_id(oportunidade_id)

        if oportunidade is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Oportunidade não encontrada",
            )

        return OportunidadeDTOResponse.model_validate(oportunidade)


    def buscar_por_modalidade_id(self, modalidade_id: int) -> list[OportunidadeDTOResponse]:
        oportunidades = self.repository.get_by_modalidade_id(modalidade_id)
        return [OportunidadeDTOResponse.model_validate(o) for o in oportunidades]


    def buscar_por_categoria_id(self, categoria_id: int) -> list[OportunidadeDTOResponse]:
        oportunidades = self.repository.get_by_categoria_id(categoria_id)
        return [OportunidadeDTOResponse.model_validate(o) for o in oportunidades]



    def criar(self, dados: OportunidadeDTORequest) -> OportunidadeDTOResponse:
        existente = self.repository.get_by_url(dados.url_original)

        if existente is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe uma oportunidade com essa URL",
            )

        try:
            oportunidade = self.repository.insert(Oportunidade(**dados.model_dump()))

        except IntegrityError:
            # As FKs rejeitam modalidade_id ou categoria_id que não existem
            self.repository.rollback()

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="modalidade_id ou categoria_id não existe",
            )

        return OportunidadeDTOResponse.model_validate(oportunidade)

    def atualizar(self, oportunidade_id: int, dados: OportunidadeDTORequest) -> OportunidadeDTOResponse:
        oportunidade = self.repository.get_by_id(oportunidade_id)

        if oportunidade is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Oportunidade não encontrada",
            )

        existente = self.repository.get_by_url(dados.url_original)

        if existente is not None and existente.oportunidade_id != oportunidade_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe uma oportunidade com essa URL",
            )

        # Copia todos os campos do DTO, sem risco de esquecer ou trocar algum
        for campo, valor in dados.model_dump().items():
            setattr(oportunidade, campo, valor)

        try:
            # Salva o próprio objeto alterado; criar um Oportunidade novo duplicaria o registro
            oportunidade = self.repository.insert(oportunidade)

        except IntegrityError:
            # As FKs rejeitam modalidade_id ou categoria_id que não existem
            self.repository.rollback()

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="modalidade_id ou categoria_id não existe",
            )

        return OportunidadeDTOResponse.model_validate(oportunidade)

    def deletar(self, oportunidade_id: int) -> None:
        oportunidade = self.repository.get_by_id(oportunidade_id)

        if oportunidade is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Oportunidade não encontrada",
            )

        try:
            self.repository.delete(oportunidade)

        except IntegrityError:
            # A FK de favoritos.oportunidade_id impede apagar uma oportunidade favoritada
            self.repository.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Oportunidade está nos favoritos de algum usuário e não pode ser removida",
            )
