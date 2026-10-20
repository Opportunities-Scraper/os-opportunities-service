from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from modules.categoria.dto import CategoriaDTORequest, CategoriaDTOResponse
from modules.categoria.model import Categoria
from modules.categoria.repository import CategoriaRepository


class CategoriaService:
    def __init__(self, repository: CategoriaRepository):
        self.repository = repository


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
        
        categoria = self.repository.insert(Categoria(**dados.model_dump()))

        return CategoriaDTOResponse.model_validate(categoria)



    def atualizar(self, categoria_id: int, dados: CategoriaDTORequest) -> CategoriaDTOResponse:
        categoria = self.repository.get_by_id(categoria_id)

        if categoria is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoria não encontrada",
            )

        elif dados.titulo is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe uma categoria com esse título",
            )
    
        categoria.titulo = dados.titulo
        return CategoriaDTOResponse.model_validate(self.repository.insert(categoria))

    def deletar(self, categoria_id: int) -> None:
        categoria = self.repository.get_by_id(categoria_id)
        
        if categoria is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Categoria não encontrada",
            )
        
        try:
            self.repository.delete(categoria)
            
        except IntegrityError:
            # A FK de oportunidade.categoria_id impede apagar uma categoria em uso
            self.repository.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Categoria possui oportunidades vinculadas e não pode ser removida",
            )