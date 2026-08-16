# 🚀 Kafka Mission Control

Aplicação full-stack para acompanhar, em tempo real, o processamento assíncrono de missões.

A API responde `201` imediatamente após publicar o evento no Kafka, sem esperar o processamento. Um worker independente consome esse evento, simula o trabalho e publica as mudanças de status de volta. O dashboard reflete a missão caminhando por `CREATED → PROCESSING → COMPLETED` em cerca de 5 segundos.

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.12 + FastAPI, Clean Architecture em 3 camadas |
| Mensageria | Apache Kafka (tópicos `missions` e `mission-status`) |
| Worker | Processo Python independente |
| Frontend | Angular 14, login JWT e dashboard com polling |

## Credenciais

| Campo | Valor |
|---|---|
| Usuário | `admin` |
| Senha | `mudar@123` |

Credenciais fixas no código, adequadas ao escopo de POC. Qualquer outro par retorna HTTP 401.

## Subindo com Docker

Caminho recomendado: sobe Kafka, API, worker e frontend integrados, com um comando.

```bash
cp .env.example .env    # opcional, ajuste o JWT_SECRET
docker compose up --build -d
```

Acesse <http://localhost:4200> e faça login. O primeiro build leva alguns minutos, por causa do `npm ci` e do build de produção do Angular.

| Serviço | Porta no host | Descrição |
|---|---|---|
| `frontend` | 4200 | nginx servindo o build do Angular e fazendo proxy da API |
| `api` | 8000 | FastAPI, com docs em `/docs` |
| `worker` | — | consome `missions` e publica em `mission-status` |
| `kafka` | 29092 | broker em modo KRaft, exposto ao host |

O `frontend` faz proxy de `/auth` e `/missions` para a API na mesma origem, então o navegador usa apenas a porta 4200 e não há CORS envolvido. A porta 8000 fica publicada só para inspecionar a API direto.

Comandos úteis:

```bash
docker compose logs -f worker    # acompanha o processamento
docker compose ps                # estado e saúde dos serviços
docker compose down              # derruba a stack
docker compose down -v           # derruba e apaga os dados do Kafka
```

Um serviço `kafka-init` cria os tópicos e encerra. A API e o worker só iniciam depois que ele conclui, então não há corrida na primeira subida nem dependência de criação automática de tópicos.

Para escalar o worker e ver o consumer group dividindo a carga, aumente as partições de `missions` e rode:

```bash
docker compose up -d --scale worker=2
```

## Rodando sem Docker

Útil para desenvolver com reload. Pré-requisitos:

- Docker (apenas para o Kafka)
- Python 3.12+
- Node.js 16+ e npm (Angular 14)

São três processos, um por terminal: API, worker e frontend. O Kafka vem do compose.

### 1. Subir o Kafka e criar os tópicos

Reaproveita o compose, subindo apenas os dois serviços de infraestrutura:

```bash
docker compose up -d kafka kafka-init
```

O broker fica acessível do host em `localhost:29092`, e o `kafka-init` cria os tópicos `missions` e `mission-status`. Para conferir:

```bash
docker compose exec kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:29092 --list
```

Como o endereço no host difere do default, exporte a variável nos terminais da API e do worker:

```bash
export KAFKA_BOOTSTRAP_SERVERS=localhost:29092
```

### 2. Subir a API

A virtualenv não é versionada, então crie na primeira vez:

```bash
cd backend

# apenas na primeira execução
python3 -m venv venv
venv/bin/pip install -r requirements.txt

venv/bin/uvicorn app.main:app --reload --port 8000
```

A API sobe em <http://localhost:8000>, com documentação interativa em <http://localhost:8000/docs>. No startup ela também inicia o `KafkaStatusConsumer` numa thread de background, que consome `mission-status` e aplica as transições de status no repositório.

Teste rápido:

```bash
curl -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"mudar@123"}'
```

### 3. Subir o worker

Em outro terminal, na mesma virtualenv e a partir de `backend/`, para o pacote `worker` resolver:

```bash
cd backend
venv/bin/python -m worker.main
```

O worker entra no consumer group `mission-workers` no tópico `missions`. Para cada evento `mission.created` ele aguarda 2s e publica `PROCESSING`, depois aguarda 3s e publica `COMPLETED`, ambos em `mission-status`.

