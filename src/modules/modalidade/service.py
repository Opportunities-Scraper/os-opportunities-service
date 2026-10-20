from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from modules.modalidade.dto import ModalidadeDTORequest, ModalidadeDTOResponse
from modules.modalidade.model import Modalidade
from modules.modalidade.repository import ModalidadeRepository


class ModalidadeService:
    def __init__(self, repository: ModalidadeRepository):
        self.repository = repository

    def listar(self) -> list[ModalidadeDTOResponse]:
        modalidades = self.repository.get_all()
        return [ModalidadeDTOResponse.model_validate(m) for m in modalidades]

    def buscar_por_id(self, modalidade_id: int) -> ModalidadeDTOResponse:
        modalidade = self.repository.get_by_id(modalidade_id)

        if modalidade is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modalidade não encontrada",
            )

        return ModalidadeDTOResponse.model_validate(modalidade)

    def buscar_por_titulo(self, modalidade_titulo: str) -> ModalidadeDTOResponse:
        modalidade = self.repository.get_by_title(modalidade_titulo)

        if modalidade is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modalidade não encontrada",
            )

        return ModalidadeDTOResponse.model_validate(modalidade)

    def criar(self, dados: ModalidadeDTORequest) -> ModalidadeDTOResponse:
        existente = self.repository.get_by_title(dados.titulo)

        if existente is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe uma modalidade com esse título",
            )

        modalidade = self.repository.insert(Modalidade(**dados.model_dump()))

        return ModalidadeDTOResponse.model_validate(modalidade)

    def atualizar(self, modalidade_id: int, dados: ModalidadeDTORequest) -> ModalidadeDTOResponse:
        modalidade = self.repository.get_by_id(modalidade_id)

        if modalidade is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modalidade não encontrada",
            )

        # Manter o próprio título é permitido; só conflita se pertencer a outra modalidade
        existente = self.repository.get_by_title(dados.titulo)

        if existente is not None and existente.modalidade_id != modalidade_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe uma modalidade com esse título",
            )

        modalidade.titulo = dados.titulo
        return ModalidadeDTOResponse.model_validate(self.repository.insert(modalidade))

    def deletar(self, modalidade_id: int) -> None:
        modalidade = self.repository.get_by_id(modalidade_id)

        if modalidade is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modalidade não encontrada",
            )

        try:
            self.repository.delete(modalidade)

        except IntegrityError:
            # A FK de oportunidade.modalidade_id impede apagar uma modalidade em uso
            self.repository.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Modalidade possui oportunidades vinculadas e não pode ser removida",
            )
