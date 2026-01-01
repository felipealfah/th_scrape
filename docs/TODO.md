# TODO - Scrape TH API

## Convenção de Status
- `[ ]` - Pendente
- `[~]` - Em progresso
- `[x]` - Completo
- `[-]` - Cancelado/Não será feito

---

## Fase 0: Setup Inicial (COMPLETO)

### Estrutura e Configuração
- [x] Inicializar projeto com pyproject.toml
- [x] Criar estrutura de diretórios
- [x] Configurar variáveis de ambiente (.env)
- [x] Criar arquivo .env.example
- [x] Setup Docker e Docker Compose
- [x] Criar Dockerfile com Selenium Chrome
- [x] Claude Code initialization (.claude/claude.json)

### Aplicação FastAPI
- [x] Criar aplicação principal (app/main.py)
- [x] Configurar CORS
- [x] Criar endpoint GET /
- [x] Criar endpoint GET /api/health
- [x] Adicionar logging básico

### Scraping Genérico com Selenium
- [x] Criar serviço ScraperService (app/services/scraper.py)
- [x] Implementar conexão com Selenium remoto
- [x] Implementar extração de dados via CSS selectors
- [x] Implementar context manager para WebDriver
- [x] Tratamento básico de exceções

### Schemas e Validação
- [x] Criar ScrapeRequest schema
- [x] Criar ScrapeResponse schema
- [x] Adicionar exemplos nos schemas

### API Endpoints Genéricos
- [x] Implementar POST /api/scrape
- [x] Validação básica de inputs
- [x] Retornar respostas estruturadas

### Documentação do Projeto
- [x] PLAN.md criado e atualizado
- [x] TODO.md criado
- [x] Atualizar PLAN.md com fluxo TubeHunt
- [x] Atualizar TODO.md com tarefas TubeHunt

---

## Fase 1: MVP Login & Navegação TubeHunt (COMPLETO) ✅

### Pré-requisitos
- [x] Variáveis de ambiente TubeHunt em .env (url_login, user, password)
- [x] Atualizar .env.example com variáveis TubeHunt
- [x] Verificar credenciais carregadas corretamente no config.py
- [x] Teste manual: acessar site com browser comum (validação manual)

### Schemas TubeHunt
- [x] Criar arquivo app/schemas/tubehunt.py
- [x] Criar TubeHuntLoginRequest schema com validações
- [x] Criar TubeHuntLoginResponse schema
- [x] Adicionar campos: success, h1_text, url, timestamp, error
- [x] Adicionar exemplos nos schemas
- [x] Documentar validações
- [x] Criar TubeHuntVideosResponse schema
- [x] Adicionar campos: success, url, title, contagens, timestamp, error

### Serviço TubeHunt (CORE)
- [x] Criar arquivo app/services/tubehunt.py
- [x] Classe TubeHuntService com __init__
- [x] Método _create_driver() - inicializar WebDriver remoto
- [x] Método get_driver() - get ou criar driver
- [x] Método _access_login_page() - acessar login URL
- [x] Método _find_email_field() - localizar email com múltiplos seletores
- [x] Método _find_password_field() - localizar password com múltiplos seletores
- [x] Método _fill_credentials() - preencher email e senha
- [x] Método _find_submit_button() - localizar botão submit com múltiplos seletores
- [x] Método _submit_form() - clicar botão submit
- [x] Método _wait_for_redirect() - aguardar carregamento pós-login
- [x] Método _extract_element() - extrair elemento por seletor com fallback
- [x] Método login_and_extract() - orquestrar fluxo de login e extração
- [x] Método navigate_to_videos() - login + navegar para vídeos (NEW)
- [x] Método close() - fechar WebDriver com cleanup
- [x] Tratamento de exceções em cada método
- [x] Context manager (__enter__, __exit__)

### Routes TubeHunt
- [x] Criar pasta app/api/v1/ com __init__.py
- [x] Criar arquivo app/api/v1/tubehunt.py
- [x] Endpoint POST /api/v1/tubehunt/login-and-scrape
- [x] Documentação completa no docstring
- [x] Logging de requisições
- [x] Error handling no endpoint
- [x] Retornar response estruturada
- [x] Endpoint POST /api/v1/tubehunt/navigate-to-videos (NEW)
- [x] Endpoint GET /api/v1/tubehunt/health