### 4. Subir o frontend

```bash
cd frontend
npm install        # apenas na primeira execução
npm start
```

Acesse <http://localhost:4200>, faça login e crie uma missão. O dashboard consulta `GET /missions` a cada segundo, então o card percorre `CREATED → PROCESSING → COMPLETED` em cerca de 5 segundos.

A URL da API fica em `frontend/src/environments/environment.ts`.

## Configuração

O backend lê as variáveis abaixo, com defaults voltados ao desenvolvimento local. Veja `backend/.env.example`.

| Variável | Default | Descrição |
|---|---|---|
| `JWT_SECRET` | `dev-only-insecure-secret` | Segredo HS256 que assina os tokens |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Endereço do broker, usado pela API e pelo worker |

O default do `JWT_SECRET` existe para a POC rodar sem configuração. Fora do ambiente local, defina um valor forte:

```bash
export JWT_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
```

## Testes

O backend usa pytest. O Kafka **não** é necessário: os testes de integração usam fakes em memória, então a suíte roda em menos de um segundo, sem Docker.

```bash
cd backend
venv/bin/python -m pytest
```

São 11 testes, cobrindo o ciclo de vida completo da missão (publicação → worker → status consumer → repositório) e as regras de arquitetura. Sendo uma POC, a suíte é deliberadamente enxuta e prioriza o fluxo ponta a ponta em vez de cobertura por unidade.

O `test_architecture.py` percorre a AST de todos os imports em `app/` e falha se alguma camada interna importar FastAPI, Kafka ou PyJWT. A regra quebra a build em vez de depender de revisão manual.

O frontend tem o Karma configurado, mas nenhum `*.spec.ts` foi escrito, então `npm test` reporta zero specs.

## API

| Método | Endpoint | Auth | Sucesso | Erros |
|---|---|---|---|---|
| POST | `/auth/login` | — | 200 | 401, 422 |
| POST | `/missions` | JWT | 201 | 401, 403, 422 |
| GET | `/missions` | JWT | 200 | 401, 403 |
| GET | `/missions/{mission_id}` | JWT | 200 | 401, 403, 404 |

Token ausente resulta em 403 e token inválido ou expirado em 401, seguindo o comportamento padrão do `HTTPBearer` do FastAPI. Tokens são HS256 e expiram em 60 minutos. Ao criar uma missão, `name` tem entre 2 e 100 caracteres e `priority` aceita `LOW`, `MEDIUM` ou `HIGH`.

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"mudar@123"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

curl -X POST http://localhost:8000/missions \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Apollo 11","priority":"HIGH"}'
```

## Arquitetura

```text
                          ┌───────────────────────┐
                          │      Angular 14       │
                          │  Login · Dashboard    │
                          │  AuthGuard            │
                          │  JWTInterceptor       │
                          └───────────┬───────────┘
                                      │
                         HTTP + Bearer JWT
                         POST /missions
                         GET  /missions (poll 1s)
                                      │
                                      ▼
                    ┌─────────────────────────────────┐
                    │            FastAPI              │
                    │                                 │
                    │  Presentation                   │
                    │   rotas · DTOs HTTP · JWT dep   │
                    │            ↓ (DI)               │
                    │  Application                    │
                    │   use cases · ports · domain    │
                    │            ↑ implementa         │
                    │  Infrastructure                 │
                    │   KafkaEventPublisher           │
                    │   KafkaStatusConsumer           │
                    │   InMemoryMissionRepository     │
                    │   JWTService                    │
                    └───────┬─────────────────▲───────┘
                            │                 │
              publica       │                 │  consome
              mission.created                 │  eventos de status
                            │                 │
                            ▼                 │
                   ┌────────────────┐  ┌──────────────────┐
                   │ tópico Kafka   │  │ tópico Kafka     │
                   │   missions     │  │  mission-status  │
                   └────────┬───────┘  └──────────▲───────┘
                            │                     │
              consome       │                     │  publica
              grupo:        │                     │  PROCESSING (após 2s)
              mission-workers                     │  COMPLETED  (após 3s)
                            │                     │
                            ▼                     │
                   ┌─────────────────────────────────┐
                   │     Worker (processo próprio)    │
                   │        backend/worker/main.py    │
                   └─────────────────────────────────┘
