# API Documentation - Scrape TH

Documentação completa de todos os endpoints disponíveis na API de Web Scraping.

**Versão:** 1.0
**Base URL:** `http://localhost:8000` ou `https://seu-servidor.com`
**API Path:** `/api/v1`

---

## 📋 Índice

1. [Notion Nichos Endpoints](#notion-nichos-endpoints)
2. [TubeHunt Endpoints](#tubehunt-endpoints)
3. [Health Check Endpoints](#health-check-endpoints)
4. [Error Handling](#error-handling)
5. [Webhook Callbacks](#webhook-callbacks)
6. [Examples](#examples)

---

## Notion Nichos Endpoints

Endpoints para scraping de nichos da página Notion com API interception.

### 1. POST `/api/v1/notion/scrape-nichos/start`

**Descrição:** Inicia um job assíncrono para fazer scraping de nichos da página Notion.

**Request:**
```json
{
  "notion_url": "https://victorgonwp.notion.site/PASTA-100-NICHOS-PRO-2e7620bdb33e813db5dac38194635f51",
  "wait_time": 15,
  "webhook_url": "https://seu-webhook.com/callback"
}
```

**Parâmetros:**
| Campo | Tipo | Obrigatório | Descrição | Range |
|-------|------|-------------|-----------|-------|
| `notion_url` | string | ✅ Sim | URL da página Notion | - |
| `wait_time` | integer | ❌ Não | Tempo de espera em segundos | 5-120 (padrão: 15) |
| `webhook_url` | string | ❌ Não | URL para webhook callback | - |

**Response (201):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Job enfileirado com sucesso",
  "created_at": "2026-01-22T13:44:56.551181"
}
```

**Erros Possíveis:**
- `400`: URL inválida (não contém "notion.site")
- `500`: Erro ao criar o job

**Exemplo cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/notion/scrape-nichos/start" \
  -H "Content-Type: application/json" \
  -d '{
    "notion_url": "https://victorgonwp.notion.site/PASTA-100-NICHOS-PRO-2e7620bdb33e813db5dac38194635f51",
    "wait_time": 20,
    "webhook_url": "https://seu-webhook.com/callback"
  }'
```

---

### 2. GET `/api/v1/notion/scrape-nichos/result/{job_id}`

**Descrição:** Obtém o status e resultado de um job de scraping de nichos.

**URL Parameters:**
| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `job_id` | string | ID do job retornado por `/scrape-nichos/start` |

**Response - Job em Progresso (200):**
```json
{
  "success": false,
  "nichos": [],
  "total_nichos": 0,
  "timestamp": "2026-01-22T13:46:00.086055",
  "error": "Job ainda em processamento. Progresso: 45%"
}
```

**Response - Job Concluído (200):**
```json
{
  "success": true,
  "nichos": [
    {
      "name": "Movies Consigliere",
      "category": "TV shows / Movie franchises",
      "image_url": "https://image.notion.com/...",
      "rpm": "4",
      "sub_niche": "Mafia Movies",
      "data": "Vazio",
      "place": "Vazio",
      "url": "https://www.youtube.com/@MoviesConsigliere/videos"
    }
  ],
  "total_nichos": 201,
  "timestamp": "2026-01-22T13:50:00.000000",
  "error": null
}
```

**Response - Job Falhou (200):**
```json
{
  "success": false,
  "nichos": [],
  "total_nichos": 0,
  "timestamp": "2026-01-22T13:46:00.086055",
  "error": "Timeout na página Notion"
}
```

**Erros Possíveis:**
- `404`: Job não encontrado
- `500`: Erro ao obter resultado

**Status Possíveis:**
- `pending`: Job aguardando início
- `processing`: Job em execução
- `completed`: Job finalizado com sucesso
- `failed`: Job falhou

**Exemplo cURL:**
```bash
curl "http://localhost:8000/api/v1/notion/scrape-nichos/result/550e8400-e29b-41d4-a716-446655440000"
```

---

### 3. GET `/api/v1/notion/health`

**Descrição:** Health check do serviço de scraping Notion.

**Response (200):**
```json
{
  "status": "healthy",
  "service": "notion-nichos-scraper",
  "version": "1.0"
}
```

**Exemplo cURL:**
```bash
curl "http://localhost:8000/api/v1/notion/health"
```

---

## TubeHunt Endpoints

Endpoints para scraping de dados do TubeHunt.io.

### 1. POST `/api/v1/tubehunt/login-and-scrape`

**Descrição:** Faz login no TubeHunt e extrai dados de um elemento específico da página.

**Request:**
```json
{
  "wait_time": 15,
  "extract_selector": "h1"
}
```

**Parâmetros:**
| Campo | Tipo | Obrigatório | Descrição | Range |
|-------|------|-------------|-----------|-------|
| `wait_time` | integer | ❌ Não | Tempo de espera em segundos | 5-60 (padrão: 15) |
| `extract_selector` | string | ❌ Não | Seletor CSS do elemento | - |

**Credenciais:** Usa variáveis de ambiente (`.env`):
```
TUBEHUNT_LOGIN_URL=https://app.tubehunt.io/login
TUBEHUNT_USER=seu_email@example.com
TUBEHUNT_PASSWORD=sua_senha
```

**Response (200):**
```json
{
  "success": true,
  "h1_text": "TubeHunt.io",
  "url": "https://app.tubehunt.io/",
  "timestamp": "2026-01-22T13:44:56.640000",
  "error": null
}
```

**Erros Possíveis:**
- `500`: Erro no login ou Selenium indisponível

**Exemplo cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/tubehunt/login-and-scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "wait_time": 15,
    "extract_selector": "h1"
  }'
```

---

### 2. POST `/api/v1/tubehunt/navigate-to-videos`

**Descrição:** Faz login no TubeHunt e navega até a página de vídeos com paginação.

**Request:** Sem body (usa credenciais do `.env`)

**Response (200):**
```json
{
  "success": true,
  "url": "https://app.tubehunt.io/long/?page=1&OrderBy=DateDESC&ChangePerPage=50",
  "title": "TubeHunt.io",
  "video_elements_count": 538,
  "links_count": 459,
  "images_count": 322,
  "buttons_count": 6,
  "timestamp": "2026-01-22T13:47:30.000000",
  "error": null
}
```

**Erros Possíveis:**
- `500`: Erro no login ou navegação

**Exemplo cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/tubehunt/navigate-to-videos" \
  -H "Content-Type: application/json"
```

---

## Health Check Endpoints

### 1. GET `/api/v1/tubehunt/health`

**Descrição:** Health check completo do serviço TubeHunt com status de todas as dependências.

**Response (200):**
```json
{
  "status": "ok",
  "timestamp": "2026-01-22T13:50:00.000000",
  "version": "1.5",
  "services": {
    "api": "healthy",
    "selenium": "healthy",
    "docker": "healthy",
    "environment": "healthy"
  },
  "uptime_seconds": 3600.5,
  "message": "API está funcionando corretamente com todos os serviços online"
}
```

**Status Possíveis:**
- `ok`: Todos os serviços funcionando corretamente
- `degraded`: Alguns serviços com problemas, API funciona
- `error`: Serviço principal indisponível

**Exemplo cURL:**
```bash
curl "http://localhost:8000/api/v1/tubehunt/health"
```

---

## Error Handling

### Padrão de Erro

Todos os erros seguem este padrão:

```json
{
  "detail": "Mensagem de erro descritiva"
}
```

### Códigos HTTP Comuns

| Código | Significado | Exemplo |
|--------|-------------|---------|
| `200` | Sucesso | Dados obtidos com sucesso |
| `201` | Criado | Job criado com sucesso |
| `400` | Bad Request | Parâmetros inválidos |
| `404` | Not Found | Job/recurso não encontrado |
| `500` | Internal Server Error | Erro no servidor ou dependência |

---

## Webhook Callbacks

Quando você fornece um `webhook_url` ao iniciar um scraping Notion, a API enviará um callback quando o job terminar.

### Webhook Payload - Sucesso

**Method:** POST
**Content-Type:** application/json

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "success": true,
    "nichos": [
      {
        "name": "Movies Consigliere",
        "category": "TV shows / Movie franchises",
        "image_url": "https://image.notion.com/...",
        "rpm": "4",
        "sub_niche": "Mafia Movies",
        "data": "Vazio",
        "place": "Vazio",
        "url": "https://www.youtube.com/@MoviesConsigliere/videos"
      }
    ],
    "total_nichos": 201,
    "timestamp": "2026-01-22T13:50:00.000000",
    "error": null
  },
  "execution_time_seconds": 330.5,
  "error": null,
  "timestamp": "2026-01-22T13:50:01.000000"
}
```

### Webhook Payload - Erro

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "result": null,
  "execution_time_seconds": 45.2,
  "error": "Timeout na página Notion",
  "timestamp": "2026-01-22T13:45:30.000000"
}
```

### Configuração do Webhook

Para testar webhooks localmente, você pode usar:
- **ngrok:** `ngrok http 3000`
- **RequestBin:** https://requestbin.com
- **n8n:** https://n8n.io

---

## Examples

### Exemplo 1: Scraping Completo Notion

```bash
#!/bin/bash

# 1. Iniciar scraping
RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/notion/scrape-nichos/start" \
  -H "Content-Type: application/json" \
  -d '{
    "notion_url": "https://victorgonwp.notion.site/PASTA-100-NICHOS-PRO-2e7620bdb33e813db5dac38194635f51",
    "wait_time": 20
  }')

JOB_ID=$(echo $RESPONSE | jq -r '.job_id')
echo "Job iniciado: $JOB_ID"

# 2. Aguardar resultado
for i in {1..60}; do
  RESULT=$(curl -s "http://localhost:8000/api/v1/notion/scrape-nichos/result/$JOB_ID")
  STATUS=$(echo $RESULT | jq -r '.success')

  if [ "$STATUS" == "true" ]; then
    echo "✅ Scraping concluído!"
    echo $RESULT | jq '.'
    break
  else
    echo "Aguardando... ($i/60)"
    sleep 5
  fi
done
```

### Exemplo 2: Scraping com Webhook

```bash
curl -X POST "http://localhost:8000/api/v1/notion/scrape-nichos/start" \
  -H "Content-Type: application/json" \
  -d '{
    "notion_url": "https://victorgonwp.notion.site/PASTA-100-NICHOS-PRO-2e7620bdb33e813db5dac38194635f51",
    "wait_time": 20,
    "webhook_url": "https://n8n.example.com/webhook/abc123"
  }'
```

### Exemplo 3: TubeHunt Login

```bash
curl -X POST "http://localhost:8000/api/v1/tubehunt/login-and-scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "wait_time": 15,
    "extract_selector": "h1"
  }' | jq '.'
```

### Exemplo 4: Health Check Completo

```bash
# Notion health
echo "=== Notion Health ==="
curl http://localhost:8000/api/v1/notion/health | jq '.'

echo ""

# TubeHunt health
echo "=== TubeHunt Health ==="
curl http://localhost:8000/api/v1/tubehunt/health | jq '.'
```

---

## Variáveis de Ambiente Obrigatórias

Crie um arquivo `.env` na raiz do projeto:

```env
# TubeHunt Credentials
TUBEHUNT_LOGIN_URL=https://app.tubehunt.io/login
TUBEHUNT_USER=seu_email@example.com
TUBEHUNT_PASSWORD=sua_senha

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Database (opcional)
DATABASE_URL=sqlite:///./scrape_th.db
```

---

## Fluxo Típico de Uso

### Notion Nichos

```
1. POST /scrape-nichos/start
   ↓ (retorna job_id)
2. GET /scrape-nichos/result/{job_id}  [repetir até terminar]
   ↓
3. Webhook callback automático (se configurado)
   ↓
   Resultado com 201 canais de 14 nichos
```

### TubeHunt

```
1. POST /login-and-scrape
   ↓ (login automático)
2. Extração de dados
   ↓
   Resultado imediato
```

---

## Performance e Limites

| Operação | Tempo Médio | Máximo |
|----------|------------|--------|
| Scraping Notion | ~60-90 segundos | 120 segundos |
| Login TubeHunt | ~15-30 segundos | 60 segundos |
| Webhook delivery | < 5 segundos | - |

---

## Suporte e Debugging

### Logs da API

```bash
# Ver logs em tempo real
docker-compose logs -f scraper-api

# Apenas erros
docker-compose logs scraper-api | grep ERROR
```

### Debug de Job

```bash
# Verificar status detalhado
curl "http://localhost:8000/api/v1/notion/scrape-nichos/result/{job_id}" | jq '.error'
```

---

## Changelog

**v1.0 (2026-01-22)**
- ✅ Notion scraping com API interception
- ✅ TubeHunt scraping
- ✅ Webhook callbacks
- ✅ Health checks
- ✅ Headless mode para produção

---

**Última atualização:** 2026-01-22
**Versão:** 1.0.0
