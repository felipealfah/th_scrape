# Guia de Testes Locais - Sistema Assíncrono de Job Queue

## Visão Geral

Este guia fornece instruções passo a passo para testar localmente o sistema assíncrono de job queue antes de fazer deploy em produção.

## Pré-requisitos

- Docker e Docker Compose instalados
- Python 3.10+ (para scripts de teste locais)
- `curl` ou `httpie` para requisições HTTP
- Credenciais TubeHunt válidas no arquivo `.env`

## Passo 1: Preparar o Ambiente Local

### 1.1 Iniciar Docker Compose

```bash
cd /Users/felipefull/Documents/Projetos/scrape_th
docker-compose up -d
```

Aguarde até que ambos os serviços estejam saudáveis:

```bash
docker-compose ps
```

Esperado:
- `scrape-th-api` - Status: Up
- `selenium-chrome` - Status: Up

### 1.2 Verificar Health Check

```bash
curl http://localhost:8000/api/v1/tubehunt/health-check
```

Esperado:
```json
{
  "status": "ok",
  "timestamp": "2026-01-01T22:00:00.000000",
  "version": "1.5",
  "services": {
    "api": "healthy",
    "selenium": "healthy",
    "docker": "healthy"
  },
  "uptime_seconds": 15.5,
  "message": "API está funcionando corretamente com todos os serviços online"
}
```

## Passo 2: Testar o Sistema Assíncrono

### 2.1 Teste Manual com cURL

#### A. Iniciar um Job de Scraping

```bash
curl -X POST http://localhost:8000/api/v1/tubehunt/scrape-channels/start \
  -H "Content-Type: application/json"
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

**Importante**: Anote o `job_id` para os próximos testes.

#### B. Verificar Status (Immediately - Job Ainda Está Enfileirado)

```bash
curl http://localhost:8000/api/v1/tubehunt/scrape-channels/result/550e8400-e29b-41d4-a716-446655440000
```

Esperado (logo após iniciar):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "progress": 0,
  "message": "Job enfileirado",
  "started_at": null
}
```

#### C. Verificar Status (Depois de Alguns Segundos - Processing)

```bash
curl http://localhost:8000/api/v1/tubehunt/scrape-channels/result/550e8400-e29b-41d4-a716-446655440000
```

Esperado (durante processamento):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 35,
  "message": "Scraping iniciado...",
  "started_at": "2026-01-01T22:00:05.000000"
}
```

#### D. Verificar Resultado (Após Conclusão - ~5 minutos)

```bash
curl http://localhost:8000/api/v1/tubehunt/scrape-channels/result/550e8400-e29b-41d4-a716-446655440000
```

Esperado (após conclusão):
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
        "channel_handle": "@example",
        "country": "US",
        "subscribers": "10k",
        "is_verified": true,
        "is_monetized": true,
        "total_views": "1M",
        "views_last_60_days": "100k",
        "average_views_per_video": "5k",
        "time_since_first_video": "há 2 anos",
        "total_videos": "200",
        "outlier_score": "80×",
        "recent_videos": []
      }
    ],
    "total_channels": 1,
    "timestamp": "2026-01-01T22:05:30.000000",
    "error": null
  },
  "execution_time_seconds": 330.5,
  "completed_at": "2026-01-01T22:05:30.000000"
}
```

#### E. Verificar Job Não Encontrado

```bash
curl http://localhost:8000/api/v1/tubehunt/scrape-channels/result/invalid-job-id
```

Esperado:
```json
{
  "detail": "Job não encontrado: invalid-job-id"
}
```
HTTP Status: 404

### 2.2 Teste com Script Automático

Execute o script de testes fornecido:

```bash
python /Users/felipefull/Documents/Projetos/scrape_th/test_async_job_queue.py
```

Este script:
1. Inicia um job de scraping
2. Realiza polling a cada 10 segundos
3. Continua até que o job seja concluído ou falhe
4. Exibe progresso em tempo real
5. Mostra o resultado final ou erro

## Passo 3: Monitorar Logs

### 3.1 Logs da API

```bash
docker-compose logs -f scraper-api
```

Procure por mensagens como:
- `Job criado: <job_id>` - Job foi criado
- `Job atualizado: <job_id> -> processing` - Job iniciou processamento
- `Job completo: <job_id>` - Job completou com sucesso
- `Job falhou: <job_id>` - Job falhou com erro

### 3.2 Logs do Selenium

```bash
docker-compose logs -f selenium-chrome
```

Procure por:
- Atividade do navegador
- Timeouts de conexão
- Erros de carregamento de página

## Passo 4: Testar Múltiplos Jobs em Paralelo

### 4.1 Iniciar Múltiplos Jobs

```bash
# Terminal 1
curl -X POST http://localhost:8000/api/v1/tubehunt/scrape-channels/start

# Terminal 2
curl -X POST http://localhost:8000/api/v1/tubehunt/scrape-channels/start

# Terminal 3
curl -X POST http://localhost:8000/api/v1/tubehunt/scrape-channels/start
```

Anote os job_ids retornados.

### 4.2 Monitorar Progresso de Todos

