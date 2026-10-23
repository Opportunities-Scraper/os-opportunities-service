# Arquitetura do Opportunities Service

Este documento descreve a arquitetura do serviço usando o vocabulário e as técnicas de três livros:

| Sigla | Livro |
|---|---|
| **[FSA]** | Mark Richards e Neal Ford, *Fundamentals of Software Architecture* (O'Reilly, 2020) |
| **[HP]** | Neal Ford, Mark Richards, Pramod Sadalage e Zhamak Dehghani, *Software Architecture: The Hard Parts* (O'Reilly, 2021) |
| **[SDI]** | Alex Xu, *System Design Interview: An Insider's Guide*, 2ª edição |

Os padrões de código (Repository, Unit of Work, DTO...) estão em [design_patterns.md](design_patterns.md).

---

## 1. Ponto de partida: as duas leis

O [FSA] (cap. 1) abre com duas leis que guiam este documento inteiro:

> *Everything in software architecture is a trade-off.* (Primeira Lei)
>
> *Why is more important than how.* (Segunda Lei)

Por isso, cada decisão abaixo vem acompanhada do **porquê** e do **que se perdeu** ao tomá-la. O próprio [FSA] lembra que não existe a melhor arquitetura, só a *least worst*: a menos ruim para o contexto.

---

## 2. Contexto do sistema

O serviço guarda as **oportunidades** (vagas) coletadas por um scraper e os **favoritos** dos usuários. Ele faz parte de um sistema maior que compartilha um único banco MySQL:

| Tabela | Quem escreve | Papel neste serviço |
|---|---|---|
| `categoria` | este serviço | Tipo da vaga (Estágio, Trainee...) |
| `modalidade` | este serviço | Formato (Remoto, Presencial...) |
| `oportunidade` | este serviço (e, no futuro, o scraper) | A vaga |
| `favoritos` | este serviço | Relação N:N entre usuário e oportunidade |
| `usuario`, `plano` | outro serviço | Não mapeadas aqui; o usuário aparece só como `usuario_id` |

```
                 ┌─────────────────────┐
  Cliente HTTP ─►│ Opportunities       │──┐
                 │ Service (FastAPI)   │  │
                 └─────────────────────┘  │
                                          ▼
  Scraper ──────(futuro)───────────► ┌──────────┐ ◄──── Serviço de usuários
                                     │  MySQL   │       (usuario, plano)
                                     │compartilh│
                                     └──────────┘
```

---

## 3. Características arquiteturais

O [FSA] (caps. 4 e 5) chama de **características arquiteturais** os requisitos que não são funcionalidades, mas que definem o sucesso do sistema (as "-ilidades"). O livro recomenda escolher **poucas**, porque cada uma tem custo e elas competem entre si.

### As que guiam este projeto

| Característica | Por que importa aqui | Como a arquitetura atende |
|---|---|---|
| **Manutenibilidade / evolutividade** | Projeto de estudo que muda o tempo todo; regras de negócio ainda em definição | Módulos por domínio, camadas com papéis claros, services sem dependência de HTTP ou ORM |
| **Integridade dos dados** | Favoritos não podem apontar para vagas inexistentes; vagas não podem duplicar | FKs no banco, Unit of Work com transações atômicas, validação nos DTOs |
| **Testabilidade** | Precisa ser possível testar regras sem subir servidor nem MySQL | Injeção de dependência, SQLite local, `TestClient`, exemplos em JSON |
| **Simplicidade / custo** | Um desenvolvedor, sem orçamento de infraestrutura | Monolito em um processo, um banco, sem mensageria |

### As que **não** foram priorizadas, de propósito

| Característica | Por que ficou de fora (por enquanto) |
|---|---|
| Elasticidade e escalabilidade extrema | Não há volume que justifique; ver a seção 8 para o caminho, se for preciso |
| Desempenho fino | Consultas simples por chave; o gargalo provável é o banco, não o código |
| **Segurança** | ⚠️ É uma **lacuna**, não uma escolha: a autenticação é provisória (seção 9) |

---

## 4. Estilo arquitetural

### 4.1 Monolito modular, particionado por domínio

O [FSA] (cap. 8) diz que a **primeira** decisão sobre componentes é o **particionamento de nível superior**:

- **Particionamento técnico:** pastas por papel técnico (`controllers/`, `services/`, `repositories/`). Um mesmo domínio fica "espalhado" por todas as camadas.
- **Particionamento por domínio:** pastas por área de negócio. Cada uma pode ter suas camadas por dentro.

Este projeto usa **particionamento por domínio no nível superior** e **camadas dentro de cada domínio**:

```
src/modules/
├── categoria/      ┐
├── modalidade/     │  cada pasta = um domínio
├── oportunidade/   │  dentro dela: controller → service → repository → model
└── favoritos/      ┘
```

O [FSA] aponta, entre as vantagens do particionamento por domínio:
- refletir como o negócio funciona;
- aproximar-se dos estilos *modular monolith* e *microservices*;
- facilitar uma eventual migração para uma arquitetura distribuída.

A desvantagem citada é que código transversal aparece em vários lugares. Aqui, isso é mitigado pelo [BaseRepository](src/modules/repository.py) e pelas [exceções de domínio](src/modules/exceptions.py) compartilhadas.

### 4.2 As camadas dentro de cada módulo

O [FSA] (cap. 10) descreve a arquitetura em camadas com quatro níveis típicos: apresentação, negócio, persistência e banco. A correspondência aqui:

| Camada [FSA] | Neste projeto | Responsabilidade |
|---|---|---|
| Apresentação | `controller.py` + `dto.py` | HTTP: rotas, validação de entrada, formato de saída |
| Negócio | `service.py` | Regras: unicidade, existência, o que é atômico |
| Persistência | `repository.py` + `db/transaction.py` | SQL e controle de transação |
| Banco | `model.py` + MySQL | Estrutura das tabelas |

**Camadas fechadas.** O [FSA] distingue camadas *fechadas* (a requisição não pode pular camadas) de *abertas*. Aqui todas são fechadas: um controller nunca chama um repository diretamente. Isso garante o que o livro chama de **layers of isolation**: mudar uma camada não afeta as outras, desde que o contrato entre elas se mantenha.

Exemplo concreto: o service lança `NaoEncontradoError`, e só o [main.py](src/app/main.py) sabe que isso vira HTTP 404. Trocar o FastAPI por outro framework não tocaria nenhum service.

### 4.3 Atenção: o *architecture sinkhole*

O [FSA] alerta para o anti-padrão **architecture sinkhole**: requisições que atravessam as camadas sem nenhuma lógica, só repassando a chamada. A regra prática do livro é **80/20**: até 20% de requisições assim é aceitável; perto de 80% indica que o estilo em camadas não serve para o problema.

Medição neste projeto:

| Rotas | Quantidade | Comportamento no service |
|---|---|---|
| GET de listagem, por id, filtros e favorito | ~10 | Só chamam o repository e convertem para DTO (sinkhole) |
| GET por título | 2 | Adicionam uma checagem mínima (`None` → 404) |
| POST, PUT, DELETE | 11 | Aplicam regras reais (unicidade, FKs, atomicidade) |

São **cerca de 40 a 50%** de rotas "de passagem": acima dos 20% ideais, mas longe dos 80% que invalidariam o estilo. É o perfil esperado de uma API majoritariamente CRUD. Duas formas de agir, se isso crescer:
1. **Aceitar:** a camada vazia custa pouco e mantém o padrão uniforme (escolha atual).
2. **Abrir a camada só para leituras:** o controller consultaria o repository diretamente nas rotas GET. O [FSA] lembra o custo disso: fica mais difícil controlar mudanças.

### 4.4 *Architecture quantum*

O [HP] (cap. 2) define o **architecture quantum** como um artefato implantável de forma independente, com alta coesão funcional, alto acoplamento estático e acoplamento dinâmico síncrono.

Este serviço inteiro é **um único quantum**: os quatro módulos são implantados juntos, num só processo, sobre um só banco. Na prática, isso significa:
- todos os módulos têm **as mesmas características operacionais** (se oportunidade precisar escalar, favoritos escala junto);
- transações entre módulos são simples, porque estão no mesmo banco (seção 6).

---

## 5. Modularidade e acoplamento

### 5.1 Acoplamento aferente e eferente

O [FSA] (cap. 3) mede o acoplamento com duas métricas:
- **aferente:** conexões que **chegam** a um componente;
- **eferente:** conexões que **saem** dele.

Os pontos de maior acoplamento no projeto:

| Componente | Acoplamento | Observação |
|---|---|---|
| [db/transaction.py](src/db/transaction.py) | **Eferente alto:** importa os repositories dos 4 módulos | Todo módulo novo exige alterá-lo. É o preço de garantir a mesma sessão para todos (ver [design_patterns.md](design_patterns.md)). |
| [modules/repository.py](src/modules/repository.py) e [modules/exceptions.py](src/modules/exceptions.py) | **Aferente alto:** usados por todos os módulos | Esperado para código base; mudanças aqui afetam tudo e precisam de cuidado. |
| `favoritos` → `oportunidade` | Favoritos importa o `model` e o `DTO` de oportunidade | Acoplamento entre domínios; ver 5.3. |

### 5.2 Conascência

O [FSA] (cap. 3) usa a **conascência** para classificar a *força* de um acoplamento. As regras de Page-Jones citadas no livro:
1. minimizar a conascência entre fronteiras de encapsulamento;
2. maximizar a conascência **dentro** das fronteiras;
3. converter formas fortes de conascência em formas fracas.

Exemplos reais deste projeto:

| Tipo de conascência | Onde aparece | Situação |
|---|---|---|
| **De nome** (a mais fraca e desejável) | Controllers chamam `service.adicionar(...)` | ✅ Ferramentas de refatoração resolvem renomeações |
| **De tipo** | Services recebem e devolvem DTOs tipados | ✅ O Pylance acusa incompatibilidades |
| **De posição** | `get_favorito(usuario_id, oportunidade_id)`: a ordem precisa casar com a chave composta | ⚠️ Inverter os argumentos não dá erro, só retorna o registro errado. Argumentos nomeados (`usuario_id=...`) converteriam em conascência de nome. |
| **De significado** | O mapa `STATUS_CODE_ERRO` em [main.py](src/app/main.py) associa cada exceção a um status | ✅ Concentrado em um único lugar |
| **De execução** | Na `Transaction`, o `flush` precisa vir antes do `commit` | ✅ Encapsulado dentro do componente, como a regra 2 recomenda |

### 5.3 Reuso e fronteiras entre módulos

O [HP] (cap. 8) analisa o custo do reuso de código. No projeto, o reuso aparece de duas formas:

- **Código base compartilhado** (`BaseRepository`, exceções): reuso técnico, estável e de baixo risco.
- **Um módulo importando o model e o DTO de outro** (`favoritos` usa `Oportunidade` e `OportunidadeDTOResponse`): reuso de domínio. O [FSA] (cap. 13) chama a versão extrema disso, uma biblioteca única com todas as entidades, de "a forma menos eficaz" de organizar serviços que compartilham banco, porque toda mudança de tabela afeta todos.

No estado atual (um único quantum), esse acoplamento é aceitável e evita duplicação. Se `favoritos` um dia virar um serviço separado, ele terá de trocar o import por uma chamada à API de oportunidades.

---

## 6. Dados

### 6.1 Banco compartilhado

O serviço divide o MySQL com o serviço de usuários. O [HP] (cap. 6) lista seis **desintegradores de dados**, motivos que justificam separar um banco. Avaliando cada um para este projeto:

| Desintegrador [HP] | Pergunta do livro | Situação atual |
|---|---|---|
| Controle de mudança | Quantos serviços uma mudança de tabela afeta? | Baixo risco: cada serviço escreve em tabelas próprias. A exceção é a FK `favoritos.usuario_id` → `usuario`. |
| Gerenciamento de conexões | O banco aguenta as conexões de vários serviços? | Sem problema na escala atual (pool padrão: 15 conexões por processo) |
| Escalabilidade | O banco acompanha a demanda dos serviços? | Sem problema na escala atual |
| Tolerância a falhas | Quantos serviços caem se o banco cair? | ⚠️ Todos. É o principal custo do banco compartilhado. |
| Quantum | O banco compartilhado força um único quantum? | Sim, e hoje isso é aceito |
| Tipo de banco | Vale usar bancos de tipos diferentes? | Não há necessidade |

**Conclusão:** manter o banco compartilhado. Reavaliar quando o scraper gerar carga de escrita relevante, ou se a indisponibilidade conjunta virar problema.

### 6.2 Posse dos dados (*data ownership*)

A regra prática do [HP] (cap. 9): **o serviço que escreve numa tabela é o dono dela**. O livro distingue três cenários:

| Cenário [HP] | Definição | Neste sistema |
|---|---|---|
| *Single ownership* | Um único serviço escreve | `categoria`, `modalidade`, `favoritos`: só este serviço |
| *Joint ownership* | Alguns serviços do mesmo domínio escrevem | `oportunidade`, **se** o scraper passar a gravar direto no banco |
| *Common ownership* | Quase todos os serviços escrevem | Não ocorre |

**Decisão recomendada para o scraper:** aplicar a **técnica do delegado** do [HP]. Um único dono (este serviço) escreve na tabela `oportunidade`, e o scraper envia as vagas pela API. Isso mantém as regras (URL única, FKs válidas, datas normalizadas) em um único lugar.

**Escrita entre módulos dentro do serviço.** Desde a regra "apagar uma oportunidade apaga os favoritos dela", `OportunidadeService.deletar` escreve na tabela `favoritos` (por meio de `FavoritosRepository`). Dentro de um único quantum isso é seguro, porque a operação é uma transação ACID. Se os módulos fossem separados em serviços, isso viraria uma **transação distribuída**, e o [HP] (caps. 9 a 12) mostra que esse é um dos problemas mais difíceis da área (sagas, compensações, consistência eventual).

### 6.3 Transações

O [HP] (cap. 9) define a transação **ACID**: atomicidade, consistência, isolamento e durabilidade. O projeto usa transações ACID locais, controladas pelo padrão **Unit of Work** (detalhado em [design_patterns.md](design_patterns.md)):

```python
with self.transaction:
    self.transaction.favoritos.delete_by_oportunidade(oportunidade_id)
    self.transaction.oportunidades.delete(oportunidade)
```

Ou os dois passos acontecem, ou nenhum acontece. Isso foi verificado forçando uma falha no segundo passo: os favoritos voltaram.

---

## 7. Decisões arquiteturais (ADRs)

O [FSA] (cap. 19) recomenda registrar decisões em **Architecture Decision Records**: textos curtos com **Título, Status, Contexto, Decisão e Consequências**, mais as seções opcionais **Compliance** (como verificar que a decisão é seguida) e **Notas**. O status pode ser *Proposed*, *Accepted* ou *Superseded* (substituído por outro ADR). Esse histórico evita rediscutir decisões já tomadas.

As decisões deste projeto, no formato do livro:

### ADR 1. Monolito modular particionado por domínio
- **Status:** Accepted
- **Contexto:** Um desenvolvedor, quatro entidades pequenas, sem demanda de escala. Microsserviços trariam rede, implantação e consistência distribuída sem benefício.
- **Decisão:** Um único serviço FastAPI, com pastas por domínio e camadas fechadas dentro de cada uma.
- **Consequências:** (+) Simples, barato, transações ACID entre módulos. (−) Um único quantum: tudo escala e cai junto.
- **Compliance:** Nenhum controller importa repository; nenhum service importa `fastapi` ou `sqlalchemy` (verificável com `grep`; ver seção 10).

### ADR 2. Exceções de domínio traduzidas em um único ponto
- **Status:** Accepted
- **Contexto:** Services lançavam `HTTPException` e capturavam `IntegrityError`, acoplando a regra de negócio ao framework e ao ORM.
- **Decisão:** Services lançam exceções de [modules/exceptions.py](src/modules/exceptions.py); a `Transaction` traduz `IntegrityError` → `IntegridadeError`; o [main.py](src/app/main.py) traduz para status HTTP.
- **Consequências:** (+) Services reutilizáveis fora do HTTP; o [scripts/seed.py](scripts/seed.py) já faz isso. (−) Uma indireção a mais para quem lê.

### ADR 3. Unit of Work controla as transações
- **Status:** Accepted, substitui a decisão anterior de cada repository fazer o próprio `commit`
- **Contexto:** Operações que alteram mais de uma tabela ficavam gravadas pela metade quando um passo falhava.
- **Decisão:** Repositories fazem só `flush`; o service delimita a transação com `with self.transaction:`; a `Transaction` cria os repositories com a mesma sessão.
- **Consequências:** (+) Atomicidade garantida. (−) A `Transaction` conhece todos os repositories (acoplamento eferente alto).

### ADR 4. A URL identifica a oportunidade
- **Status:** Accepted
- **Contexto:** Vagas de empresas diferentes repetem títulos ("Estágio em TI"), e o scraper vai coletar a mesma vaga várias vezes.
- **Decisão:** A duplicidade é verificada pela `url_original` (normalizada pelo DTO), não pelo título.
- **Consequências:** (+) Sem falsos conflitos; a coleta repetida é detectada. (−) Sem constraint `UNIQUE` no banco, duas requisições simultâneas podem passar pela verificação (seção 9).

### ADR 5. Apagar uma oportunidade apaga os favoritos dela
- **Status:** Accepted, substitui a regra anterior (409 se a vaga estivesse favoritada)
- **Contexto:** Vagas expiram e somem dos sites de origem; bloquear a remoção por causa de favoritos deixaria vagas mortas no sistema.
- **Decisão:** `OportunidadeService.deletar` remove os favoritos e a vaga na mesma transação.
- **Consequências:** (+) Remoção sempre possível, sem favoritos órfãos. (−) O usuário perde o favorito sem aviso; o módulo de oportunidade passa a escrever em `favoritos` (seção 6.2).

### ADR 6. Autenticação provisória por header
- **Status:** Proposed, a ser substituída por JWT emitido pelo serviço de usuários
- **Contexto:** O serviço de usuários ainda não emite tokens.
- **Decisão:** O `usuario_id` vem do header `usuario-id`, lido em um único ponto: [auth/dependencies.py](src/auth/dependencies.py).
- **Consequências:** (+) A troca futura afeta só esse arquivo. (−) Qualquer cliente pode se passar por outro usuário. **Não pode ir para produção assim.**

### ADR 7. SQLite para desenvolvimento local
- **Status:** Accepted
- **Contexto:** Testar sem depender do MySQL compartilhado.
- **Decisão:** Trocar a `DATABASE_URL`; com SQLite, ligar as FKs (`PRAGMA foreign_keys=ON`) e criar as tabelas no `lifespan`.
- **Consequências:** (+) Ciclo de desenvolvimento rápido; o [seed](scripts/seed.py) popula dados de exemplo. (−) Diferenças de comportamento: o SQLite compara texto de forma exata, enquanto o MySQL ignora maiúsculas e acentos.

---

## 8. Escalabilidade: o caminho, se for preciso

O [SDI] (cap. 1) apresenta a evolução de um sistema "de zero a milhões de usuários" e resume as práticas assim:

> Keep web tier stateless · Build redundancy at every tier · Cache data as much as you can · Support multiple data centers · Host static assets in CDN · Scale your data tier by sharding · Split tiers into individual services · Monitor your system and use automation tools

Aplicando ao projeto, **na ordem em que faria sentido**:

| Passo [SDI] | Situação atual | O que seria necessário |
|---|---|---|
| **Camada web sem estado** (*stateless web tier*) | ✅ Já é: nenhuma informação fica no processo entre requisições | Nada. É o que permite os próximos passos. |
| **Escalar horizontalmente** + *load balancer* | Um processo uvicorn | Várias réplicas atrás de um balanceador. Possível justamente porque o serviço não guarda estado. |
| **Cache** | Nenhum | Categorias e modalidades quase nunca mudam: são candidatas naturais a cache |
| **Replicação do banco** (escrita no primário, leitura nas réplicas) | Um MySQL | As listagens (maioria das rotas) poderiam ler de réplicas |
| **Separar em serviços** | Um quantum | Último recurso; traz os problemas de dados distribuídos da seção 6.2 |

O [SDI] também diferencia **escalar verticalmente** (máquina maior; simples, mas com teto e ponto único de falha) de **horizontalmente** (mais máquinas). Para o volume atual, a vertical basta.

---

## 9. Riscos e limitações conhecidos

| Risco | Impacto | Mitigação proposta |
|---|---|---|
| Autenticação provisória | Alto: qualquer um age como qualquer usuário; o catálogo pode ser alterado por qualquer cliente | JWT (ADR 6); restringir escritas do catálogo a administradores e ao scraper |
| Unicidade só no código | Médio: duplicatas sob concorrência | Constraints `UNIQUE` em `titulo` e `url_original` (exige migration) |
| Banco compartilhado sem dono definido do schema | Médio: alterações de schema descoordenadas | Definir qual serviço aplica migrations (o Alembic está instalado, mas não configurado) |
| Sem paginação | Médio: `GET /oportunidade` devolve tudo | `limit`/`offset` e filtros por query param |
| Sem testes automatizados | Médio: regressões só são pegas manualmente | Transformar os [exemplos JSON](scripts/exemplos/) em suíte pytest |

---

## 10. Governança: *fitness functions*

O [FSA] (cap. 6) define **fitness functions** como mecanismos objetivos que verificam se uma característica arquitetural continua sendo atendida, de forma automatizada, a cada mudança. Funções que fariam sentido aqui:

| Fitness function | Protege | Como verificar |
|---|---|---|
| Services não importam `fastapi` nem `sqlalchemy` | Isolamento das camadas (ADR 2) | `grep -n "fastapi\|sqlalchemy" src/modules/*/service.py` deve retornar vazio |
| Controllers não importam repositories | Camadas fechadas (ADR 1) | `grep -n "repository" src/modules/*/controller.py` deve retornar vazio |
| Todos os exemplos da API passam | Comportamento esperado | Executar os casos de [scripts/exemplos/](scripts/exemplos/) contra o `TestClient` |
| Operações multi-tabela são atômicas | Integridade (ADR 3) | Teste que força falha no segundo passo e confere que nada mudou |

Hoje essas verificações são feitas manualmente. O próximo passo natural é transformá-las em testes do pytest, para rodarem a cada mudança.

---

## 11. Como rodar

Da raiz do projeto, com a `DATABASE_URL` definida no `.env`:

```bash
uv run python scripts/seed.py --reset                       # popula o SQLite local
uv run uvicorn app.main:app --app-dir src --reload          # sobe a API
```

A documentação interativa fica em `http://127.0.0.1:8000/docs`.
