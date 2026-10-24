# Opportunities Service

API em **FastAPI** que gerencia as **oportunidades** (vagas de estágio, trainee, júnior...) do projeto **Opportunities Scraper**, e os **favoritos** dos usuários.

As vagas são coletadas de sites externos por um scraper. Este serviço guarda essas vagas, organiza-as por categoria e modalidade, e permite que cada usuário salve as que mais lhe interessam.

---

## Contexto

O projeto inteiro compartilha um banco **MySQL** com o modelo abaixo:

![Modelo do banco de dados](img/megadados.jpeg)

Este repositório é **um dos serviços** do sistema e é responsável só pela parte de oportunidades:

| Tabela | Neste serviço? | Descrição |
|---|---|---|
| `categoria` | ✅ Sim | Tipo da vaga: Estágio, Trainee, Júnior... |
| `modalidade` | ✅ Sim | Formato de trabalho: Remoto, Presencial, Híbrido |
| `oportunidade` | ✅ Sim | A vaga em si: título, descrição, URL original, local, datas, categoria e modalidade |
| `favoritos` | ✅ Sim | Relação muitos-para-muitos entre usuário e oportunidade |
| `usuario` | ❌ Não | Pertence ao serviço de usuários; aqui aparece só como `usuario_id` |
| `plano` | ❌ Não | Pertence ao serviço de usuários |

### O que é cada tabela

- **Oportunidade:** é a vaga em si, coletada pelo scraper. Guarda o título, a descrição, o link para a vaga no site de origem (`url_original`), o país e a cidade, a data de publicação e a data limite para se candidatar. Cada oportunidade pertence a uma categoria e a uma modalidade.
- **Categoria:** refere-se ao tipo ou nível da oportunidade, como estágio, trainee, júnior ou freelance.
- **Modalidade:** refere-se ao formato de trabalho da oportunidade, seja presencial, remoto, híbrido etc.
- **Favoritos:** refere-se às oportunidades que cada usuário salvou para ver depois. É a ligação entre um usuário e uma oportunidade, com a data em que foi favoritada. Um usuário pode favoritar várias oportunidades, e uma oportunidade pode ser favoritada por vários usuários.
- **Usuário** *(outro serviço)*: refere-se à pessoa cadastrada no sistema, com e-mail, nome de usuário, senha (guardada como hash), se a conta está ativa, se é administrador e qual plano possui.
- **Plano** *(outro serviço)*: refere-se ao tipo de assinatura do usuário.

**Regras de negócio principais:**
- Não podem existir duas categorias (ou duas modalidades) com o mesmo título.
- A **URL original** identifica a vaga: duas oportunidades não podem ter a mesma URL. O título pode repetir, porque empresas diferentes publicam vagas com o mesmo nome.
- A `data_limite` não pode ser anterior à `data_publicacao`.
- Uma categoria ou modalidade **em uso** por alguma oportunidade não pode ser apagada.
- Apagar uma oportunidade **remove também os favoritos** ligados a ela, numa única transação.

---

## Tecnologias

