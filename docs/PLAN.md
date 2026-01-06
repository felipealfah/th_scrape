# Plano de Desenvolvimento - Scrape TH

## 1. Visão Geral do Projeto

**Nome:** Scrape TH API
**Objetivo:** API para automação de login no TubeHunt e extração de dados autenticados
**Caso de Uso Inicial:**
- Acessar https://app.tubehunt.io/login
- Fazer login com credenciais armazenadas em .env (user e password)
- Carregar página autenticada
- Extrair o primeiro `<h1>` da página
- Retornar dados em JSON

**Stack Tecnológico:**
- Backend: FastAPI + Python 3.10+
- Scraping: Selenium WebDriver com Chrome (Headless)
- Automação: Login com credenciais via Selenium
- Containerização: Docker + Docker Compose
- Banco de Dados: (TBD - PostgreSQL/MongoDB)
- Queue: (TBD - Celery/RabbitMQ para tarefas assíncronas)

---

## 2. Fluxo de Trabalho Principal

```
┌─────────────────────────────────────────────────────────────┐
│  Cliente HTTP (GET /api/tubehunt/login-and-scrape)         │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│  FastAPI Route - autenticaçao TubeHunt                      │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│  TubeHuntService                                            │
│  1. Inicializar WebDriver                                  │
│  2. Acessar https://app.tubehunt.io/login                  │
│  3. Preencher credenciais (user, password)                 │
│  4. Submeter formulário                                    │
│  5. Aguardar carregamento de página                        │
│  6. Extrair primeiro <h1>                                  │
│  7. Retornar dados                                         │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│  Resposta JSON                                              │
│  {                                                          │
│    "success": true,                                         │
│    "h1_text": "Bem-vindo ao TubeHunt",                     │
│    "url": "https://app.tubehunt.io/...",                  │
│    "timestamp": "2026-01-01T00:00:00Z"                     │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Arquitetura da Aplicação

### 3.1 Estrutura de Pastas
```
scrape_th/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py           # Endpoints principais
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── tubehunt.py      # Endpoints TubeHunt
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py           # Configurações e .env
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── scrape.py           # Schemas genéricos
│   │   └── tubehunt.py         # Schemas TubeHunt
│   ├── services/
│   │   ├── __init__.py
│   │   ├── scraper.py          # Serviço genérico
│   │   └── tubehunt.py         # Serviço TubeHunt
│   ├── utils/
│   │   ├── __init__.py
│   │   └── logger.py           # Logging
│   ├── __init__.py
│   └── main.py                 # Aplicação FastAPI
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_tubehunt.py
│   └── test_scraper.py
├── docs/
│   ├── PLAN.md                 # Este arquivo
│   ├── TODO.md                 # Tarefas
│   └── ARCHITECTURE.md         # (Futuro)
├── .env                        # Variáveis de ambiente
├── .env.example                # Exemplo
├── docker-compose.yml          # Orquestração
├── Dockerfile                  # Build da imagem
├── pyproject.toml              # Dependências
└── README.md                   # Documentação
```

### 3.2 Arquitetura de Camadas
```
┌─────────────────────────────────────────┐
│      API Layer (FastAPI)                │
│  - Routes TubeHunt                      │
│  - Request/Response Validation          │
└────────────────────┬────────────────────┘
                     │
┌────────────────────▼────────────────────┐
│      Service Layer                      │
│  - TubeHuntService                      │
│  - Business Logic de Login              │
│  - Automação Selenium                   │
└────────────────────┬────────────────────┘
                     │
