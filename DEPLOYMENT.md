# 🚀 Guia de Deployment - Scrape TH API

## Status Atual
✅ **Versão:** 3.2 - PRONTO PARA PRODUÇÃO
✅ **Data:** 2026-01-06
✅ **Branch:** main
✅ **Deploy:** EasyPanel

---

## 📋 Resumo da Implementação

### Arquitetura
```
FastAPI (Async)
    ↓
Job Queue (Threading)
    ↓
Playwright Sync (Browser Automation)
    ↓
Webhook Caller (Retry Logic)
```

### Features Implementadas

#### ✅ Job Queue + Webhook
- Execução em background via threading
- Webhook callbacks com retry logic (exponencial: 2s, 4s, 8s)
- Status polling: pending → processing → completed/failed
- Suporte a múltiplos jobs simultâneos

#### ✅ Playwright Migration
- Migração completa de Selenium para Playwright
- Sync API (não async)
- Chromium pré-instalado no Docker
- Performance: ~4-5 minutos para 50 canais

#### ✅ Variáveis Dinâmicas
- Credenciais por request com fallback .env
- Scrape URL customizável
- Wait time ajustável
- Webhook URL customizável

#### ✅ Health Check
- Endpoint: `GET /api/v1/tubehunt/health`
- Retorna status de todos os serviços
- Uptime tracking
- Ideal para monitoramento

#### ✅ Limpeza de Produção
- 5 arquivos desnecessários removidos
- Projeto reduzido de 21 para 16 arquivos Python
- Sem dependências de async browser
- Sem Selenium (deprecated)

---

## 🔧 Configuração no EasyPanel

### Variáveis de Ambiente Necessárias

```env
# Credenciais TubeHunt (obrigatórios como fallback)
TUBEHUNT_LOGIN_URL=https://app.tubehunt.io/login
TUBEHUNT_USER=seu_email@gmail.com
TUBEHUNT_PASSWORD=sua_senha

# API Configuration
API_HOST=0.0.0.0
API_PORT=80
LOG_LEVEL=INFO
```

### Health Check Setup (IMPORTANTE)

1. **Health Check Path:** `/api/v1/tubehunt/health`
2. **Health Check Interval:** `30 segundos`
3. **Health Check Timeout:** `10 segundos`
4. **Health Check Retries:** `3`

### Requisitos de Recursos

- **Memory:** Mínimo 1GB (Playwright + Chromium)
- **CPU:** Mínimo 1 core
- **Disk:** ~500MB para Chromium

---

## 📡 Endpoints Disponíveis

### 1. Health Check
```bash
GET /api/v1/tubehunt/health
```
**Response:** `200 OK`
```json
{
  "status": "ok",
  "version": "1.5",
  "services": {
    "api": "healthy",
    "selenium": "healthy"
  },
  "uptime_seconds": 3600.5,
  "message": "API está funcionando corretamente"
}
```

### 2. Iniciar Job de Scraping
```bash
POST /api/v1/tubehunt/scrape-channels/start
```

**Request (todos os campos opcionais):**
```json
{
  "login_url": "https://app.tubehunt.io/login",
  "username": "custom@email.com",
  "password": "custom_password",
  "scrape_url": "https://app.tubehunt.io/long/?page=2&OrderBy=DateDESC&ChangePerPage=50",
  "webhook_url": "https://seu-webhook.com/endpoint",
  "wait_time": 20
}
```

**Response:** `200 OK`
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Job criado com sucesso",
  "created_at": "2026-01-06T22:15:09.330000"
}
```

### 3. Obter Status do Job
```bash
GET /api/v1/tubehunt/scrape-channels/result/{job_id}
```

**Response - Pending:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "created_at": "2026-01-06T22:15:09.330000"
}
```

**Response - Processing:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 45,
  "message": "Navegando para página de canais...",
  "created_at": "2026-01-06T22:15:09.330000"
}
```

**Response - Completed:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "total_canais": 50,
    "canais": [
      {
        "channel_name": "Nome do Canal",
        "channel_link": "https://www.youtube.com/...",
        "subscribers": "1M"
      }
    ]
  },
  "execution_time_seconds": 245.5,
  "created_at": "2026-01-06T22:15:09.330000"
}
```

