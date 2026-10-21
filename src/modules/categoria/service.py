from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from db.unit_of_work import UnitOfWork
from modules.categoria.dto import CategoriaDTORequest, CategoriaDTOResponse
from modules.categoria.model import Categoria
from modules.categoria.repository import CategoriaRepository


class CategoriaService:
    def __init__(self, repository: CategoriaRepository, uow: UnitOfWork):
        self.repository = repository
        self.uow = uow


    def listar(self) -> list[CategoriaDTOResponse]:
        categorias = self.repository.get_all()
        return [CategoriaDTOResponse.model_validate(c) for c in categorias]


    def buscar_por_id(self, categoria_id: int) -> CategoriaDTOResponse:
        categoria = self.repository.get_by_id(categoria_id)

        if categoria is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoria não encontrada",
            )
        
        return CategoriaDTOResponse.model_validate(categoria)


    def buscar_por_titulo(self, categoria_nome: str) -> CategoriaDTOResponse:
        categoria = self.repository.get_by_title(categoria_nome)

        if categoria is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoria não encontrada",
            )

        return CategoriaDTOResponse.model_validate(categoria)


    def criar(self, dados: CategoriaDTORequest) -> CategoriaDTOResponse:
        existente = self.repository.get_by_title(dados.titulo)

        if existente is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe uma categoria com esse título",
            )
        
        with self.uow:
            categoria = self.repository.insert(Categoria(**dados.model_dump()))

        return CategoriaDTOResponse.model_validate(categoria)



    def atualizar(self, categoria_id: int, dados: CategoriaDTORequest) -> CategoriaDTOResponse:
        categoria = self.repository.get_by_id(categoria_id)

        if categoria is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoria não encontrada",
            )

        # Manter o próprio título é permitido; só conflita se pertencer a outra categoria
        existente = self.repository.get_by_title(dados.titulo)

        if existente is not None and existente.categoria_id != categoria_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe uma categoria com esse título",
            )

        with self.uow:
            categoria = self.repository.update(categoria, dados.model_dump())

        return CategoriaDTOResponse.model_validate(categoria)

    def deletar(self, categoria_id: int) -> None:
        categoria = self.repository.get_by_id(categoria_id)
        
        if categoria is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoria não encontrada",
            )
        
        try:
            with self.uow:
                self.repository.delete(categoria)

        except IntegrityError:
            # A FK de oportunidade.categoria_id impede apagar uma categoria em uso
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Categoria possui oportunidades vinculadas e não pode ser removida",
            )