┌────────────────────▼────────────────────┐
│      Data Layer (Selenium)              │
│  - WebDriver Management                 │
│  - Browser Automation                   │
│  - DOM Navigation                       │
└─────────────────────────────────────────┘
```

---

## 4. Features MVP - Login & Navegação TubeHunt

### 4.1 Autenticação TubeHunt
- [x] Acessar página de login do TubeHunt
- [x] Localizar campo de email/username
- [x] Localizar campo de password
- [x] Preencher credenciais do .env
- [x] Submeter formulário
- [x] Aguardar redirecionamento/carregamento
- [x] Validar sucesso do login
- [x] Extrair elemento H1 da página

### 4.2 Navegação para Página de Vídeos
- [x] Fazer login no TubeHunt
- [x] Navegar para https://app.tubehunt.io/long/?page=1&OrderBy=DateDESC&ChangePerPage=50
- [x] Aguardar carregamento completo da página
- [x] Extrair informações da página (contagem de elementos)
- [x] Validar carregamento com timeout ajustado (120 segundos)

### 4.3 API Endpoints
- [x] `GET /` - Informações gerais
- [x] `GET /api/health` - Health check
- [x] `POST /api/scrape` - Scraping genérico (mantém compatibilidade)
- [x] `POST /api/v1/tubehunt/login-and-scrape` - Login + scrape TubeHunt
- [x] `POST /api/v1/tubehunt/navigate-to-videos` - Login + navegar para vídeos
- [x] `POST /api/v1/tubehunt/scrape-channels` - Login + scrape completo de canais com dados de vídeos (SÍNCRONO)
- [x] `GET /api/v1/tubehunt/health` - Health check completo (status, uptime, serviços)
- [ ] `POST /api/v1/tubehunt/scrape-channels/start` - Inicia job de scraping assíncrono (retorna job_id)
- [ ] `GET /api/v1/tubehunt/scrape-channels/result/{job_id}` - Consulta resultado do job (status, dados, erro)
- [ ] `GET /api/tubehunt/status` - Status da sessão

### 4.4 Configurações
- [x] Variáveis de ambiente (.env)
- [x] URL do login
- [x] Credenciais (user, password)
- [x] Timeout configurável
- [x] URL do Selenium remoto
- [ ] Selectors para campos de login customizáveis

### 4.5 Schemas TubeHunt

#### Login e Scrape
```python
# Request
{
  "wait_time": 15,
  "extract_selector": "h1"  # Opcional, default é "h1"
}

# Response
{
  "success": true,
  "h1_text": "TubeHunt.io",
  "url": "https://app.tubehunt.io/",
  "timestamp": "2026-01-01T18:51:36.640000",
  "error": null
}
```

#### Navegação para Vídeos
```python
# Request
(sem corpo - usa credenciais do .env)

# Response
{
  "success": true,
  "url": "https://app.tubehunt.io/long/?page=1&OrderBy=DateDESC&ChangePerPage=50",
  "title": "TubeHunt.io",
  "video_elements_count": 538,
  "links_count": 459,
  "images_count": 322,
  "buttons_count": 6,
  "timestamp": "2026-01-01T19:07:46.000000",
  "error": null
}
```

#### Scraping de Canais
```python
# Request
(sem corpo - usa credenciais do .env)

# Response
{
  "success": true,
  "channels": [
    {
      "channel_name": "O Caminho Sagrado",
      "channel_link": "https://app.tubehunt.io/channel/UCo9J4v08H7so8znUgydIC6Q",
      "channel_handle": "@ocaminhosagrado-2026",
      "country": "(PT)",
      "subscribers": "3k",
      "is_verified": true,
      "is_monetized": true,
      "total_views": "61k",
      "views_last_60_days": "105k",
      "average_views_per_video": "20k",
      "time_since_first_video": "há 5 dias",
      "total_videos": "3",
      "outlier_score": "22×",
      "recent_videos": [
        {
          "title": "7 PECADOS Que Você Deve CONFESSAR...",
          "video_link": "https://youtube.com/watch?v=Rk53pD3AJTA",
          "thumbnail_url": "https://i.ytimg.com/vi/Rk53pD3AJTA/mqdefault.jpg",
          "duration": "54:01",
          "views": "75k",
          "comments": "775",
          "uploaded_time": "há 4 dias"
        }
      ]
    }
  ],
  "total_channels": 10,
  "timestamp": "2026-01-01T20:00:00.000000",
  "error": null
}
```

#### Job Queue - Scraping Assíncrono (Fase 2)

**Iniciar Job de Scraping**
```python
# POST /api/v1/tubehunt/scrape-channels/start
# Request: (sem corpo)

