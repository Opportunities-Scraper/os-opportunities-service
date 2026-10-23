# Popula o banco SQLite de desenvolvimento com dados de exemplo.
#
# Uso (sempre a partir da raiz do projeto, para o .env ser encontrado):
#     uv run python scripts/seed.py            # adiciona o que ainda não existe
#     uv run python scripts/seed.py --reset    # apaga tudo e popula do zero
#
# Os dados passam pelos services, então seguem as mesmas validações da API
# (DTOs, título e URL únicos, FKs). Rodar mais de uma vez não duplica nada.

import argparse
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Permite importar os módulos de src/ sem precisar configurar o PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from config.settings import settings

from db.database import Base, SessionLocal, engine
from db.transaction import Transaction

from modules.categoria.dto import CategoriaDTORequest
from modules.categoria.service import CategoriaService
from modules.exceptions import ConflitoError
from modules.favoritos.dto import FavoritosDTORequest
from modules.favoritos.service import FavoritosService
from modules.modalidade.dto import ModalidadeDTORequest
from modules.modalidade.service import ModalidadeService
from modules.oportunidade.dto import OportunidadeDTORequest
from modules.oportunidade.service import OportunidadeService

CATEGORIAS = ["Estágio", "Trainee", "Júnior", "Freelance"]

MODALIDADES = ["Remoto", "Presencial", "Híbrido"]

# As datas são relativas a hoje, para as vagas continuarem "atuais" sempre que o
# seed rodar. Os domínios example.com são reservados para exemplos e não existem.
OPORTUNIDADES = [
    {
        "slug": "estagio-backend",
        "titulo": "Estágio em Desenvolvimento Back-end",
        "descricao": "Apoio no desenvolvimento de APIs em Python com FastAPI e MySQL.",
        "pais": "BR",
        "cidade": "São Paulo",
        "categoria": "Estágio",
        "modalidade": "Remoto",
        "publicada_ha_dias": 3,
        "dias_para_encerrar": 25,
    },
    {
        "slug": "estagio-dados",
        "titulo": "Estágio em Análise de Dados",
        "descricao": "Construção de dashboards e consultas SQL para a área comercial.",
        "pais": "BR",
        "cidade": "Recife",
        "categoria": "Estágio",
        "modalidade": "Híbrido",
        "publicada_ha_dias": 10,
        "dias_para_encerrar": 5,
    },
    {
        "slug": "trainee-tecnologia",
        "titulo": "Programa de Trainee em Tecnologia",
        "descricao": "Programa de 18 meses com rotação entre times de produto e dados.",
        "pais": "BR",
        "cidade": "Belo Horizonte",
        "categoria": "Trainee",
        "modalidade": "Presencial",
        "publicada_ha_dias": 15,
        "dias_para_encerrar": 30,
    },
    {
        "slug": "trainee-engenharia-dados",
        "titulo": "Trainee em Engenharia de Dados",
        "descricao": "Pipelines de dados com Python, Airflow e nuvem.",
        "pais": "BR",
        "cidade": "Curitiba",
        "categoria": "Trainee",
        "modalidade": "Híbrido",
        "publicada_ha_dias": 1,
        "dias_para_encerrar": 45,
    },
    {
        "slug": "python-junior",
        "titulo": "Desenvolvedor Python Júnior",
        "descricao": "Manutenção de serviços internos e automações com Python.",
        "pais": "BR",
        "cidade": "Florianópolis",
        "categoria": "Júnior",
        "modalidade": "Remoto",
        "publicada_ha_dias": 7,
        "dias_para_encerrar": 20,
    },
    {
        "slug": "qa-junior",
        "titulo": "Analista de QA Júnior",
        "descricao": "Testes manuais e automatizados de aplicações web.",
        "pais": "BR",
        "cidade": "Porto Alegre",
        "categoria": "Júnior",
        "modalidade": "Presencial",
        "publicada_ha_dias": 4,
        "dias_para_encerrar": 12,
    },
    {
        "slug": "frontend-junior-lisboa",
        "titulo": "Desenvolvedor Front-end Júnior",
        "descricao": "Desenvolvimento de interfaces em React para produtos SaaS.",
        "pais": "PT",
        "cidade": "Lisboa",
        "categoria": "Júnior",
        "modalidade": "Remoto",
        "publicada_ha_dias": 2,
        "dias_para_encerrar": 28,
    },
    {
        "slug": "freelance-landing-page",
        "titulo": "Freelance: landing page em React",
        "descricao": "Criação de uma landing page responsiva com formulário de contato.",
        "pais": "BR",
        "cidade": "Rio de Janeiro",
        "categoria": "Freelance",
        "modalidade": "Remoto",
        "publicada_ha_dias": 6,
        "dias_para_encerrar": 8,
    },
    {
        # Já encerrada: útil para testar filtros de vagas ativas
        "slug": "estagio-suporte-encerrada",
        "titulo": "Estágio em Suporte Técnico",
        "descricao": "Atendimento a usuários internos e manutenção de equipamentos.",
        "pais": "BR",
        "cidade": "Salvador",
        "categoria": "Estágio",
        "modalidade": "Presencial",
        "publicada_ha_dias": 40,
        "dias_para_encerrar": -10,
    },
]

