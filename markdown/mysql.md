# MySQL no Docker

Um guia rápido para rodar o MySQL deste projeto em um container Docker, explicando o porquê de cada escolha.

> Os nomes e senhas abaixo são **exemplos**. Troque pelos seus e nunca coloque senhas reais em arquivos versionados.

---

## Por que rodar o MySQL no Docker?

Um **container** é um processo isolado que traz junto tudo o que precisa para rodar: o MySQL, as bibliotecas dele e a configuração. A imagem oficial `mysql` já vem pronta. Você não instala nada no seu sistema além do próprio Docker.

| Vantagem | Na prática |
|---|---|
| **Não "suja" o sistema** | Nada de serviço do MySQL rodando sempre, arquivos espalhados ou desinstalação difícil. Apagou o container, sumiu. |
| **Versão fixa** | `mysql:8.0.45` é exatamente a mesma versão em qualquer máquina. Dá para usar a mesma versão do servidor de produção e evitar o "na minha máquina funciona". |
| **Ambiente reproduzível** | Qualquer pessoa sobe o mesmo banco com um comando, em Linux, macOS ou Windows. |
| **Descartável** | Banco corrompido ou cheio de dados de teste? Apague e recrie em segundos. |
| **Vários bancos lado a lado** | Projetos diferentes, ou versões diferentes do MySQL, cada um no seu container e na sua porta, sem conflito. |

**Desvantagens:** o Docker consome memória (o MySQL sozinho usa algumas centenas de MB), exige aprender alguns comandos, e os dados precisam de um **volume** para não se perderem (veja abaixo).

### Docker × SQLite × MySQL instalado

| | SQLite | MySQL no Docker | MySQL instalado no sistema |
|---|---|---|---|
| Configuração | Nenhuma (é um arquivo) | Um comando | Instalação e configuração manuais |
| Fidelidade com produção | Baixa: comporta-se diferente em vários pontos | **Alta**: o mesmo banco e a mesma versão | Alta, se a versão bater |
| Isolamento | Total | Total | Nenhum: fica no sistema |
| Uso ideal | Desenvolvimento rápido | **Testar antes de ir para produção** | Quando o MySQL é usado o tempo todo |

Neste projeto, o SQLite serve para o dia a dia, e o MySQL no Docker serve para testar com o banco real antes de conectar ao servidor compartilhado.

---

## Subindo o container

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

| Trecho | O que faz | Por quê |
|---|---|---|
| `-d` | Roda em segundo plano (*detached*) | Libera o terminal |
| `--name mysql-opportunities` | Dá um nome ao container | Para usar nos outros comandos (`docker stop mysql-opportunities`) em vez de um id aleatório |
| `-p 127.0.0.1:3307:3306` | Liga a porta **3307 do seu computador** à **3306 do container** | **3307** evita conflito com um MySQL já instalado na 3306. O **`127.0.0.1:`** faz o banco aceitar conexões só desta máquina; sem ele, a porta fica aberta para toda a rede. |
| `-v mysql-opportunities-dados:/var/lib/mysql` | Guarda os dados num **volume** com nome | Sem isso, os dados vivem dentro do container e se perdem quando ele é removido (veja abaixo) |
| `MYSQL_ROOT_PASSWORD` | Senha do administrador (`root`) | Obrigatória; o container não sobe sem ela |
| `MYSQL_DATABASE` | Cria um banco vazio com esse nome | Já fica pronto para a aplicação |
| `MYSQL_USER` / `MYSQL_PASSWORD` | Cria um usuário comum, com acesso total a esse banco | A aplicação deve usar este usuário, **não o root**. É o princípio do menor privilégio: se a senha vazar, o estrago fica limitado a um banco. |
| `mysql:8.0.45` | Imagem e versão | Sempre fixe a versão. `mysql:latest` pode mudar de versão sozinha e quebrar o projeto. |

As variáveis `MYSQL_*` só têm efeito **na primeira vez**, quando o volume está vazio. Mudá-las depois não altera senhas nem usuários já criados.

---

## Container × volume: onde ficam os dados

Essa é a parte que mais confunde quem começa:

- O **container** é descartável: pode ser parado, apagado e recriado.
- O **volume** é onde os dados moram de fato (`/var/lib/mysql` dentro do container).

| Ação | Os dados sobrevivem? |
|---|---|
| `docker stop` / `docker start` | ✅ Sim |
| Reiniciar o computador | ✅ Sim (o container só precisa ser iniciado de novo) |
| `docker rm` **com** volume nomeado (`-v nome:/var/lib/mysql`) | ✅ Sim: recrie o container com o mesmo `-v` e tudo volta |
| `docker rm` **sem** volume nomeado | ❌ Na prática, não. O Docker cria um volume anônimo, com um nome aleatório, e um container novo não o reaproveita. |