### Integração com FastAPI
- [x] Atualizar app/main.py para incluir router v1
- [x] Testar import dos routers
- [x] Verificar endpoints no Swagger

### Testes Manuais do TubeHunt
- [x] Teste LOCAL: iniciar servidor FastAPI local
- [x] Teste DOCKER: iniciar com docker-compose
- [x] Teste endpoint com curl/Postman
- [x] Validar resposta JSON com sucesso
- [x] Validar extração do h1
- [x] Validar estrutura da resposta
- [x] Teste com wait_time variável
- [x] Teste com timeout
- [x] Teste com credenciais inválidas
- [x] Verificar mensagens de erro
- [x] Teste navegação para página de vídeos (NEW)
- [x] Validar contagem de elementos (videos, links, images, buttons) (NEW)
- [x] Validar timeout aumentado para 120 segundos (NEW)

---

## Fase 1.5: Scraping Completo de Canais (COMPLETO) ✅

### Análise da Estrutura de Canais
- [x] Analisar HTML da página de canais
- [x] Identificar seletor CSS para cada canal
- [x] Identificar campos disponíveis (nome, link, handle, subs, monetização, verificação, stats, vídeos, etc)
- [x] Documentar estrutura dos dados
- [x] Criar exemplos de dados extraídos

### Schema para Dados de Vídeo e Canal
- [x] Criar VideoData schema com campos relevantes
- [x] Definir campos obrigatórios vs opcionais
- [x] Adicionar validações
- [x] Adicionar exemplos
- [x] Criar ChannelData schema com todos os campos
- [x] Criar ChannelsListResponse schema

### Método de Extração de Canais
- [x] Criar método _extract_channel_data() em TubeHuntService
- [x] Implementar lógica de extração de dados
- [x] Tratar casos onde campos podem estar vazios
- [x] Extrair dados de 6 vídeos por canal
- [x] Retornar lista estruturada de canais
- [x] Criar método scrape_channels() para orquestração completa

### Endpoint para Dados de Canais
- [x] Criar schema ChannelsListResponse
- [x] Criar endpoint POST /api/v1/tubehunt/scrape-channels
- [x] Integrar com navigate_to_videos() e _extract_channel_data()
- [x] Documentar endpoint completo com exemplos no Swagger
- [x] Adicionar logging estruturado

### Testes de Scraping de Canais
- [x] Teste: extrair canais com sucesso
- [x] Teste: validar estrutura dos dados
- [x] Teste: validar número de canais extraídos (10 canais)
- [x] Teste: validar campos obrigatórios em todos os canais
- [x] Teste: extrair até 6 vídeos por canal com sucesso

---

## Fase 2: Job Queue Assíncrono para Scraping

### Sistema de Fila de Jobs
- [ ] Criar app/core/job_queue.py com gerenciador de jobs
- [ ] Definir estrutura de Job (id, status, data, timestamp)
- [ ] Implementar armazenamento em memória (dict/cache)
- [ ] Criar métodos: create_job(), get_job(), update_job(), list_jobs()
- [ ] Implementar limpeza automática de jobs > 24h

### Schemas para Job Queue
- [ ] Criar JobStartResponse schema (job_id, status, message, created_at)
- [ ] Criar JobStatusResponse schema (job_id, status, progress, message)
- [ ] Criar JobResultResponse schema (job_id, status, result, execution_time)
- [ ] Criar JobErrorResponse schema (job_id, status, error, failed_at)
- [ ] Adicionar exemplos em todos os schemas

### Endpoints Assíncronos
- [ ] Criar POST /api/v1/tubehunt/scrape-channels/start
- [ ] Criar GET /api/v1/tubehunt/scrape-channels/result/{job_id}
- [ ] Implementar background task para scraping
- [ ] Retornar job_id para rastrear progresso
- [ ] Suportar status: pending, processing, completed, failed

### Execução em Background
- [ ] Usar threading.Thread ou asyncio.create_task()
- [ ] Armazenar resultado do job após conclusão
- [ ] Capturar e armazenar erros
- [ ] Calcular tempo de execução
- [ ] Registrar progresso do job (opcional: progress %)

