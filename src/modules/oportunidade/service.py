from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from db.unit_of_work import UnitOfWork
from modules.oportunidade.dto import OportunidadeDTORequest, OportunidadeDTOResponse
from modules.oportunidade.model import Oportunidade
from modules.oportunidade.repository import OportunidadeRepository


class OportunidadeService:
    def __init__(self, repository: OportunidadeRepository, uow: UnitOfWork):
        self.repository = repository
        self.uow = uow

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
            with self.uow:
                oportunidade = self.repository.insert(Oportunidade(**dados.model_dump()))

        except IntegrityError:
            # As FKs rejeitam modalidade_id ou categoria_id que não existem
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

        try:
            # O objeto já está na sessão: basta alterá-lo, e o commit da uow grava
            with self.uow:
                oportunidade.titulo = dados.titulo
                oportunidade.descricao = dados.descricao
                oportunidade.url_original = dados.url_original
                oportunidade.pais = dados.pais
                oportunidade.cidade = dados.cidade
                oportunidade.data_publicacao = dados.data_publicacao
                oportunidade.data_limite = dados.data_limite
                oportunidade.modalidade_id = dados.modalidade_id
                oportunidade.categoria_id = dados.categoria_id

        except IntegrityError:
            # As FKs rejeitam modalidade_id ou categoria_id que não existem
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
            with self.uow:
                self.repository.delete(oportunidade)

        except IntegrityError:
            # A FK de favoritos.oportunidade_id impede apagar uma oportunidade favoritada
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Oportunidade está nos favoritos de algum usuário e não pode ser removida",
            )