Volumes anônimos esquecidos se acumulam e ocupam disco. Para ver e limpar:

```bash
docker volume ls          # volumes com nomes enormes e aleatórios são os anônimos
docker volume prune       # remove os que não estão em uso por nenhum container
```

---

## Comandos do dia a dia

```bash
docker ps                                   # containers rodando (e as portas)
docker stop mysql-opportunities             # para o banco
docker start mysql-opportunities            # inicia de novo, com os mesmos dados
docker logs -f mysql-opportunities          # acompanha os logs (útil se não subir)

# Abre o cliente do MySQL dentro do container (pede a senha)
docker exec -it mysql-opportunities mysql -u app -p opportunities_service

# Recomeçar do zero: apaga o container E os dados
docker rm -f mysql-opportunities
docker volume rm mysql-opportunities-dados
```

---

## Conectando a aplicação

No `.env` da raiz do projeto:

```env
DATABASE_URL=mysql+pymysql://app:troque-esta-senha-app@127.0.0.1:3307/opportunities_service
```

| Parte | Significado |
|---|---|
| `mysql+pymysql` | Banco MySQL, usando o driver PyMySQL (já está nas dependências do projeto) |
| `app:troque-esta-senha-app` | Usuário e senha criados no `docker run` |
| `127.0.0.1:3307` | A porta do **seu computador**, não a 3306 de dentro do container |
| `opportunities_service` | O banco criado pelo `MYSQL_DATABASE` |

Se a senha tiver caracteres especiais (`@`, `:`, `/`, `#`), eles precisam ser codificados na URL (por exemplo, `@` vira `%40`). Senão, o SQLAlchemy entende errado onde a senha termina.

---

## Particularidades deste projeto

**1. O banco nasce vazio, e a aplicação não cria as tabelas no MySQL.**
O `lifespan` do [main.py](src/app/main.py) só roda o `create_all` quando o banco é SQLite. Isso é proposital: no servidor real, o schema já existe e é mantido fora deste serviço. Num MySQL novo no Docker, as requisições vão falhar com "Table doesn't exist" até as tabelas serem criadas. Há três caminhos:
- rodar o script SQL do schema (exportado do MySQL Workbench) dentro do container;
- colocar esse script em `/docker-entrypoint-initdb.d/` com um volume; a imagem oficial executa automaticamente os `.sql` dessa pasta **na primeira inicialização**;
- configurar o Alembic (já instalado no projeto) para criar e versionar o schema.

**2. O `seed.py` não popula o MySQL.**
O [scripts/seed.py](scripts/seed.py) recusa de propósito qualquer banco que não seja SQLite, para nunca colocar dados falsos no banco compartilhado. Para um MySQL **local**, essa trava em `preparar_banco` é o único ponto a ajustar.

**3. O MySQL compara textos de forma diferente do SQLite.**
O MySQL 8 usa por padrão a collation `utf8mb4_0900_ai_ci`, que **ignora acentos e maiúsculas**: `'Estágio' = 'estagio'` é verdadeiro. No SQLite, a comparação é exata. Na prática, criar a categoria "estagio" com "Estágio" já cadastrada dá **409 no MySQL**, mas é aceito no SQLite. É um bom motivo para testar no MySQL antes de publicar.

**4. Se aparecer um erro pedindo o pacote `cryptography`.**
O MySQL 8 autentica usuários com o método `caching_sha2_password`. Em algumas situações, o PyMySQL precisa do pacote `cryptography` para completar esse login. Se a conexão falhar com uma mensagem citando `cryptography` ou `caching_sha2_password`, instale:

```bash
uv add cryptography
```

---

## Opcional: Docker Compose

Em vez de decorar o `docker run`, a configuração pode ficar num arquivo `compose.yaml` na raiz do projeto, e as senhas num `.env`, que já está no `.gitignore`:

```yaml
services:
  mysql:
    image: mysql:8.0.45
    container_name: mysql-opportunities
    ports:
      - "127.0.0.1:3307:3306"
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: opportunities_service
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    volumes:
      - mysql-dados:/var/lib/mysql

volumes:
  mysql-dados:
```

```bash
docker compose up -d     # sobe
docker compose down      # para e remove o container (o volume continua)
docker compose down -v   # remove também os dados
```

A vantagem é que a configuração fica **versionada e documentada** junto com o código, e qualquer pessoa sobe o banco com um único comando.
