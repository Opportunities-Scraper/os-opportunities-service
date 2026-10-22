from db.transaction import Transaction
from modules.exceptions import ConflitoError, IntegridadeError, ReferenciaInvalidaError
from modules.oportunidade.dto import OportunidadeDTORequest, OportunidadeDTOResponse
from modules.oportunidade.model import Oportunidade


class OportunidadeService:
    def __init__(self, transaction: Transaction):
        self.transaction = transaction

    def listar(self) -> list[OportunidadeDTOResponse]:
        oportunidades = self.transaction.oportunidades.get_all()
        return [OportunidadeDTOResponse.model_validate(o) for o in oportunidades]

    def buscar_por_id(self, oportunidade_id: int) -> OportunidadeDTOResponse:
        oportunidade = self.transaction.oportunidades.get_or_raise(oportunidade_id)
        return OportunidadeDTOResponse.model_validate(oportunidade)

    def buscar_por_modalidade_id(self, modalidade_id: int) -> list[OportunidadeDTOResponse]:
        oportunidades = self.transaction.oportunidades.get_by_modalidade_id(modalidade_id)
        return [OportunidadeDTOResponse.model_validate(o) for o in oportunidades]

    def buscar_por_categoria_id(self, categoria_id: int) -> list[OportunidadeDTOResponse]:
        oportunidades = self.transaction.oportunidades.get_by_categoria_id(categoria_id)
        return [OportunidadeDTOResponse.model_validate(o) for o in oportunidades]

    def criar(self, dados: OportunidadeDTORequest) -> OportunidadeDTOResponse:
        existente = self.transaction.oportunidades.get_by_url(dados.url_original)

        if existente is not None:
            raise ConflitoError("Já existe uma oportunidade com essa URL")

        try:
            with self.transaction:
                oportunidade = self.transaction.oportunidades.insert(
                    Oportunidade(**dados.model_dump())
                )

        except IntegridadeError as erro:
            # As FKs rejeitam modalidade_id ou categoria_id que não existem
            raise ReferenciaInvalidaError(
                "modalidade_id ou categoria_id não existe"
            ) from erro

        return OportunidadeDTOResponse.model_validate(oportunidade)

    def atualizar(self, oportunidade_id: int, dados: OportunidadeDTORequest) -> OportunidadeDTOResponse:
        oportunidade = self.transaction.oportunidades.get_or_raise(oportunidade_id)

        existente = self.transaction.oportunidades.get_by_url(dados.url_original)

        if existente is not None and existente.oportunidade_id != oportunidade_id:
            raise ConflitoError("Já existe uma oportunidade com essa URL")

        try:
            # O objeto já está na sessão: basta alterá-lo, e o commit da transaction grava
            with self.transaction:
                oportunidade.titulo = dados.titulo
                oportunidade.descricao = dados.descricao
                oportunidade.url_original = dados.url_original
                oportunidade.pais = dados.pais
                oportunidade.cidade = dados.cidade
                oportunidade.data_publicacao = dados.data_publicacao
                oportunidade.data_limite = dados.data_limite
                oportunidade.modalidade_id = dados.modalidade_id
                oportunidade.categoria_id = dados.categoria_id

        except IntegridadeError as erro:
            # As FKs rejeitam modalidade_id ou categoria_id que não existem
            raise ReferenciaInvalidaError(
                "modalidade_id ou categoria_id não existe"
            ) from erro

        return OportunidadeDTOResponse.model_validate(oportunidade)

    def deletar(self, oportunidade_id: int) -> None:
        oportunidade = self.transaction.oportunidades.get_or_raise(oportunidade_id)

        try:
            with self.transaction:
                self.transaction.oportunidades.delete(oportunidade)

        except IntegridadeError as erro:
            # A FK de favoritos.oportunidade_id impede apagar uma oportunidade favoritada
            raise ConflitoError(
                "Oportunidade está nos favoritos de algum usuário e não pode ser removida"
            ) from erro