# usuario_id → slugs das oportunidades favoritadas
FAVORITOS = {
    1: ["estagio-backend", "python-junior", "trainee-engenharia-dados"],
    2: ["estagio-backend", "frontend-junior-lisboa"],
}


# As funções garantir_* tentam criar o registro. Se o service acusar duplicidade
# (ConflitoError), devolvem o id do que já existe. O bool indica se foi criado agora.


def garantir_categoria(service: CategoriaService, titulo: str) -> tuple[int, bool]:
    try:
        return service.adicionar(CategoriaDTORequest(titulo=titulo)).categoria_id, True
    except ConflitoError:
        return service.buscar_por_titulo(titulo).categoria_id, False


def garantir_modalidade(service: ModalidadeService, titulo: str) -> tuple[int, bool]:
    try:
        return service.adicionar(
            ModalidadeDTORequest(titulo=titulo)
        ).modalidade_id, True
    except ConflitoError:
        return service.buscar_por_titulo(titulo).modalidade_id, False


def garantir_oportunidade(
    service: OportunidadeService,
    transaction: Transaction,
    dados: OportunidadeDTORequest,
) -> tuple[int, bool]:
    try:
        return service.adicionar(dados).oportunidade_id, True
    except ConflitoError:
        # A URL já vem normalizada pelo DTO, igual à que foi gravada
        return transaction.oportunidades.get_by_url(
            dados.url_original
        ).oportunidade_id, False


def preparar_banco(resetar: bool) -> None:
    # Protege o banco compartilhado: só popula SQLite ou um MySQL marcado com BANCO_LOCAL=true
    if not (engine.dialect.name == "sqlite" or settings.banco_local):
        sys.exit(
            f"Abortado: DATABASE_URL aponta para um banco '{engine.dialect.name}' que não está "
            "marcado como local. Para popular um MySQL descartável (ex.: no Docker), "
            "defina BANCO_LOCAL=true no .env."
        )

    if resetar:
        Base.metadata.drop_all(engine)

    # Mesma criação de tabelas do lifespan, para o seed funcionar sem subir a API
    Base.metadata.create_all(engine)


def popular() -> dict[str, list[int]]:
    # [criados, já existentes] por entidade, para o resumo final
    contagem = {
        nome: [0, 0]
        for nome in ("categorias", "modalidades", "oportunidades", "favoritos")
    }

    def registrar(entidade: str, criado: bool) -> None:
        contagem[entidade][0 if criado else 1] += 1

    with SessionLocal() as session:
        transaction = Transaction(session)
        categorias = CategoriaService(transaction)
        modalidades = ModalidadeService(transaction)
        oportunidades = OportunidadeService(transaction)
        favoritos = FavoritosService(transaction)

        categoria_ids: dict[str, int] = {}
        for titulo in CATEGORIAS:
            categoria_ids[titulo], criado = garantir_categoria(categorias, titulo)
            registrar("categorias", criado)

        modalidade_ids: dict[str, int] = {}
        for titulo in MODALIDADES:
            modalidade_ids[titulo], criado = garantir_modalidade(modalidades, titulo)
            registrar("modalidades", criado)

        agora = datetime.now(UTC).replace(microsecond=0)
        oportunidade_ids: dict[str, int] = {}
        for vaga in OPORTUNIDADES:
            dados = OportunidadeDTORequest(
                titulo=vaga["titulo"],
                descricao=vaga["descricao"],
                url_original=f"https://vagas.example.com/{vaga['slug']}",
                pais=vaga["pais"],
                cidade=vaga["cidade"],
                data_publicacao=agora - timedelta(days=vaga["publicada_ha_dias"]),
                data_limite=agora + timedelta(days=vaga["dias_para_encerrar"]),
                modalidade_id=modalidade_ids[vaga["modalidade"]],
                categoria_id=categoria_ids[vaga["categoria"]],
            )
            oportunidade_ids[vaga["slug"]], criado = garantir_oportunidade(
                oportunidades, transaction, dados
            )
            registrar("oportunidades", criado)

        for usuario_id, slugs in FAVORITOS.items():
            for slug in slugs:
                dados_favorito = FavoritosDTORequest(
                    oportunidade_id=oportunidade_ids[slug]
                )
                try:
                    favoritos.adicionar(usuario_id, dados_favorito)
                    registrar("favoritos", True)
                except ConflitoError:
                    registrar("favoritos", False)

    return contagem


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Popula o banco SQLite de desenvolvimento."
    )
    parser.add_argument(
        "--reset", action="store_true", help="apaga todas as tabelas antes de popular"
    )
    args = parser.parse_args()

    preparar_banco(resetar=args.reset)
    contagem = popular()

    print(f"Banco: {engine.url.database}")
    for entidade, (criados, existentes) in contagem.items():
        print(f"  {entidade:<14} {criados:>2} criados, {existentes:>2} já existiam")


if __name__ == "__main__":
    main()