**Response - Failed:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "error": "Erro ao fazer login",
  "failed_at": "2026-01-06T22:15:09.330000",
  "created_at": "2026-01-06T22:15:09.330000"
}
```

---

## 🔄 Fluxo de Uso (Recomendado)

### 1. Iniciar Scraping
```bash
curl -X POST https://fulled-th-scrape.nbshm6.easypanel.host/api/v1/tubehunt/scrape-channels/start \
  -H "Content-Type: application/json" \
  -d '{
    "scrape_url": "https://app.tubehunt.io/long/?page=2&OrderBy=DateDESC&ChangePerPage=50",
    "webhook_url": "https://seu-webhook.com/callback",
    "wait_time": 20
  }'
```

### 2. Recebe job_id na resposta
```
Exemplo: "550e8400-e29b-41d4-a716-446655440000"
```

### 3. Fazer polling para status
```bash
# A cada 3-5 segundos
curl -X GET https://fulled-th-scrape.nbshm6.easypanel.host/api/v1/tubehunt/scrape-channels/result/550e8400-e29b-41d4-a716-446655440000
```

### 4. Webhook Callback Automático
Quando o job terminar com `status: "completed"`, a API automaticamente envia POST para `webhook_url` com:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "total_canais": 50,
    "canais": [...]
  },
  "execution_time_seconds": 245.5
}
```

---

## 🐳 Docker - Otimizações para EasyPanel

### Dockerfile Changes
- ✅ `--workers 1`: Reduz memória de ~800MB para ~300MB
- ✅ `--timeout-keep-alive 75`: Conexões mais eficientes
- ✅ `.dockerignore`: Build mais rápido
- ✅ Python 3.11 slim: Base otimizada

### Build Context
```
Repository: https://github.com/felipealfah/th_scrape.git
Branch: main
Dockerfile: ./Dockerfile
Build Context: . (raiz)
Port: 8000 (mapeado para porta do EasyPanel)
```

---

## ✅ Checklist de Deployment

- [ ] Variáveis de ambiente configuradas no EasyPanel
- [ ] Memory limit: 1GB ou mais
- [ ] Health check path: `/api/v1/tubehunt/health`
- [ ] Porta mapeada corretamente (8000 → porta do EasyPanel)
- [ ] CORS habilitado (já está `allow_origins: ["*"]`)
- [ ] Rebuild imagem Docker a partir de `main` branch
- [ ] Testar health check: `curl https://fulled-th-scrape.nbshm6.easypanel.host/api/v1/tubehunt/health`
- [ ] Testar início de job
- [ ] Testar polling de status

---

## 🐛 Troubleshooting

### Erro: "No such option: --timeout"
✅ **Resolvido** - Usar `--timeout-keep-alive` ao invés

### Erro: 502 Bad Gateway
❌ **Causa:** Falta de memória ou timeout
✅ **Solução:** Aumentar memory limit para 1GB+ no EasyPanel

### Erro: "Connection refused" em health check
❌ **Causa:** Container não iniciou
✅ **Solução:** Verificar logs do Docker, aumentar timeout de health check

### Job não retorna resultado
❌ **Causa:** Job ainda processando
✅ **Solução:** Esperar mais tempo (até 360 segundos) e fazer polling novamente

---

## 📞 Contato & Suporte

**Projeto:** Scrape TH API
**Versão:** 3.2
**Desenvolvedor:** Felipe Full
**Data:** 2026-01-06
**Status:** Production Ready ✅

---

## 🔐 Security Notes

- ✅ CORS habilitado para todas as origens (ajustar em produção se necessário)
- ✅ Sem autenticação na API (adicionar se necessário)
- ✅ Variáveis sensíveis (.env) não versionadas
- ✅ Logs não expõem senhas completas

---

## 📈 Performance Esperada

- **Tempo de startup:** ~10-15 segundos
- **Tempo de scraping:** ~4-5 minutos (50 canais)
- **Memória em repouso:** ~300MB
- **Memória durante scraping:** ~600-800MB
- **Threads simultâneas:** 1 (workers=1)

---

**Última atualização:** 2026-01-06
**Próxima revisão:** 2026-01-13