### Testes de Job Queue
- [ ] Teste: criar job retorna job_id válido
- [ ] Teste: consultar job em progresso
- [ ] Teste: consultar job completo com resultado
- [ ] Teste: consultar job falhado com erro
- [ ] Teste: job_id inválido retorna 404
- [ ] Teste: múltiplos jobs simultâneos

---

## Fase 2.1: Features Essenciais e Testes

### Health Check e Monitoramento (JÁ COMPLETO)
- [x] Criar schema HealthCheckResponse com campos: status, timestamp, version, services, uptime, message
- [x] Implementar endpoint GET /api/v1/tubehunt/health
- [x] Verificação de status Selenium no health check
- [x] Verificação de variáveis de ambiente no health check
- [x] Verificação de Docker detection no health check
- [x] Cálculo de uptime em segundos
- [x] Status progressivo: ok, degraded, error
- [ ] Testar health check endpoint com curl/Postman
- [ ] Validar resposta JSON do health check
- [ ] Documentar possíveis respostas do health check

### Testes Unitários
- [ ] Instalar pytest e pytest-asyncio
- [ ] Criar tests/test_tubehunt_service.py
- [ ] Testes para login_and_extract()
- [ ] Mock WebDriver para testes
- [ ] Testes com credenciais válidas
- [ ] Testes com credenciais inválidas
- [ ] Testes de timeout
- [ ] Testes de elemento não encontrado
- [ ] Criar tests/test_tubehunt_routes.py
- [ ] Testes dos endpoints
- [ ] Testes de validação de schemas
- [ ] Cobertura mínima de 70%
- [ ] GitHub Actions para rodar testes automaticamente

### Tratamento de Erros Robusto
- [ ] Criar exceptions customizadas (app/core/exceptions.py)
- [ ] TubeHuntAuthError - falha de autenticação
- [ ] TubeHuntTimeoutError - timeout
- [ ] TubeHuntElementNotFoundError - elemento não localizado
- [ ] TubeHuntWebDriverError - erro no webdriver
- [ ] Capturar e tratar cada tipo de erro
- [ ] Mensagens de erro claras e informativas
- [ ] Status HTTP apropriados nas respostas
- [ ] Nunca expor stack traces ao cliente

### Logging Estruturado
- [ ] Criar app/utils/logger.py com setup de logging
- [ ] Logging em TubeHuntService (entrada, saída, etapas)
- [ ] Logging em routes (requisições, respostas)
- [ ] Diferentes níveis: DEBUG, INFO, WARNING, ERROR
- [ ] Timestamp em todos os logs
- [ ] NUNCA logar credenciais (mascarar email/senha)
- [ ] Log de tempo total de execução
- [ ] Log de cada etapa do login

### Validação Robusta
- [ ] Validar URL de login no schema
- [ ] Validar formato de email do .env
- [ ] Validar timeout (min/max)
- [ ] Testes de validação
- [ ] Feedback claro para validações falhas

### Retry Logic (Opcional para MVP)
- [ ] Implementar retry com backoff exponencial
- [ ] Máximo de 3 tentativas (configurável)
- [ ] Delay de 2s entre tentativas
- [ ] Log de cada tentativa

### Documentação
- [ ] Atualizar README.md com TubeHunt
- [ ] Seção: Como fazer login no TubeHunt
- [ ] Exemplos de curl
- [ ] Exemplos de Python
- [ ] Troubleshooting section
- [ ] Explicar cada campo da resposta
- [ ] Guia de configuração (.env)

### Qualidade de Código
- [ ] Adicionar type hints em todos os métodos
- [ ] Docstrings em todas as funções/classes
- [ ] Instalar e configurar black (code formatter)
- [ ] Instalar e configurar flake8 (linter)
- [ ] Rodar black em todo código
- [ ] Rodar flake8 e corrigir issues
- [ ] Pre-commit hooks para formatação

---

## Fase 3: Segurança e Performance