# Response
{
  "job_id": "abc123xyz789",
  "status": "pending",
  "message": "Job enfileirado com sucesso",
  "created_at": "2026-01-01T20:00:00.000000"
}
```

**Consultar Resultado do Job**
```python
# GET /api/v1/tubehunt/scrape-channels/result/{job_id}

# Response (quando pendente/processando)
{
  "job_id": "abc123xyz789",
  "status": "processing",
  "progress": 45,
  "message": "Extraindo dados de canais... 45/50 concluído"
}

# Response (quando completo)
{
  "job_id": "abc123xyz789",
  "status": "completed",
  "result": {
    "success": true,
    "channels": [...],  # Mesmo formato de scrape-channels síncrono
    "total_channels": 50,
    "timestamp": "2026-01-01T20:15:30.000000",
    "error": null
  },
  "execution_time_seconds": 330.5,
  "completed_at": "2026-01-01T20:15:30.000000"
}

# Response (quando falhou)
{
  "job_id": "abc123xyz789",
  "status": "failed",
  "error": "Erro ao fazer scraping: timeout na página",
  "failed_at": "2026-01-01T20:10:00.000000"
}
```

---

## 5. Serviço TubeHunt Detalhado

### 5.1 TubeHuntService (app/services/tubehunt.py)
```python
class TubeHuntService:
    def __init__(self, settings):
        self.login_url = settings.url_login
        self.username = settings.user
        self.password = settings.password
        self.selenium_url = settings.SELENIUM_URL
        self.driver = None

    def login_and_extract(self, extract_selector: str = "h1"):
        """
        1. Inicializa WebDriver
        2. Acessa página de login
        3. Preenche credenciais
        4. Submete formulário
        5. Aguarda carregamento
        6. Extrai elemento
        7. Fecha WebDriver
        """
        pass

    def navigate_to_videos(self, wait_time: int = 15):
        """
        1. Inicializa WebDriver
        2. Acessa página de login
        3. Preenche credenciais e submete
        4. Aguarda redirecionamento
        5. Navega para página de vídeos
        6. Aguarda carregamento completo
        7. Extrai informações da página
        8. Fecha WebDriver
        """
        pass
```

### 5.2 Passos de Implementação - Login & Scrape
1. **Inicializar WebDriver remoto** → Chrome headless
2. **Acessar login URL** → https://app.tubehunt.io/login
3. **Localizar campos** → input[type=email], input[type=password]
4. **Preencher credenciais** → .send_keys()
5. **Localizar botão** → button[type=submit] ou similar
6. **Submeter formulário** → .click() ou .submit()
7. **Aguardar redirecionamento** → WebDriverWait para elemento visível
8. **Extrair H1** → find_element(By.TAG_NAME, "h1").text
9. **Retornar resposta** → JSON estruturado

### 5.3 Passos de Implementação - Navegação para Vídeos
1. **Realizar login** → Reutiliza passos 1-7 do login_and_extract
2. **Navegar para vídeos URL** → https://app.tubehunt.io/long/?page=1&OrderBy=DateDESC&ChangePerPage=50
3. **Aumentar timeout** → driver.set_page_load_timeout(120) para página pesada
4. **Aguardar elementos** → WebDriverWait procurando .item, .video ou tr
5. **Contar elementos** → find_elements para video, links, images, buttons
6. **Extrair metadata** → current_url, page_title
7. **Retornar estatísticas** → JSON com contagens

---

## 6. Tratamento de Erros

- Credenciais inválidas → Resposta com erro claro
- Timeout no login → Resposta com timeout
- Elemento H1 não encontrado → Retornar null ou erro
- WebDriver crash → Tratamento de exceção
- Conexão Selenium falha → Health check falha

---

## 7. Variáveis de Ambiente Necessárias

```env
# Já existentes em .env
url_login=https://app.tubehunt.io/login
user=felipealfah@gmail.com
password=Tub3h@17560919

