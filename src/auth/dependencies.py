from typing import Annotated

from fastapi import Depends, Header


# simula usuário autenticado para utilizar a tabela intermediária "favoritos"
def get_usuario_id(usuario_id: Annotated[int, Header(gt=0)]) -> int:
    return usuario_id


UsuarioId = Annotated[int, Depends(get_usuario_id)]