```

### Ciclo de vida da missão

```text
CREATED ──► PROCESSING ──► COMPLETED
     │             └──────► FAILED
     └────────────────────► FAILED
```

Qualquer outra transição (por exemplo `COMPLETED → PROCESSING`) levanta `InvalidTransitionError` e deixa a missão intacta.

### Fluxo de uma missão

1. O Angular envia `POST /missions` com o Bearer token anexado pelo `JWTInterceptor`.
2. A dependency de JWT valida o token e o Pydantic valida o DTO.
3. `CreateMission` monta a `Mission` com status `CREATED`, salva pelo `MissionRepository` e publica `mission.created` no tópico `missions` via `EventPublisher`.
4. A API responde `201` na hora, o processamento é totalmente desacoplado.
5. O worker consome o evento, aguarda 2s e publica `PROCESSING`, aguarda 3s e publica `COMPLETED` em `mission-status`.
6. O `KafkaStatusConsumer` dentro da API consome esses eventos e dirige a máquina de estados do domínio.
7. O polling de 1s do dashboard exibe o novo status.

## Estrutura

```text
backend/
├── app/
│   ├── domain/                     # entidade Mission, enums, máquina de estados
│   ├── application/
│   │   ├── ports/                  # protocolos MissionRepository, EventPublisher, TokenService
│   │   ├── schemas/events.py       # modelos dos eventos Kafka
│   │   └── use_cases/              # AuthenticateUser, CreateMission, GetMission, ListMissions
│   ├── infrastructure/
│   │   ├── kafka/                  # producer.py, consumer.py
│   │   ├── repositories/           # in_memory_mission_repository.py
│   │   └── security/               # jwt_service.py
│   ├── presentation/
│   │   ├── api/                    # auth.py, missions.py
│   │   ├── schemas/                # DTOs de request/response
│   │   ├── auth_dependency.py      # validação do Bearer token
│   │   └── dependencies.py         # composition root / factories de DI
│   └── main.py                     # app FastAPI + lifespan do consumer
├── worker/main.py                  # processo worker independente
├── tests/                          # integration/ + test_architecture.py
├── Dockerfile                      # imagem compartilhada pela API e pelo worker
└── requirements.txt

frontend/
├── src/app/
│   ├── components/                 # login, dashboard, mission-list, mission-card, mission-create-form
│   ├── guards/auth.guard.ts
│   ├── interceptors/jwt.interceptor.ts
│   └── services/                   # auth.service.ts, mission.service.ts, models/
├── Dockerfile                      # build multi-stage: node -> nginx
└── nginx.conf                      # serving do SPA + proxy da API

