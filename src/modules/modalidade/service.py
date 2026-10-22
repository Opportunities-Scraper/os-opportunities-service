from db.transaction import Transaction
from modules.exceptions import ConflitoError, IntegridadeError, NaoEncontradoError
from modules.modalidade.dto import ModalidadeDTORequest, ModalidadeDTOResponse
from modules.modalidade.model import Modalidade


class ModalidadeService:
    def __init__(self, transaction: Transaction):
        self.transaction = transaction

    def listar(self) -> list[ModalidadeDTOResponse]:
        modalidades = self.transaction.modalidades.get_all()
        return [ModalidadeDTOResponse.model_validate(m) for m in modalidades]

    def buscar_por_id(self, modalidade_id: int) -> ModalidadeDTOResponse:
        modalidade = self.transaction.modalidades.get_or_raise(modalidade_id)
        return ModalidadeDTOResponse.model_validate(modalidade)

    def buscar_por_titulo(self, modalidade_titulo: str) -> ModalidadeDTOResponse:
        modalidade = self.transaction.modalidades.get_by_title(modalidade_titulo)

        if modalidade is None:
            raise NaoEncontradoError("Modalidade não encontrada")

        return ModalidadeDTOResponse.model_validate(modalidade)

    def adicionar(self, dados: ModalidadeDTORequest) -> ModalidadeDTOResponse:
        existente = self.transaction.modalidades.get_by_title(dados.titulo)

        if existente is not None:
            raise ConflitoError("Já existe uma modalidade com esse título")

        with self.transaction:
            modalidade = self.transaction.modalidades.insert(Modalidade(**dados.model_dump()))

        return ModalidadeDTOResponse.model_validate(modalidade)

    def atualizar(self, modalidade_id: int, dados: ModalidadeDTORequest) -> ModalidadeDTOResponse:
        modalidade = self.transaction.modalidades.get_or_raise(modalidade_id)

        # Manter o próprio título é permitido; só conflita se pertencer a outra modalidade
        existente = self.transaction.modalidades.get_by_title(dados.titulo)

        if existente is not None and existente.modalidade_id != modalidade_id:
            raise ConflitoError("Já existe uma modalidade com esse título")

        with self.transaction:
            modalidade = self.transaction.modalidades.update(modalidade, dados.model_dump())

        return ModalidadeDTOResponse.model_validate(modalidade)

    def deletar(self, modalidade_id: int) -> None:
        modalidade = self.transaction.modalidades.get_or_raise(modalidade_id)

        try:
            with self.transaction:
                self.transaction.modalidades.delete(modalidade)

        except IntegridadeError as erro:
            # A FK de oportunidade.modalidade_id impede apagar uma modalidade em uso
            raise ConflitoError(
                "Modalidade possui oportunidades vinculadas e não pode ser removida"
            ) from erro
