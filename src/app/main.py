from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from modules.exceptions import (
    ConflitoError,
    DomainError,
    IntegridadeError,
    NaoEncontradoError,
    ReferenciaInvalidaError,
)

from contextlib import asynccontextmanager
from db.database import Base, engine

from modules.modalidade.controller import router as modalidade_router
from modules.categoria.controller import router as categoria_router
from modules.favoritos.controller import router as favoritos_router
from modules.oportunidade.controller import router as oportunidade_router





@asynccontextmanager
async def lifespan(app: FastAPI):
    # No MySQL o schema já existe e é mantido fora deste serviço
    if engine.dialect.name == "sqlite":
        Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Opportunities Service", lifespan=lifespan) 

for router in (categoria_router, modalidade_router, oportunidade_router, favoritos_router):
    app.include_router(router)




# Único lugar que traduz erros de domínio para HTTP: services e repositories não conhecem status codes
STATUS_CODE_ERRO: dict[type[DomainError], int] = {
    NaoEncontradoError: status.HTTP_404_NOT_FOUND,
    ConflitoError: status.HTTP_409_CONFLICT,
    IntegridadeError: status.HTTP_409_CONFLICT,
    ReferenciaInvalidaError: status.HTTP_422_UNPROCESSABLE_CONTENT,
}


@app.exception_handler(DomainError)
async def handle_erro(request: Request, erro: DomainError) -> JSONResponse:
    status_code = STATUS_CODE_ERRO.get(type(erro), status.HTTP_400_BAD_REQUEST)

    # Mesmo formato do HTTPException, para as respostas da API não mudarem
    return JSONResponse(status_code=status_code, content={"detail": erro.mensagem})
