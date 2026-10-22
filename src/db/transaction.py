from types import TracebackType
from typing import Annotated, Self

from fastapi import Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.database import get_session
from modules.categoria.repository import CategoriaRepository
from modules.exceptions import IntegridadeError
from modules.favoritos.repository import FavoritosRepository
from modules.modalidade.repository import ModalidadeRepository
from modules.oportunidade.repository import OportunidadeRepository


# Controla a transação de uma operação de escrita. Os repositories só enviam o SQL
# (flush); quem decide gravar é o service, ao sair do bloco:
#
#     with self.transaction:
#         self.transaction.favoritos.delete(...)
#         self.transaction.oportunidades.delete(...)
#
# Se o bloco termina sem erro, tudo é gravado (commit). Se qualquer passo falhar,
# nada é gravado (rollback), inclusive o que os passos anteriores já tinham feito.
class Transaction:
    def __init__(self, session: Session):
        self.session = session

        # Os repositories nascem aqui, todos da mesma sessão da uow. Assim é
        # impossível um service usar um repository fora desta transação.
        self.categorias = CategoriaRepository(session)
        self.modalidades = ModalidadeRepository(session)
        self.oportunidades = OportunidadeRepository(session)
        self.favoritos = FavoritosRepository(session)


    def __enter__(self) -> Self:
        return self


    def __exit__(self, exception_type: type[BaseException] | None, exception: BaseException | None, traceback_type: TracebackType | None) -> None:

        if exception_type is not None:
            self.session.rollback()

            # Traduz o erro do SQLAlchemy para que os services não dependam do ORM
            if isinstance(exception, IntegrityError):
                raise IntegridadeError("A operação viola uma restrição do banco") from exception
            return

        try:
            self.session.commit()

        except IntegrityError as erro:
            self.session.rollback()

            raise IntegridadeError("A operação viola uma restrição do banco") from erro
        
        except Exception:
            self.session.rollback()
            raise


def get_transaction(session: Annotated[Session, Depends(get_session)]) -> Transaction:
    return Transaction(session)