# Selenium
SELENIUM_URL=http://selenium-chrome:4444
SELENIUM_TIMEOUT=30

# API
API_HOST=0.0.0.0
API_PORT=8000
```

---

## 8. Dependências

### Já Instaladas
- fastapi>=0.104.1
- uvicorn>=0.24.0
- selenium>=4.15.2
- pydantic>=2.5.0
- pydantic-settings>=2.1.0
- python-dotenv>=1.0.0

### Possíveis Adições (Fase 2+)
- pytest>=7.4.0 (testes)
- pytest-asyncio (testes assíncronos)
- sqlalchemy (banco de dados)

---

## 9. Plano de Desenvolvimento

### Fase 1: MVP Login & Navegação TubeHunt (COMPLETO) ✅
1. [x] Criar TubeHuntService
2. [x] Criar schemas TubeHunt
3. [x] Criar routes TubeHunt
4. [x] Testar login e extração
5. [x] Testar navegação para vídeos
6. [x] Integração Docker
7. [x] Documentação de uso

### Fase 1.5: Scraping Completo de Canais (COMPLETO) ✅
1. [x] Analisar estrutura HTML dos cards de canais
2. [x] Criar VideoData schema
3. [x] Criar ChannelData schema
4. [x] Criar ChannelsListResponse schema
5. [x] Implementar método _extract_channel_data() em TubeHuntService
6. [x] Implementar método scrape_channels() em TubeHuntService
7. [x] Criar endpoint POST /api/v1/tubehunt/scrape-channels
8. [x] Testar extração de canais com dados de vídeos
9. [x] Validar resposta JSON e integridade de dados
10. [x] Documentar endpoint no Swagger

### Fase 1.6: Migração para Playwright v1.57.0 (COMPLETO) ✅
1. [x] Criar branch feature/playwright-migration
2. [x] Atualizar pyproject.toml com playwright>=1.57.0
3. [x] Atualizar Dockerfile para usar playwright
4. [x] Criar novo PlaywrightBrowserManager em app/core/browser.py
5. [x] Converter TubeHuntService para usar Playwright (sync API)
6. [x] Converter métodos Selenium → Playwright:
   - [x] _create_driver() → _init_browser()
   - [x] find_element() → page.query_selector()
   - [x] send_keys() → page.fill()
   - [x] click() → page.click() com no_wait_after=True
   - [x] WebDriverWait → page.wait_for_selector()
   - [x] wait_for_load_state() como fallback
7. [x] Testar todos os endpoints com Playwright
8. [x] Validar compatibilidade 100%
9. [x] Validar performance (Playwright é mais rápido)
10. [x] Testes de regressão completos
11. [x] Documentação atualizada
12. [x] Todos os 50 canais extraídos com sucesso

### Fase 2: Simplificação de Arquitetura (COMPLETO) ✅
1. [x] Remover sistema de Job Queue (não necessário)
2. [x] Remover sistema de Webhooks (não necessário)
3. [x] Remover implementação Async (desnecessária)
4. [x] Criar endpoint simples POST /scrape-channels síncrono
5. [x] Usar asyncio.to_thread() para executar Sync em FastAPI async
6. [x] Remover imports desnecessários
7. [x] Testar funcionamento com novo endpoint
8. [x] Documentar mudanças (SIMPLIFICATION.md, REBUILD_INSTRUCTIONS.md, etc)

### Fase 2.1: Job Queue + Webhook para Integração n8n (IMPLEMENTADO) ✅
**Motivação:** n8n possui timeout de 5-10 minutos enquanto o scraping leva 3-5 minutos variáveis. Implementar Job Queue + Webhook permite:
- n8n chama endpoint POST para iniciar job (retorna imediatamente com job_id)
- Scraping executa em background em thread separada
- Quando completa, webhook notifica n8n com resultado completo
- n8n não fica bloqueado aguardando resposta

**Implementação Completa:**
1. [x] Criar gerenciador de jobs (app/core/job_queue.py) - JobManager com thread-safety
2. [x] Criar schemas Job (JobStartResponse, JobStatusResponse, JobResultResponse) - Já existiam em schemas/tubehunt.py
3. [x] Criar endpoint POST /api/v1/tubehunt/scrape-channels/start - Com background thread
4. [x] Criar endpoint GET /api/v1/tubehunt/scrape-channels/result/{job_id} - Com suporte a 3 estados
5. [x] Implementar background task com threading - Thread daemon para scraping
6. [x] Implementar WebhookCaller com retry logic (exponential backoff) - 3 tentativas: 2s, 4s, 8s
7. [x] Suporte a variáveis da requisição - login_url, username, password com fallback .env
8. [x] Suporte a variável scrape_url - URL customizável para scraping com fallback padrão
9. [x] Documentar endpoints e fluxo - Documentação completa nos docstrings

**Resposta do Endpoint Job Queue - Mantém Compatibilidade:**
Quando o job completa, a resposta em GET /result/{job_id} retorna EXATAMENTE o mesmo formato de canais_extraidos_simples.json:
```json
{
  "job_id": "abc123xyz789",
  "status": "completed",
  "result": {
    "total_canais": 50,
    "canais": [
      {
        "channel_name": "...",
        "channel_link": "...",
        ...
      }
    ]
  },
  "execution_time_seconds": 330.5,
  "completed_at": "2026-01-01T20:15:30.000000"
}
```

**Endpoints:**
- `POST /api/v1/tubehunt/scrape-channels/start` → Retorna `{"job_id": "...", "status": "pending", "created_at": "..."}`
- `GET /api/v1/tubehunt/scrape-channels/result/{job_id}` → Retorna status ou resultado completo (com formato canais_extraidos_simples.json)
- `POST /webhook/job-complete` → Recebe callback de n8n (callback_url opcional na request)

**Job States:**
- `pending` - Job enfileirado, aguardando execução
- `processing` - Job em execução, scraping acontecendo
- `completed` - Job finalizou com sucesso, resultado disponível
- `failed` - Job falhou com erro

### Fase 3: Correções e Ajustes (COMPLETO) ✅
1. [x] Identificar problema de timeout no click (30s esperando navegação)
2. [x] Implementar no_wait_after=True para evitar esperar navegação
3. [x] Adicionar delay de 3s após click para navegação iniciar
4. [x] Corrigir lógica de redirecionamento (OR → AND)
5. [x] Adicionar wait_for_load_state() como fallback
6. [x] Reduzir timeout de espera de redirecionamento de 60s para 30s
7. [x] Adicionar verificações de page load entre etapas
8. [x] Testar scraping completo: 50 canais extraídos com sucesso

### Fase 2.2: Features Essenciais ⏰
- [ ] Testes unitários
- [ ] Tratamento robusto de erros
- [ ] Logging estruturado
- [ ] Validação de inputs
- [ ] Retry logic com backoff

### Fase 3: Qualidade ⏰
- [ ] CI/CD
- [ ] Cache de sessão
- [ ] Rate limiting
- [ ] Observabilidade

### Fase 4: Escala ⏰
- [ ] Banco de dados
- [ ] Fila de tarefas
- [ ] Multi-usuário

---

## 10. Instrução de Execução

```bash
# Build e execução
docker-compose up --build

