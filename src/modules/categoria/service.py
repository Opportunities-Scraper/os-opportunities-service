from db.transaction import Transaction
from modules.categoria.dto import CategoriaDTORequest, CategoriaDTOResponse
from modules.categoria.model import Categoria
from modules.base_exceptions import ConflitoError, IntegridadeError, NaoEncontradoError


class CategoriaService:
    def __init__(self, transaction: Transaction):
        self.transaction = transaction

    def listar(self) -> list[CategoriaDTOResponse]:
        categorias = self.transaction.categorias.get_all()
        return [CategoriaDTOResponse.model_validate(c) for c in categorias]

    def buscar_por_id(self, categoria_id: int) -> CategoriaDTOResponse:
        categoria = self.transaction.categorias.get_or_raise(categoria_id)
        return CategoriaDTOResponse.model_validate(categoria)

    def buscar_por_titulo(self, categoria_nome: str) -> CategoriaDTOResponse:
        categoria = self.transaction.categorias.get_by_title(categoria_nome)

        if categoria is None:
            raise NaoEncontradoError("Categoria não encontrada")

        return CategoriaDTOResponse.model_validate(categoria)

    def adicionar(self, dados: CategoriaDTORequest) -> CategoriaDTOResponse:
        existente = self.transaction.categorias.get_by_title(dados.titulo)

        if existente is not None:
            raise ConflitoError("Já existe uma categoria com esse título")

        with self.transaction:
            categoria = self.transaction.categorias.insert(Categoria(**dados.model_dump()))

        return CategoriaDTOResponse.model_validate(categoria)

    def atualizar(self, categoria_id: int, dados: CategoriaDTORequest) -> CategoriaDTOResponse:
        categoria = self.transaction.categorias.get_or_raise(categoria_id)

        # Manter o próprio título é permitido; só conflita se pertencer a outra categoria
        existente = self.transaction.categorias.get_by_title(dados.titulo)

        if existente is not None and existente.categoria_id != categoria_id:
            raise ConflitoError("Já existe uma categoria com esse título")

        with self.transaction:
            categoria = self.transaction.categorias.update(categoria, dados.model_dump())

        return CategoriaDTOResponse.model_validate(categoria)

    def deletar(self, categoria_id: int) -> None:
        categoria = self.transaction.categorias.get_or_raise(categoria_id)

        try:
            with self.transaction:
                self.transaction.categorias.delete(categoria)

        except IntegridadeError as erro:
            # A FK de oportunidade.categoria_id impede apagar uma categoria em uso
            raise ConflitoError(
                "Categoria possui oportunidades vinculadas e não pode ser removida"
            ) from erro