### Segurança
- [ ] Revisão: credenciais nunca expostas em logs
- [ ] Revisão: email nunca exposto em response (opcional mascarar)
- [ ] Validação: aceitar apenas URLs HTTPS (futuro)
- [ ] Rate limiting para prevenir força bruta
- [ ] CORS restritivo (só origem esperada)
- [ ] Sanitizar inputs de seletores

### Performance
- [ ] Validar timeouts (muito rápido? muito lento?)
- [ ] Otimizar wait conditions (usar WebDriverWait corretamente)
- [ ] Profiling de memória durante login
- [ ] Monitorar CPU usage do Chrome
- [ ] Testes de carga (múltiplas requisições paralelas)

### Monitoramento
- [ ] Métricas de sucesso/falha
- [ ] Tempo médio de resposta
- [ ] Health check expandido com status Selenium
- [ ] Alertas para falhas (email/Slack - futuro)

---

## Fase 4: Escalabilidade

### Cache de Sessão (Futuro)
- [ ] Armazenar cookies de sessão
- [ ] Reuso de WebDriver entre requisições
- [ ] TTL de sessão configurável
- [ ] Invalidação de cache

### Banco de Dados
- [ ] Escolher banco: PostgreSQL
- [ ] Modelo para histórico de scraping
- [ ] Armazenar resultados
- [ ] Timestamps de cada login
- [ ] Migrations com Alembic

### Fila de Tarefas (Futuro)
- [ ] Setup Redis
- [ ] Setup Celery
- [ ] Tarefas assíncronas de login
- [ ] Job tracking

### Multi-Usuário
- [ ] Armazenar credenciais diferentes (criptografadas)
- [ ] Endpoint para criar/atualizar credenciais
- [ ] Autenticação API key
- [ ] Rate limiting por usuário

---

## Funcionalidades Futuras

### Features Avançadas de Scraping
- [ ] JavaScript rendering avançado (se necessário)
- [ ] Custom headers
- [ ] User-Agent rotation
- [ ] Screenshot da página após login
- [ ] Exportar dados em CSV/JSON

### API Features
- [ ] Versionamento: /api/v2, /api/v3
- [ ] Deprecation warnings
- [ ] Changelog automático
- [ ] Batch endpoint para múltiplos logins

### Analytics
- [ ] Dashboard de estatísticas
- [ ] Relatórios de uso
- [ ] Insights (horários de pico, etc)

---

## Dependências Entre Tarefas

```
Fase 0: Setup (✅ COMPLETO)
  └─> Fase 1: MVP TubeHunt (✅ COMPLETO)
      ├─> Schemas TubeHunt ✅
      ├─> TubeHuntService ✅
      ├─> Routes TubeHunt ✅
      ├─> Integração FastAPI ✅
      └─> Testes Manuais ✅
          └─> Fase 1.5: Scraping Completo de Canais (✅ COMPLETO)
              ├─> Análise de Estrutura ✅
              ├─> Schema VideoData & ChannelData ✅
              ├─> Método _extract_channel_data() ✅
              ├─> Método scrape_channels() ✅
              ├─> Endpoint scrape-channels ✅
              └─> Testes de Scraping ✅
                  └─> Fase 2: Job Queue Assíncrono (⏰ PRÓXIMA)
                      ├─> Sistema de Fila de Jobs
                      ├─> Schemas Job Queue
                      ├─> Endpoints start/result
                      └─> Background Tasks
                          └─> Fase 2.1: Features & Testes (⏰ DEPOIS)
                              ├─> Testes Unitários
                              ├─> Tratamento de Erros
                              ├─> Logging
                              └─> Documentação
                                  └─> Fase 3: Segurança (⏰ DEPOIS)
                                      └─> Fase 4: Escalabilidade (⏰ FUTURO)
```

---

## Timeline Estimada

| Fase | Status | Duração | Términô |
|------|--------|---------|----------|
| Fase 0 | ✅ COMPLETO | 2 dias | 2026-01-01 |
| Fase 1 | ✅ COMPLETO | 3-4 dias | 2026-01-01 |
| Fase 1.5 | ✅ COMPLETO | 2 dias | 2026-01-01 |
| Fase 2 (Job Queue) | ⏰ PRÓXIMA | 2-3 dias | 2026-01-03 |
| Fase 2.1 (Features & Testes) | ⏰ PRÓXIMA | 3-5 dias | 2026-01-08 |
| Fase 3 | ⏰ PLANEJADO | 2-3 dias | 2026-01-11 |
| Fase 4 | ⏰ FUTURO | 1-2 semanas | 2026-01-29 |