# Acessar API
curl -X POST http://localhost:8000/api/tubehunt/login-and-scrape \
  -H "Content-Type: application/json" \
  -d '{"wait_time": 15}'

# Documentação
http://localhost:8000/docs
```

---

## 11. Comparação Selenium vs Playwright

### Stack Atual (Selenium)
- **Imagem Base Docker:** selenium/standalone-chrome:4.15.0 (~3GB)
- **Tamanho da Imagem:** 3.0GB+
- **API:** WebDriver Protocol (mais verbosa)
- **Navegadores:** Chrome apenas
- **Performance:** Baseline
- **Mensagens de erro:** Genéricas

### Stack Novo (Playwright v1.57.0)
- **Imagem Base Docker:** mcr.microsoft.com/playwright:v1.57.0 (~2GB)
- **Tamanho da Imagem:** 2.0GB
- **API:** Modern async/sync (mais intuitiva)
- **Navegadores:** Chrome, Firefox, Safari
- **Performance:** 2-3x mais rápido
- **Mensagens de erro:** Detalhadas e informativas

### Migração - Mudanças de Código

**Antes (Selenium)**
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Remote(command_executor=self.selenium_url)
driver.get(login_url)
email_field = driver.find_element(By.ID, "email")
email_field.send_keys(username)
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".page")))
```

