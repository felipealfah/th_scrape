# Quick Start - Testes Locais do Sistema Assíncrono

Este documento fornece um guia rápido para testar o sistema assíncrono de job queue sem detalhes extensos.

## Pré-requisitos

- Docker Compose rodando: `docker-compose ps`
- Python 3.10+ disponível
- Credenciais TubeHunt configuradas no `.env`

## Teste Rápido em 5 Minutos

### 1. Verificar se API está rodando

```bash
curl http://localhost:8000/api/health
```

Esperado: `{"status":"healthy","message":"Scrape TH API is running"}`

### 2. Iniciar um Job

```bash
curl -X POST http://localhost:8000/api/v1/tubehunt/scrape-channels/start
```

Esperado:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Job enfileirado com sucesso",
  "created_at": "2026-01-01T22:00:00.000000"
}
```

**Anote o job_id!**

### 3. Verificar Status Imediatamente

```bash
curl http://localhost:8000/api/v1/tubehunt/scrape-channels/result/550e8400-e29b-41d4-a716-446655440000
```

Esperado (segundos após iniciar):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 0,
  "message": "Iniciando scraping...",
  "started_at": "2026-01-01T22:00:05.000000"
}
```

### 4. Script Automático (Recomendado)

```bash
python test_job_queue_quick.py
```

Este script:
- Inicia um job
- Faz polling automático a cada 5 segundos
- Exibe progresso em tempo real
- Aguarda até conclusão (5-10 minutos)

## O que Cada Status Significa

| Status | Significado | Ação |
|--------|------------|------|
| `pending` | Job está na fila, ainda não iniciou | Aguarde alguns segundos |
| `processing` | Scraping em andamento | Continue fazendo polling |
| `completed` | Scraping concluído com sucesso | Ver resultado em `data.result` |
| `failed` | Erro durante scraping | Ver mensagem de erro em `data.error` |

## Exemplo de Resultado Completo (Status = completed)

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "success": true,
    "channels": [
      {
        "channel_name": "Example Channel",
        "channel_link": "/channel/UCxxx",
        "subscribers": "10k",
        "total_views": "1M",
        "recent_videos": []
      }
    ],
    "total_channels": 50,
    "timestamp": "2026-01-01T22:05:30.000000",
    "error": null
  },
  "execution_time_seconds": 330.5,
  "completed_at": "2026-01-01T22:05:30.000000"
}
```

## Testar com Job ID Inválido

```bash
curl http://localhost:8000/api/v1/tubehunt/scrape-channels/result/invalid-job-id
```

Esperado: HTTP 404 com mensagem `{"detail": "Job não encontrado: invalid-job-id"}`

## Monitorar Logs em Tempo Real

### API Logs

```bash
docker-compose logs -f scraper-api
```

Procure por:
- `Job criado: <job_id>` ✓
- `Job atualizado: <job_id> -> processing` ✓
- `Job completo: <job_id>` ✓

### Selenium Logs

```bash
docker-compose logs -f selenium-chrome
```

## Troubleshooting

### Erro: "Connection refused"
API não está rodando:
```bash
docker-compose up -d
docker-compose ps
```

### Erro: Job fica em "processing" por mais de 15 minutos
Pode ser timeout do Selenium:
```bash
docker-compose logs scraper-api | tail -50
```

Verifique credenciais em `.env`:
```bash
cat .env
```

### Erro: "Not Found" (404) ao chamar endpoint

Certifique-se de usar o endpoint correto:
```
POST   http://localhost:8000/api/v1/tubehunt/scrape-channels/start
GET    http://localhost:8000/api/v1/tubehunt/scrape-channels/result/{job_id}
```

## Próximos Passos

1. ✅ Testar job queue localmente
2. ⏳ Validar com n8n (ver ASYNC_TESTING_GUIDE.md)
3. ⏳ Deploy para Render (produção)
4. ⏳ Monitorar por 24h

## Referências Completas

Para guia completo com:
- Múltiplos jobs em paralelo
- Teste de tratamento de erros
- Integração com n8n
- Deploy em produção

Veja: [ASYNC_TESTING_GUIDE.md](./ASYNC_TESTING_GUIDE.md)