```bash
# Criar um loop para monitorar todos os jobs
for job_id in job1 job2 job3; do
  echo "=== Job: $job_id ==="
  curl http://localhost:8000/api/v1/tubehunt/scrape-channels/result/$job_id
  echo ""
done
```

## Passo 5: Testar Tratamento de Erros

### 5.1 Credenciais Inválidas

Edite o `.env` com credenciais inválidas e inicie um job:

```bash
curl -X POST http://localhost:8000/api/v1/tubehunt/scrape-channels/start
```

Aguarde alguns segundos e verifique o status:

```bash
curl http://localhost:8000/api/v1/tubehunt/scrape-channels/result/<job_id>
```

Esperado:
```json
{
  "job_id": "<job_id>",
  "status": "failed",
  "error": "Erro ao fazer scraping: Login falhou - credenciais inválidas",
  "failed_at": "2026-01-01T22:10:00.000000"
}
```

### 5.2 Timeout

O script de teste simulará um timeout se o Selenium não responder:

```bash
# No docker-compose.yml, pare o Selenium
docker-compose pause selenium-chrome

# Inicie um job
curl -X POST http://localhost:8000/api/v1/tubehunt/scrape-channels/start

# Aguarde alguns segundos
# Retome o Selenium
docker-compose unpause selenium-chrome

# Verifique o status
curl http://localhost:8000/api/v1/tubehunt/scrape-channels/result/<job_id>
```

## Passo 6: Testar Integração com n8n

### 6.1 Configurar Workflow no n8n

1. Abra o workflow existente no n8n
2. Atualize o endpoint anterior:
   - De: `POST http://localhost:8000/api/v1/tubehunt/scrape-channels`
   - Para: `POST http://localhost:8000/api/v1/tubehunt/scrape-channels/start`

3. Adicione um novo nó HTTP com delay entre requests:
   - Endpoint: `GET http://localhost:8000/api/v1/tubehunt/scrape-channels/result/<job_id>`
   - Implementar polling com retry automático
   - Aguardar até receber `status: "completed"` ou `status: "failed"`

### 6.2 Exemplo com Polling

No n8n, use uma função loop para fazer polling:

```javascript
// Pseudocódigo para n8n
let attempts = 0;
let maxAttempts = 60; // 10 minutos com interval de 10 segundos

while (attempts < maxAttempts) {
  const response = await fetch(`http://localhost:8000/api/v1/tubehunt/scrape-channels/result/${jobId}`);
  const data = await response.json();

  if (data.status === "completed") {
    return data.result;
  }

  if (data.status === "failed") {
    throw new Error(data.error);
  }

  // Aguardar 10 segundos
  await new Promise(resolve => setTimeout(resolve, 10000));
  attempts++;
}

throw new Error("Job timeout após 10 minutos");
```

## Passo 7: Cleanup

### 7.1 Parar Docker Compose

```bash
docker-compose down
```

### 7.2 Limpar Volumes (Opcional)

```bash
docker-compose down -v
```

## Checklist de Validação

- [ ] Health check retorna status "ok"
- [ ] POST /scrape-channels/start retorna imediatamente com job_id
- [ ] GET /scrape-channels/result/{job_id} retorna "pending" imediatamente após POST
- [ ] GET /scrape-channels/result/{job_id} retorna "processing" durante execução
- [ ] GET /scrape-channels/result/{job_id} retorna "completed" com dados após conclusão
- [ ] Job_id inválido retorna HTTP 404
- [ ] Múltiplos jobs podem rodar em paralelo
- [ ] Erros de login são capturados e reportados
- [ ] Logs mostram execução correta do job
- [ ] n8n consegue fazer polling sem timeout

## Troubleshooting

### Problema: Docker containers não iniciam

```bash
# Verificar logs
docker-compose logs

# Reconstruir imagens
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Problema: Selenium não conecta

```bash
# Verificar status
docker-compose ps

# Reiniciar Selenium
docker-compose restart selenium-chrome
```

### Problema: Job fica em "processing" indefinidamente

```bash
# Verificar logs da API
docker-compose logs scraper-api

# Pode indicar erro silencioso na thread de background
# Verifique credenciais no .env
```

### Problema: Credenciais inválidas

```bash
# Verificar arquivo .env
cat .env

# Validar credenciais TubeHunt
# Atualizar com credenciais corretas
```

## Notas Importantes

1. **Tempo de Execução**: O scraping pode levar 5-10 minutos dependendo da quantidade de canais
2. **Limite de Sessões**: Configurado para máximo 5 sessões Selenium simultâneas
3. **Memória**: Cada sessão Selenium consome ~300-500MB de RAM
4. **Shared Memory**: Docker Compose aloca 2GB para Selenium
5. **Job Storage**: Jobs são armazenados em memória (serão perdidos ao reiniciar API)

## Próximos Passos

1. ✅ Validar testes locais
2. ✅ Verificar logs e tratamento de erros
3. ✅ Testar com n8n
4. ⏳ Deploy para Render (produção)
5. ⏳ Monitorar em produção por 24h
6. ⏳ Validar resolução do timeout no n8n
