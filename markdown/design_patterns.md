# Padrões de projeto do Opportunities Service

Este documento explica os padrões usados no código: o que cada um resolve, como foi implementado aqui e qual é o seu custo. A visão de arquitetura (estilo, dados, decisões) está em [arquitetura.md](arquitetura.md).

As referências seguem as mesmas siglas:

| Sigla | Livro |
|---|---|
| **[FSA]** | Richards e Ford, *Fundamentals of Software Architecture* (2020) |
| **[HP]** | Ford, Richards, Sadalage e Dehghani, *Software Architecture: The Hard Parts* (2021) |
| **[SDI]** | Alex Xu, *System Design Interview: An Insider's Guide* |

Os livros tratam de arquitetura, não de catálogos de padrões de código. Por isso, cada padrão abaixo é ligado ao **problema arquitetural** que ele resolve, no vocabulário dos livros: acoplamento, contratos, transações, isolamento de camadas.

---

## Visão geral

| Padrão | Onde está | Resolve |
|---|---|---|
| [Camadas fechadas](#1-camadas-fechadas) | estrutura de cada módulo | Mudanças numa camada não se espalham |
| [Injeção de dependência](#2-injeção-de-dependência-e-composition-root) | `Depends` nos controllers, [main.py](src/app/main.py) | Ninguém cria as próprias dependências |
| [DTO](#3-dto-o-contrato-da-api) | `dto.py` de cada módulo | Separa o contrato da API da estrutura da tabela |
| [Service Layer](#4-service-layer) | `service.py` de cada módulo | Um lugar para cada regra de negócio |
| [Repository genérico](#5-repository-genérico) | [modules/repository.py](src/modules/repository.py) | Isola o SQL e evita CRUD repetido |
| [Unit of Work](#6-unit-of-work) | [db/transaction.py](src/db/transaction.py) | Operações de várias tabelas são atômicas |
| [Exceções de domínio](#7-exceções-de-domínio-e-tradução-num-único-ponto) | [modules/exceptions.py](src/modules/exceptions.py) | Regras sem depender de HTTP nem de ORM |

---

## 1. Camadas fechadas

**Problema.** Se o controller pudesse falar direto com o banco e o service soubesse de status HTTP, qualquer mudança (trocar o framework, o ORM ou o banco) se espalharia pelo projeto inteiro.

**Padrão.** O [FSA] (cap. 10) descreve camadas **fechadas**: uma requisição não pode pular camadas. O benefício é o que o livro chama de **layers of isolation**: mudanças numa camada não afetam as outras, desde que o contrato entre elas se mantenha.

```
controller  →  service  →  repository  →  banco
 (HTTP)        (regras)    (SQL)
```

**Neste projeto.** Cada camada só conhece a de baixo:
- O controller recebe o service pronto e repassa a chamada.
- O service usa os repositories pela `Transaction`.
- O repository usa a `Session` do SQLAlchemy.

**Custo.** O [FSA] alerta para o **architecture sinkhole**: requisições que só atravessam as camadas, sem lógica. Aqui, cerca de 10 das 23 rotas são assim, quase todas leituras. A análise completa está na seção 4.3 do [arquitetura.md](arquitetura.md).

---

## 2. Injeção de dependência e *composition root*

**Problema.** Se um service criasse o próprio repository (`self.repo = CategoriaRepository(Session())`), seria impossível testá-lo sem banco, e cada um poderia acabar com uma sessão diferente.

**Padrão.** Cada componente **recebe** as dependências prontas, de fora. O lugar que monta tudo é a *composition root*.

**Neste projeto.** O FastAPI monta a cadeia a cada requisição:

```python
# controller.py
def get_categoria_service(transaction: Annotated[Transaction, Depends(get_transaction)]) -> CategoriaService:
    return CategoriaService(transaction)
```

```
get_session()        → abre a Session da requisição
  └ get_transaction()  → Transaction(session), que cria os repositories
      └ get_categoria_service() → CategoriaService(transaction)
          └ a rota recebe o service pronto
```

O [main.py](src/app/main.py) é a *composition root* da aplicação: o único arquivo que conhece todas as peças (routers, handlers de erro, ciclo de vida).

**Prova de que funciona.** O [scripts/seed.py](scripts/seed.py) usa os mesmos services **sem HTTP**, montando a dependência à mão: `CategoriaService(Transaction(session))`.

**Custo.** Mais indireção. Para entender de onde vem um objeto, é preciso seguir a cadeia de `Depends`.

---

## 3. DTO: o contrato da API

**Problema.** Se a API devolvesse os models diretamente, qualquer coluna nova no banco apareceria na resposta, e mudar a resposta exigiria mudar a tabela.

**Padrão.** *Data Transfer Objects*: classes que definem **o que entra e o que sai** da API, independentemente de como os dados são guardados.

**Neste projeto.** Cada módulo tem dois DTOs Pydantic:
- `*DTORequest` valida a entrada. Com `extra="forbid"`, ele funciona como **lista branca**: é isso que impede, por exemplo, mandar `usuario_id` no corpo para favoritar em nome de outra pessoa.
- `*DTOResponse` formata a saída e é criado a partir do model (`from_attributes=True`).

### Contratos estritos e soltos

O [HP] (cap. 13) descreve um espectro de contratos:
- **estritos**, que exigem nomes, tipos e formato exatos;
- **soltos**, mais tolerantes a variações.

O livro alerta que contratos estritos tornam integrações **frágeis**: toda mudança quebra quem os consome.

Aqui há um equilíbrio deliberado:

| Lado | Rigor | Por quê |
|---|---|---|
| **Entrada** (`DTORequest`) | Estrito: tipos, tamanhos e `extra="forbid"` | É validação. Rejeitar o inesperado protege as regras de negócio. |
| **Saída** (`DTOResponse`) | Aditivo: campos novos podem ser incluídos | Acrescentar um campo não quebra clientes que o ignoram |

### *Stamp coupling*

O [HP] (cap. 13) chama de **stamp coupling** passar uma estrutura de dados inteira quando o consumidor usa só parte dela. O livro trata isso como anti-padrão quando acontece por excesso de especificação.

O `FavoritosDTOResponse` embute o `OportunidadeDTOResponse` **completo**. É *stamp coupling*, mas **intencional**: o frontend precisa dos dados da vaga para exibir a lista de favoritos, e mandá-los junto evita uma requisição por favorito. O custo é que qualquer mudança no DTO de oportunidade também muda a resposta de favoritos.

---

## 4. Service Layer

**Problema.** Regras de negócio ("o título não pode repetir", "o favorito precisa de uma vaga existente") precisam de um lugar só. Espalhadas pelos controllers, seriam duplicadas e esquecidas.

**Padrão.** Uma camada de serviço em que **cada método é um caso de uso**. A lógica fica no service (estilo *transaction script*), e os models são apenas dados.

**Neste projeto.** Cada caso de uso segue o mesmo roteiro:

```python
def atualizar(self, categoria_id: int, dados: CategoriaDTORequest) -> CategoriaDTOResponse:
    categoria = self.transaction.categorias.get_or_raise(categoria_id)   # 1. carregar (ou 404)

    existente = self.transaction.categorias.get_by_title(dados.titulo)   # 2. aplicar as regras
    if existente is not None and existente.categoria_id != categoria_id:
        raise ConflitoError("Já existe uma categoria com esse título")

    with self.transaction:                                               # 3. gravar de forma atômica
        categoria = self.transaction.categorias.update(categoria, dados.model_dump())

    return CategoriaDTOResponse.model_validate(categoria)                # 4. devolver um DTO
```

**Por que models sem lógica.** Para uma API majoritariamente CRUD, colocar comportamento nos models (o chamado modelo de domínio rico) acrescentaria complexidade sem ganho. O [FSA] lembra que não existe "a melhor" escolha, só a adequada ao contexto. Se o domínio ganhar regras complexas, essa decisão deve ser revista.

**Custo.** `CategoriaService` e `ModalidadeService` são quase idênticos. A tentação é criar um "service genérico", mas, com só dois casos, a abstração custaria mais do que a repetição.

---

## 5. Repository genérico

**Problema.** Sem uma camada de acesso a dados, o SQL ficaria misturado às regras. Escrito por entidade, o mesmo CRUD seria repetido quatro vezes.

**Padrão.** O **Repository** esconde *como* os dados são buscados e gravados atrás de métodos com nomes de negócio. A versão **genérica** implementa o CRUD uma vez e o reaproveita.

**Neste projeto.** A [BaseRepository](src/modules/repository.py) é genérica no tipo do model:

```python
class BaseRepository[Model: Base]:
    model: type[Model]
    nao_encontrado: str = "Registro não encontrado"

    def get_or_raise(self, id: int) -> Model: ...
    def insert(self, obj: Model) -> Model: ...
    def update(self, obj: Model, valores: dict[str, Any]) -> Model: ...
    def delete(self, obj: Model) -> None: ...
```

Cada repository concreto só declara o model e acrescenta o que é específico dele:

```python
class CategoriaRepository(BaseRepository[Categoria]):
    model = Categoria
    nao_encontrado = "Categoria não encontrada"

    def get_by_title(self, titulo: str) -> Categoria | None: ...
```

Detalhes que valem atenção:
- **`[Categoria]` na herança** faz o editor saber que `get_by_id` retorna `Categoria | None`.
- **O `update` recusa campos inexistentes.** Sem isso, um `setattr` com nome errado cria um atributo comum, que **não é salvo e não dá erro**. Em termos do [FSA] (cap. 3), isso transforma um erro silencioso de conascência de nome em uma falha imediata.
- **Os métodos de escrita fazem `flush`, nunca `commit`.** Quem decide gravar é a Unit of Work (próxima seção).
- **Operações em lote viram um único comando.** O `delete_by_oportunidade` em [favoritos/repository.py](src/modules/favoritos/repository.py) apaga todos os favoritos de uma vaga com um único `DELETE`, em vez de um por favorito.

**Custo.** O [HP] (cap. 8) alerta que código compartilhado cria acoplamento: mudar a `BaseRepository` afeta todos os módulos. Ela deve ficar pequena e estável, e o que for específico deve ficar no repository concreto.

---

## 6. Unit of Work

Esta é a seção mais detalhada, porque é o padrão menos intuitivo do projeto.

### 6.1 O problema

A operação "apagar uma oportunidade" tem dois passos, porque a tabela `favoritos` aponta para `oportunidade`:

1. apagar os favoritos da vaga;
2. apagar a vaga.

Se cada repository confirmasse a própria escrita (`commit`), uma falha no passo 2 deixaria o banco num estado impossível: favoritos apagados e a vaga ainda lá. E sem como desfazer.

### 6.2 O conceito: transação ACID

O [HP] (cap. 9) define a transação **ACID** como uma única unidade de trabalho em que várias alterações são confirmadas juntas ou desfeitas juntas. A propriedade que importa aqui é a **atomicidade**: ou tudo é aplicado, ou nada.

No SQLAlchemy, duas operações são frequentemente confundidas:

| | `flush()` | `commit()` |
|---|---|---|
| Envia o SQL ao banco? | Sim | Sim |
| Confirma a transação? | **Não** | **Sim** |
| Pode ser desfeito depois? | Sim, com `rollback` | Não |

### 6.3 O padrão

O **Unit of Work** separa as responsabilidades:

| Quem | Faz o quê |
|---|---|
| **Repository** | Executa o SQL com `flush`, sem confirmar |
| **Unit of Work** | Decide o destino da transação inteira: `commit` ou `rollback` |
| **Service** | Diz **onde** a transação começa e termina, porque conhece o caso de uso |

### 6.4 A implementação: [db/transaction.py](src/db/transaction.py)

**Os repositories nascem dentro da `Transaction`:**

```python
class Transaction:
    def __init__(self, session: Session):
        self.session = session
        self.categorias = CategoriaRepository(session)
        self.modalidades = ModalidadeRepository(session)
        self.oportunidades = OportunidadeRepository(session)
        self.favoritos = FavoritosRepository(session)
```

A transação pertence à **sessão**, e um `commit` só confirma o que foi feito naquela sessão. Se um repository fosse criado com outra sessão, o trabalho dele ficaria fora da transação, **sem nenhum erro**. Criando todos aqui, esse bug fica impossível.

**O protocolo `with` decide entre commit e rollback.** Qualquer objeto com `__enter__` e `__exit__` pode ser usado num `with`, e o Python garante que o `__exit__` **sempre** roda, informando se houve exceção:

```python
def __exit__(self, exception_type, exception, traceback_type) -> None:
    if exception_type is not None:                      # houve erro dentro do bloco
        self.session.rollback()
        if isinstance(exception, IntegrityError):       # traduz o erro do ORM
            raise IntegridadeError("A operação viola uma restrição do banco") from exception
        return                                          # deixa a exceção original seguir

    try:
        self.session.commit()                           # tudo certo: grava
    except IntegrityError as erro:
        self.session.rollback()
        raise IntegridadeError("A operação viola uma restrição do banco") from erro
```

| Caminho | Situação | Resultado |
|---|---|---|
| A | O bloco terminou sem erro | `commit` |
| B | Exceção dentro do bloco | `rollback`, e a exceção continua subindo |
| C | O próprio `commit` falhou | `rollback`, e a exceção continua subindo |

Três detalhes importantes:
- **A ordem dos parâmetros do `__exit__` é fixa:** `(tipo, exceção, traceback)`. O Python passa por posição. Invertê-los já causou um bug neste projeto: a tradução do `IntegrityError` nunca acontecia, e os 409 viravam 500.
- **Retornar `None` deixa a exceção continuar.** Se o `__exit__` retornasse `True`, o erro seria engolido, e o service acharia que deu tudo certo.
- **`raise ... from exception`** guarda o erro original em `__cause__`, então nada se perde nos logs.

**Por que os repositories fazem `flush`.** Sem ele, o SQL só rodaria no `commit`, ou seja, depois do bloco. Um erro de FK apareceria longe da causa, e valores gerados pelo banco (o `id`, o `data_criacao`) não estariam disponíveis dentro do bloco.

### 6.5 Uso no projeto

```python
def deletar(self, oportunidade_id: int) -> None:
    oportunidade = self.transaction.oportunidades.get_or_raise(oportunidade_id)   # leitura: fora do bloco

    with self.transaction:                                                        # escrita: dentro
        self.transaction.favoritos.delete_by_oportunidade(oportunidade_id)
        self.transaction.oportunidades.delete(oportunidade)
```

Isso foi verificado forçando uma falha no segundo passo: os favoritos **voltaram**.

### 6.6 Armadilhas (todas reproduzidas neste projeto)

| Armadilha | O que acontece | Regra |
|---|---|---|
| Escrever **fora** do `with` | Nada é gravado; a sessão fecha e descarta a transação, mas a API responde com sucesso | Toda escrita dentro de `with self.transaction:` |
| **Engolir** uma exceção de domínio dentro do bloco | O `__exit__` não vê erro e faz `commit` do que foi feito até ali | Capture exceções **fora** do `with` |
| Engolir um erro do **banco** dentro do bloco | O SQLAlchemy marca a sessão como inválida, e o `commit` lança `PendingRollbackError` (vira 500) | Idem |
| **Aninhar** blocos `with` da mesma transação | O bloco interno faz `commit` ao terminar; o externo não consegue mais desfazer | Um caso de uso, um bloco. Se um service chamar outro, só o mais externo abre o `with`. |

### 6.7 O limite do padrão

A Unit of Work funciona porque tudo está **num único banco**, o que garante a transação ACID. O [HP] (caps. 9 a 12) mostra que, quando os dados ficam em **serviços diferentes**, não existe um `commit` comum. Aí entram as **transações distribuídas** e as **sagas**: sequências de passos com ações de compensação para desfazer o que já foi feito, ao custo de consistência eventual.

Se um dia `favoritos` virar um serviço separado, o `deletar` acima deixará de ser atômico e precisará de uma dessas técnicas. É um dos motivos para manter o projeto como um único quantum por enquanto (ADR 1 em [arquitetura.md](arquitetura.md)).

### 6.8 Custo

A `Transaction` conhece os repositories de **todos** os módulos, ou seja, tem acoplamento eferente alto. Todo módulo novo exige alterá-la. É uma troca consciente: em troca, a regra "todos usam a mesma sessão" deixa de depender de disciplina.

---

## 7. Exceções de domínio e tradução num único ponto

**Problema.** Services que lançam `HTTPException` só funcionam dentro de uma requisição HTTP. Services que capturam `IntegrityError` dependem do SQLAlchemy.

**Padrão.** Cada camada fala a **sua** linguagem de erros, e a tradução acontece nas fronteiras:

```
SQLAlchemy             Domínio                   HTTP
IntegrityError  ──►  IntegridadeError    ─┐
                     NaoEncontradoError   ├──►  main.py  ──►  404 / 409 / 422
                     ConflitoError        │
                     ReferenciaInvalida.. ┘
   (Transaction)        (services)              (handler único)
```

**Neste projeto:**
1. A `Transaction` traduz `IntegrityError` → `IntegridadeError`.
2. O service, que sabe o **motivo**, converte para um erro com significado de negócio: na exclusão de uma categoria em uso, `IntegridadeError` → `ConflitoError("Categoria possui oportunidades vinculadas...")`.
3. O [main.py](src/app/main.py) traduz para HTTP num único mapa:

```python
STATUS_CODE_ERRO = {
    NaoEncontradoError: 404,
    ConflitoError: 409,
    IntegridadeError: 409,
    ReferenciaInvalidaError: 422,
}
```

**Benefício.** Os services não importam nada de `fastapi` nem de `sqlalchemy`. É isso que permite ao [seed](scripts/seed.py) tratar um `ConflitoError` como qualquer exceção Python, para não duplicar dados.

**Custo.** Um nível de indireção a mais, e um tipo de erro novo exige três passos: criar a exceção, lançá-la e mapeá-la.

---

## 8. Anti-padrões a evitar

| Anti-padrão | Fonte | Como aparece (ou apareceria) aqui |
|---|---|---|
| **Architecture sinkhole** | [FSA] cap. 10 | Rotas que só repassam chamadas. Hoje entre 40 e 50%; acompanhar para não chegar perto de 80%. |
| **Biblioteca única de entidades** | [FSA] cap. 13 | Todos os módulos importando os models uns dos outros. Hoje só `favoritos` importa de `oportunidade`. |
| **Contrato excessivamente estrito** | [HP] cap. 13 | Exigir campos de saída que o cliente não usa, ou quebrar clientes a cada campo novo. |
| **Stamp coupling acidental** | [HP] cap. 13 | Embutir estruturas inteiras sem necessidade. O de favoritos é intencional (seção 3). |
| **Transação distribuída disfarçada** | [HP] cap. 9 | Chamar outro serviço por HTTP dentro de um `with self.transaction:`; o rollback não desfaria a chamada remota. |
| **Estado no processo** | [SDI] cap. 1 | Guardar dados entre requisições em variáveis globais. Impediria ter várias réplicas. Hoje o serviço é *stateless*. |

---

## Para se aprofundar

- [FSA] cap. 3 (modularidade e conascência), cap. 10 (camadas) e cap. 19 (ADRs)
- [HP] cap. 9 (posse de dados e transações), cap. 12 (sagas) e cap. 13 (contratos)
- [SDI] cap. 1 (escalar de zero a milhões de usuários)
- Harry Percival e Bob Gregory, *Architecture Patterns with Python*, cap. 6 (Unit of Work), disponível em [cosmicpython.com](https://www.cosmicpython.com/book/chapter_06_uow.html)