**Depois (Playwright)**
```python
from playwright.sync_api import sync_playwright

async_context = await playwright.chromium.launch()
page = await context.new_page()
await page.goto(login_url)
await page.fill("#email", username)
await page.wait_for_selector(".page")
```

---

**Versão:** 3.2-JOB-QUEUE-PRODUÇÃO-READY
**Data:** 2026-01-06
**Status:** ✅ Migração Playwright + Job Queue + Webhook + Produção Cleanup COMPLETO
**Branch Atual:** feature/playwright-migration (Pronto para merge em main)
**Arquitetura:** Playwright Sync + FastAPI Async (asyncio.to_thread) + Job Queue + Webhook
**Resultado:**
- 50 canais extraídos com sucesso (síncro)
- Job Queue + Webhook implementado para n8n (assíncrono)
- Suporte a variáveis dinâmicas por requisição com fallback .env
- Suporte a scrape_url customizável com fallback padrão (planejado)
- 5 arquivos desnecessários removidos (16 arquivos Python mantidos)

### Limpeza de Produção Realizada
**Arquivos removidos do projeto:**
1. ❌ `app/api/routes.py` - DEPRECATED (v1 endpoints já existem)
2. ❌ `app/core/async_browser.py` - Async browser code (projeto usa sync apenas)
3. ❌ `app/services/scraper.py` - Selenium antigo (migrado para Playwright)
4. ❌ `app/services/tubehunt_async.py` - Async tubehunt (não usado - sync apenas)
5. ❌ `app/schemas/scrape.py` - Schemas genéricos antigos (replaced by tubehunt schemas)

**Arquivos mantidos (16 Python files):**
- ✅ `app/api/v1/tubehunt.py` - Endpoints TubeHunt (CORE)
- ✅ `app/core/config.py` - Configurações
- ✅ `app/core/job_queue.py` - Job Manager com thread-safety
- ✅ `app/services/webhook.py` - WebhookCaller com retry logic
- ✅ `app/services/tubehunt.py` - TubeHuntService (Playwright sync)
- ✅ `app/schemas/tubehunt.py` - Schemas TubeHunt
- ✅ Outros arquivos de suporte

### Feature: scrape_url Customizável
**Status:** ✅ Implementado
**Descrição:** Permite passar URL customizada para scraping via request, com fallback para URL padrão
**Benefício:** Flexibilidade para scraping de diferentes páginas (page=1, page=5, etc)

**Implementação Completa:**
- [x] Campo `scrape_url` existe no schema `ScrapeChannelsRequest` (opcional)
- [x] Método TubeHuntService.scrape_channels() aceita parâmetro `scrape_url` opcional
- [x] Usa URL fornecida se presente, caso contrário padrão: `https://app.tubehunt.io/long/?page=1&OrderBy=DateDESC&ChangePerPage=50`
- [x] Endpoint POST /start passa scrape_url para o serviço
- [x] Logging de URL customizada quando fornecida
- [x] Teste: test_scrape_url_feature.py criado

**Exemplo de uso:**
```bash
# Com URL customizada (página 2)
POST /api/v1/tubehunt/scrape-channels/start
{
  "scrape_url": "https://app.tubehunt.io/long/?page=2&OrderBy=DateDESC&ChangePerPage=50",
  "wait_time": 15
}

# Sem URL customizada (usa padrão - página 1)
POST /api/v1/tubehunt/scrape-channels/start
{
  "wait_time": 15
}
```

**Como testar:**
```bash
python3 test_scrape_url_feature.py
```