| Ferramenta | Uso |
|---|---|
| Python 3.13 | Linguagem |
| [FastAPI](https://fastapi.tiangolo.com/) | Framework da API |
| [Uvicorn](https://www.uvicorn.org/) | Servidor que coloca a API no ar |
| [SQLAlchemy 2](https://www.sqlalchemy.org/) | ORM / acesso ao banco |
| [Pydantic](https://docs.pydantic.dev/) | Validação dos dados e das configurações |
| SQLite / MySQL 8 | Banco de dados (SQLite para desenvolvimento; MySQL para o ambiente real) |
| [uv](https://docs.astral.sh/uv/) | Gerenciador de Python, dependências e ambiente virtual |

---

## Rotas

A documentação interativa (Swagger) fica em **`http://127.0.0.1:8000/docs`** com a API rodando. Lá dá para testar cada rota pelo navegador.

### Categoria e modalidade

As duas têm as mesmas rotas. Troque `categoria` por `modalidade`:

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/categoria` | Lista todas |
| `GET` | `/categoria/{id}` | Busca por id |
| `GET` | `/categoria/titulo/{titulo}` | Busca pelo título |
| `POST` | `/categoria` | Cria. Corpo: `{"titulo": "Estágio"}` |
| `PUT` | `/categoria/{id}` | Atualiza o título |
| `DELETE` | `/categoria/{id}` | Apaga (409 se estiver em uso por alguma oportunidade) |

### Oportunidade

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/oportunidade` | Lista todas |
| `GET` | `/oportunidade/{id}` | Busca por id |
| `GET` | `/oportunidade/categoria/{categoria_id}` | Filtra por categoria |
| `GET` | `/oportunidade/modalidade/{modalidade_id}` | Filtra por modalidade |
| `POST` | `/oportunidade` | Cria (veja o corpo abaixo) |
| `PUT` | `/oportunidade/{id}` | Atualiza (exige todos os campos) |
| `DELETE` | `/oportunidade/{id}` | Apaga a oportunidade e os favoritos ligados a ela |

Exemplo de corpo para criar uma oportunidade:

```json
{
  "titulo": "Estágio em Desenvolvimento Back-end",
  "descricao": "Apoio no desenvolvimento de APIs em Python.",
  "url_original": "https://vagas.example.com/estagio-backend",
  "pais": "BR",
  "cidade": "São Paulo",
  "data_publicacao": "2026-10-20T09:00:00-03:00",
  "data_limite": "2026-12-20T18:00:00-03:00",
  "modalidade_id": 1,
  "categoria_id": 1
}
```

Datas com fuso horário são convertidas e gravadas em UTC.

### Favoritos

Todas as rotas de favoritos exigem o header **`usuario-id`** com o id do usuário:

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/favoritos` | Lista os favoritos do usuário, com os dados de cada oportunidade |
| `GET` | `/favoritos/{oportunidade_id}` | Diz se a oportunidade está nos favoritos do usuário (200 ou 404) |
| `POST` | `/favoritos` | Favorita. Corpo: `{"oportunidade_id": 1}` |
| `DELETE` | `/favoritos/{oportunidade_id}` | Remove dos favoritos |

```bash
curl http://127.0.0.1:8000/favoritos -H "usuario-id: 1"
```

> ⚠️ **Autenticação provisória.** Por enquanto, o usuário é identificado só pelo header `usuario-id`, sem verificação. Isso é temporário, até o serviço de usuários emitir tokens (JWT). **Não use assim em produção.**

### Respostas de erro

Os erros seguem o formato padrão do FastAPI, `{"detail": "mensagem"}`:

| Status | Quando |
|---|---|
| `404` | O registro não existe |
| `409` | Conflito: título ou URL duplicados, registro em uso, favorito repetido |
| `422` | Dados inválidos, ou uma `categoria_id`/`modalidade_id` que não existe |

---

## Instalando o uv

O projeto usa o **[uv](https://docs.astral.sh/uv/)** para gerenciar a versão do Python, as dependências e o ambiente virtual. Você **não precisa** ter o Python 3.13 instalado: o uv baixa a versão certa sozinho.

**Linux e macOS:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Feche e reabra o terminal, e confira:
```bash
uv --version
```

### Os arquivos que o uv usa

| Arquivo | Para que serve |
|---|---|
| `pyproject.toml` | Lista as dependências do projeto (e as de desenvolvimento, como `ruff` e `pytest`) |
| `uv.lock` | Fixa a versão **exata** de cada dependência, para todos instalarem o mesmo |
| `.python-version` | A versão do Python do projeto (3.13) |
| `.venv/` | O ambiente virtual, criado pelo uv. **Não é versionado.** |

### Comandos essenciais

```bash
uv sync                  # cria o .venv e instala tudo do uv.lock (rode após clonar)
uv run <comando>         # roda um comando usando o Python e as dependências do projeto
uv add <pacote>          # adiciona uma dependência (atualiza pyproject.toml e uv.lock)
uv add --dev <pacote>    # adiciona uma dependência só de desenvolvimento
uv remove <pacote>       # remove uma dependência
```

**Por que sempre `uv run`?** Ele garante que o comando use o Python **do projeto** (do `.venv`), e não o do sistema. Ele também sincroniza as dependências antes de rodar, se o `uv.lock` tiver mudado. Assim não é preciso ativar o ambiente virtual com `source .venv/bin/activate`.

---

## Instalação

```bash
git clone <url-do-repositório>
cd os-opportunities-service
uv sync
```

O `uv sync` baixa o Python 3.13 (se necessário), cria a pasta `.venv` e instala todas as dependências.

---

## Configurando o banco de dados

A aplicação lê a configuração de um arquivo **`.env`** na raiz do projeto. Ele **não é versionado**, porque pode conter senhas. Crie o seu a partir do modelo, que já traz as duas opções comentadas:

```bash
cp .env.example .env
```

Depois, deixe ativa apenas uma das opções abaixo.

### Opção 1: SQLite (mais simples, recomendado para começar)

O banco é um único arquivo, criado automaticamente. Não é preciso instalar nada.

```env
DATABASE_URL=sqlite:///mock.sqlite
```

Ao subir, a API cria o arquivo `mock.sqlite` e as tabelas sozinha.

### Opção 2: MySQL no Docker (igual ao ambiente real)

Requer o [Docker](https://docs.docker.com/get-docker/). Suba um MySQL 8 num container:

```bash
docker run -d \
  --name mysql-opportunities \
  -p 127.0.0.1:3307:3306 \
  -v mysql-opportunities-dados:/var/lib/mysql \
  -e MYSQL_ROOT_PASSWORD='troque-esta-senha-root' \
  -e MYSQL_DATABASE='opportunities_service' \
  -e MYSQL_USER='app' \
  -e MYSQL_PASSWORD='troque-esta-senha-app' \
  mysql:8.0.45
```

E no `.env`:

```env
DATABASE_URL=mysql+pymysql://app:troque-esta-senha-app@127.0.0.1:3307/opportunities_service
BANCO_LOCAL=true
```

| Variável | Significado |
|---|---|
| `DATABASE_URL` | Qual banco usar. São aceitos só `sqlite://` e `mysql+pymysql://`; um `mysql://` é recusado com uma mensagem explicando o prefixo certo. |
| `BANCO_LOCAL` | Marca o MySQL como **local e descartável**. Com ela, a API cria as tabelas que faltam e o script de seed pode popular o banco. |

> ⚠️ **Nunca use `BANCO_LOCAL=true` apontando para o MySQL compartilhado.** Sem ela, a API não cria nem altera tabelas no MySQL: só confere se o schema existe e, se faltar alguma tabela, não sobe e diz quais estão faltando. Isso protege o banco real.

O passo a passo completo do MySQL no Docker, com o porquê de cada opção, está em [markdown/mysql.md](markdown/mysql.md).

### Populando com dados de exemplo

O script `scripts/seed.py` insere dados de exemplo: 4 categorias, 3 modalidades, 9 oportunidades e 5 favoritos.

```bash
uv run python scripts/seed.py            # adiciona o que ainda não existe (pode rodar várias vezes)
uv run python scripts/seed.py --reset    # APAGA as 4 tabelas e popula do zero
```

O script funciona com o SQLite e com um MySQL marcado com `BANCO_LOCAL=true`. Ele se recusa a rodar em qualquer outro banco.

---

## Rodando o projeto

Sempre **a partir da raiz do projeto**, para o `.env` ser encontrado:

```bash
uv run uvicorn app.main:app --app-dir src --reload
```

| Parte | Significado |
|---|---|
| `uvicorn` | O servidor que coloca a API no ar |
| `app.main:app` | A variável `app` dentro de `src/app/main.py` |
| `--app-dir src` | Indica que o código fica na pasta `src/` |
| `--reload` | Reinicia sozinho ao salvar um arquivo (só para desenvolvimento) |

Depois, acesse:
- **Swagger:** http://127.0.0.1:8000/docs
- **Exemplo:** http://127.0.0.1:8000/oportunidade

### Resumo: do zero até a API no ar (com SQLite)

```bash
uv sync
cp .env.example .env          # o modelo já vem configurado para SQLite
uv run python scripts/seed.py
uv run uvicorn app.main:app --app-dir src --reload
```

### Problemas comuns

| Erro | Causa e solução |
|---|---|
| `Address already in use` | Outro processo já usa a porta 8000 (geralmente outro uvicorn esquecido aberto). Encerre-o, ou use `--port 8001`. |
| `Field required` em `database_url` | O `.env` não existe (crie com `cp .env.example .env`), ou o comando não foi rodado da raiz do projeto |
| `Tabelas ausentes no banco ...` | O MySQL não tem as tabelas. Se for um banco local, adicione `BANCO_LOCAL=true` ao `.env`. |
| `422` com `"loc": ["header", "usuario-id"]` | Faltou o header `usuario-id` numa rota de favoritos |
| Aviso `VIRTUAL_ENV ... does not match` | Um ambiente virtual de outra pasta está ativado. Ele é ignorado pelo `uv run`; rode `deactivate` ou abra um terminal novo. |

---

## Estrutura do projeto

```
src/
├── app/main.py             # Cria a aplicação, registra as rotas e traduz erros para HTTP
├── auth/dependencies.py    # Identificação do usuário (provisória, via header)
├── config/settings.py      # Leitura e validação do .env
├── db/
│   ├── database.py         # Conexão com o banco
│   ├── schema.py           # Criação/verificação das tabelas ao iniciar
│   └── transaction.py      # Controle de transações (padrão Unit of Work)
└── modules/                # Um módulo por entidade
    ├── categoria/          # cada um com: controller, dto, service, repository, model
    ├── modalidade/
    ├── oportunidade/
    └── favoritos/
scripts/
├── seed.py                 # Popula o banco com dados de exemplo
└── data/                   # Exemplos de requisições e respostas esperadas (JSON)
markdown/                   # Documentação técnica
```

Cada requisição percorre as camadas `controller` (HTTP) → `service` (regras de negócio) → `repository` (banco).

## Documentação técnica

| Documento | Conteúdo |
|---|---|
| [markdown/arquitetura.md](markdown/arquitetura.md) | Estilo arquitetural, dados, decisões (ADRs), riscos e escalabilidade |
| [markdown/design_patterns.md](markdown/design_patterns.md) | Os padrões usados (Repository, Unit of Work, DTO...) e por quê |
| [markdown/mysql.md](markdown/mysql.md) | Guia do MySQL no Docker |