---

## Métricas de Progresso

**Total Geral:** ~240 tarefas
**Fase 0 Completa:** 25 tarefas ✅
**Fase 1 Completa:** 50 tarefas ✅
**Fase 1.5 Completa:** 20 tarefas ✅
**Fase 2+:** ~145 tarefas

**Progresso Geral:** 44.6% 🚀

---

## Prioridades AGORA - Fase 2 (Próximas Horas)

### 🔴 CRÍTICAS (Job Queue - Evitar Timeout do n8n)
1. [ ] Criar JobQueue manager em app/core/job_queue.py
2. [ ] Implementar endpoint POST /api/v1/tubehunt/scrape-channels/start
3. [ ] Implementar endpoint GET /api/v1/tubehunt/scrape-channels/result/{job_id}
4. [ ] Implementar execução em background (threading ou asyncio)
5. [ ] Criar schemas para Job responses

### 🟡 ALTA (Testes & Validação)
6. [ ] Testar endpoints com curl/Postman
7. [ ] Validar resposta JSON dos novos endpoints
8. [ ] Teste com múltiplos jobs simultâneos
9. [ ] Documentar nova abordagem assíncrona

### 🟢 MÉDIA (Melhorias)
10. [ ] Implementar progress tracking (opcional)
11. [ ] Implementar retry de jobs falhados
12. [ ] Limpeza automática de jobs > 24h

---

## Definição de Conclusão - Fase 1 MVP ✅

O MVP foi **CONCLUÍDO** com sucesso:

### Funcionalidade ✅
- [x] App FastAPI rodando em Docker
- [x] Endpoint POST /api/v1/tubehunt/login-and-scrape criado e funcional
- [x] Login bem-sucedido no TubeHunt
- [x] Extração correta do primeiro h1
- [x] Response JSON estruturado
- [x] Endpoint POST /api/v1/tubehunt/navigate-to-videos criado e funcional
- [x] Navegação para página de vídeos com sucesso
- [x] Extração de metadados da página (contagens de elementos)

### Teste ✅
- [x] Endpoint funcionando localmente
- [x] Endpoint funcionando em Docker
- [x] Credenciais corretas do .env usadas
- [x] Testes manuais passando
- [x] Navegação com timeout de 120 segundos

### Documentação ✅
- [x] PLAN.md atualizado
- [x] TODO.md atualizado
- [x] Swagger documentado

---

## Definição de Conclusão - Fase 1.5 Scraping Completo de Canais ✅

Fase 1.5 foi **CONCLUÍDA** com sucesso:

### Funcionalidade ✅
- [x] Schema VideoData criado com campos relevantes
- [x] Schema ChannelData criado com todos os campos
- [x] Schema ChannelsListResponse implementado
- [x] Método _extract_channel_data() implementado em TubeHuntService
- [x] Método scrape_channels() implementado em TubeHuntService
- [x] Dados de canais extraídos com sucesso (10 canais)
- [x] Dados de vídeos extraídos com sucesso (6 por canal)
- [x] Response JSON estruturado com lista de canais e vídeos

### Teste ✅
- [x] Extração de canais funcionando corretamente
- [x] Validação de campos obrigatórios passou
- [x] Número correto de canais extraídos (10)
- [x] Número correto de vídeos extraídos (até 6 por canal)
- [x] Integridade de dados validada em JSON

### Documentação ✅
- [x] Endpoint POST /api/v1/tubehunt/scrape-channels documentado no Swagger
- [x] Exemplos de resposta completos adicionados
- [x] PLAN.md e TODO.md atualizados
- [x] Estrutura de schemas validada

---

**Última Atualização:** 2026-01-01
**Próxima Revisão:** 2026-01-06
**Status:** FASE 1.5 COMPLETA ✅ - PRONTO PARA DOCKER E TESTES DE API - INICIANDO FASE 2
**Responsável:** Felipe Full