docker-compose.yml                  # kafka, kafka-init, api, worker, frontend
```

## Decisões de arquitetura

**Três camadas, dependências apontando para dentro.** `domain/` e `application/` nunca importam FastAPI, Kafka ou PyJWT. A infraestrutura implementa as abstrações declaradas pela camada de aplicação, e `test_architecture.py` transforma essa regra em teste automatizado.

**Ports como `typing.Protocol` em vez de ABCs.** A tipagem estrutural mantém as classes de infraestrutura livres de herança das camadas internas: `InMemoryMissionRepository` e `KafkaEventPublisher` apenas satisfazem o formato esperado. O trade-off é que a conformidade é verificada estaticamente, não em tempo de import, o que os testes cobrem.

**Um único composition root.** `dependencies.py` instancia repositório, serviço de JWT e publisher como singletons de módulo e expõe factories via `Depends()`. Nenhuma rota constrói use case ou fala com Kafka diretamente, então trocar `KafkaEventPublisher` por um fake nos testes é um override de uma linha.

**Modelos distintos por fronteira.** DTOs de request, de response, eventos Kafka e a entidade de domínio são classes separadas. Um modelo único vazaria preocupações de transporte para o domínio e deixaria o formato de rede preso a refatorações internas.

**Máquina de estados na entidade.** `Mission.transition_to` é dona das transições válidas e levanta `InvalidTransitionError`. Como a regra vive no domínio, a mesma guarda protege o caminho HTTP e o caminho do consumer Kafka, sem duplicação.

**Kafka para desacoplamento real.** A API publica e retorna `201` sem esperar o processamento. Se a publicação falhar, a missão continua persistida em `CREATED`: a disponibilidade da escrita é priorizada sobre a entrega do evento, e a ausência do worker nunca quebra a criação. Dois tópicos mantêm os fluxos unidirecionais.

**Worker como processo separado do SO.** Tem entry point próprio e consumer group `mission-workers`, então escalar é rodar o comando duas vezes. Mensagens malformadas são logadas e descartadas, o loop de consumo não morre por um evento ruim.

**Status consumer em thread de background.** O `KafkaStatusConsumer` sobe e desce junto com o lifespan do FastAPI, como daemon thread. O `confluent-kafka` é um cliente blocante, e a thread mantém o event loop responsivo sem trazer um driver Kafka assíncrono.

**Repositório em memória.** Escolha deliberada: o exercício mira arquitetura, não persistência. O armazenamento fica atrás de `MissionRepository`, então uma implementação com banco seria uma nova classe de infraestrutura e uma linha no composition root. Os dados são perdidos quando a API reinicia.

**Polling em vez de WebSockets.** Um `GET /missions` por segundo basta nessa escala e mantém o frontend simples. Erros de polling são engolidos e reprocessados no tick seguinte, então uma instabilidade breve da API não limpa o dashboard.

**Frontend sem host fixo na imagem.** O `apiUrl` do build de produção é vazio e o nginx faz proxy de `/auth` e `/missions` para a API. Como o Angular resolve tudo em caminho relativo, a mesma imagem roda em localhost, num EC2 ou atrás de um domínio, sem rebuild e sem CORS. Fixar a URL no bundle exigiria uma imagem por ambiente.

**API e worker na mesma imagem.** É o mesmo código com entry points distintos, então o worker apenas sobrescreve o `command`. Uma imagem a menos para versionar, e o build não sai de sincronia entre os dois.

**Tópicos criados por um serviço dedicado.** O `kafka-init` roda, cria os tópicos e sai. API e worker usam `service_completed_successfully`, o que torna a subida determinística em vez de depender de auto-criação, que geraria tópicos com o número errado de partições.

## Limitações conhecidas

São conscientes, dado o escopo de POC:

- Dados em memória, perdidos a cada restart da API. Duas instâncias da API não compartilham estado.
- Credenciais fixas no código, sem cadastro de usuários nem refresh token.
- `allow_origins=["*"]` na API. Irrelevante no caminho com Docker, em que o nginx serve tudo na mesma origem, mas deve ser restringido caso a porta 8000 seja exposta publicamente.
- Todo o tráfego é HTTP, sem TLS.
- O status `FAILED` existe no domínio e é respeitado pela máquina de estados, mas o worker atual sempre segue o caminho de sucesso.
- Sem testes no frontend.

## Caminho para AWS

A stack em containers foi pensada para migrar sem reescrita. O que a POC já resolve e o que falta:

**Pronto.** As imagens não carregam configuração fixa: `JWT_SECRET` e `KAFKA_BOOTSTRAP_SERVERS` vêm do ambiente, e o frontend resolve a API por caminho relativo. Rodar num EC2 é clonar o repo, definir o `.env` e executar o mesmo `docker compose up -d`.

**Antes de expor.** Definir um `JWT_SECRET` forte (idealmente via Secrets Manager ou SSM Parameter Store), colocar TLS na frente (ALB com ACM, ou nginx com Certbot), restringir o CORS e não publicar a porta 29092 do Kafka fora da VPC.

**Sobre o S3.** Vale notar que ele não substitui o estado atual: o repositório em memória guarda entidades mutáveis consultadas a cada segundo, o que pede DynamoDB ou RDS, não object storage. Onde o S3 encaixa bem é em servir o build do Angular como site estático (com CloudFront na frente, dispensando o container de frontend) e em arquivar o histórico de eventos das missões. Nesse cenário o proxy do nginx sai de cena e o `apiUrl` volta a apontar para o domínio da API, que passaria a precisar de CORS configurado para a origem do CloudFront.

**Evolução natural.** Trocar o Kafka self-hosted por MSK, o repositório em memória por DynamoDB (uma nova classe de infraestrutura e uma linha no composition root) e o worker por um serviço ECS escalável de forma independente da API.
