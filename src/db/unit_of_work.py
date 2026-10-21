from types import TracebackType
from typing import Self

from sqlalchemy.orm import Session


# Controla a transação de uma operação de escrita. Os repositories só enviam o SQL
# (flush); quem decide gravar é o service, ao sair do bloco:
#
#     with self.uow:
#         self.repository_a.insert(...)
#         self.repository_b.delete(...)
#
# Se o bloco termina sem erro, tudo é gravado (commit). Se qualquer passo falhar,
# nada é gravado (rollback), inclusive o que os passos anteriores já tinham feito.
# Para isso funcionar, a UnitOfWork e os repositories precisam usar a mesma Session.
class UnitOfWork:
    def __init__(self, session: Session):
        self.session = session

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self.session.rollback()
            return

        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
