from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from db.schema import handle_db_schema
from modules.categoria.controller import router as categoria_router
from modules.base_exceptions import (
    ConflitoError,
    DomainError,
    IntegridadeError,
    NaoEncontradoError,
    ReferenciaInvalidaError,
)
from modules.favoritos.controller import router as favoritos_router
from modules.modalidade.controller import router as modalidade_router
from modules.oportunidade.controller import router as oportunidade_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # SQLite ou banco local: cria as tabelas. Banco compartilhado: só confere se existem.
    handle_db_schema()
    yield



# uv run uvicorn app.main:app --app-dir src --reload

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
