# Como Testar Localmente - Guia Prático

## Resumo Executivo

Você implementou com sucesso um sistema assíncrono de job queue para resolver o problema de timeout do n8n. Agora vamos testar localmente antes de fazer deploy em produção.

**Tempo total estimado**: 5-10 minutos

## O Que Mudou

Antes (Síncrono - Problemático):
```
POST /scrape-channels → API bloqueia por 5-10 minutos → n8n timeout ❌
```

Depois (Assíncrono - Resolvido):
```
POST /scrape-channels/start → API retorna em < 100ms com job_id ✅
GET /scrape-channels/result/{job_id} → Polling sem timeout ✅
```

## Passo 1: Verificar Docker Compose

Verifique se os containers estão rodando:

```bash
docker-compose ps
```

Esperado:
```
NAME              STATUS      PORTS
scrape-th-api     Up          0.0.0.0:8000->8000/tcp
selenium-chrome   Up          0.0.0.0:4444->4444/tcp
```

Se não estão rodando, inicie:
```bash
docker-compose up -d
```

## Passo 2: Teste Rápido com Script

Execute este simples script que faz todo o teste automaticamente:

```bash
python test_job_queue_quick.py
```

Isso vai:
1. ✅ Iniciar um job de scraping
2. ✅ Fazer polling automático a cada 5 segundos
3. ✅ Exibir progresso em tempo real
4. ✅ Aguardar até conclusão (5-10 minutos)
5. ✅ Exibir resultado final

**Esperado**:
```
============================================================
TESTE DO SISTEMA ASSÍNCRONO - JOB QUEUE
============================================================

1️⃣  Iniciando job de scraping...
   Job ID: a24992f9-a314-480d-a691-07f0f58f93e1
   Status: pending
   Message: Job enfileirado com sucesso

2️⃣  Fazendo polling do status...
   [     0s | Tentativa  1] Status:    pending | Progresso:   0%
   [     5s | Tentativa  2] Status: processing | Progresso:   0%
   [    30s | Tentativa  6] Status: processing | Progresso:  25%
   [    60s | Tentativa 12] Status: processing | Progresso:  50%
   [   180s | Tentativa 36] Status: processing | Progresso:  85%
   [   300s | Tentativa 60] Status:  completed | Progresso: 100%

✅ JOB COMPLETADO!
   Tempo total: 330.1s
   Canais extraídos: 50
   Sucesso: true
   Tempo de execução: 330.5s
```

## Passo 3: Verificar Logs (Opcional)

Em outro terminal, acompanhe os logs em tempo real:

```bash
docker-compose logs -f scraper-api
```

Procure por linhas como:
- `Job criado: a24992f9-a314-480d-a691-07f0f58f93e1`
- `Job atualizado: ... -> processing`
- `Job completo: ...`

## Passo 4: Teste Manual com cURL (Opcional)

Se preferir testar manualmente:

### 4.1 Iniciar Job

```bash
curl -X POST http://localhost:8000/api/v1/tubehunt/scrape-channels/start
```

Copie o `job_id` do resultado.

### 4.2 Verificar Status (Repetir várias vezes)

```bash
curl http://localhost:8000/api/v1/tubehunt/scrape-channels/result/a24992f9-a314-480d-a691-07f0f58f93e1
```

**Status Pending** (logo após iniciar):
```json
{
  "job_id": "a24992f9-a314-480d-a691-07f0f58f93e1",
  "status": "pending",
  "progress": 0,
  "message": "Job enfileirado",
  "started_at": null
}
```

**Status Processing** (alguns segundos depois):
```json
{
  "job_id": "a24992f9-a314-480d-a691-07f0f58f93e1",
  "status": "processing",
  "progress": 35,
  "message": "Iniciando scraping...",
  "started_at": "2026-01-01T22:00:05.000000"
}
```

**Status Completed** (após 5-10 minutos):
```json
{
  "job_id": "a24992f9-a314-480d-a691-07f0f58f93e1",
  "status": "completed",
  "result": {
    "success": true,
    "channels": [...],
    "total_channels": 50,
    "timestamp": "2026-01-01T22:05:30.000000",
    "error": null
  },
  "execution_time_seconds": 330.5,
  "completed_at": "2026-01-01T22:05:30.000000"
}
```

## Passo 5: Monitorar Múltiplos Jobs (Opcional)

Você pode iniciar múltiplos jobs em paralelo:

```bash
# Terminal 1
curl -X POST http://localhost:8000/api/v1/tubehunt/scrape-channels/start

# Terminal 2
curl -X POST http://localhost:8000/api/v1/tubehunt/scrape-channels/start

# Terminal 3
curl -X POST http://localhost:8000/api/v1/tubehunt/scrape-channels/start
```

A API suporta até 5 jobs simultâneos.

## ✅ Checklist de Validação

Após completar os testes, marque:

- [ ] Docker Compose está rodando (2 containers)
- [ ] `python test_job_queue_quick.py` executa sem erros
- [ ] POST retorna em < 100ms
- [ ] GET retorna status "pending" primeiro
- [ ] GET retorna status "processing" segundos depois
- [ ] GET retorna status "completed" após 5-10 minutos
- [ ] Resultado contém canais extraídos
- [ ] Logs mostram mensagens de job criado, processando, completo
- [ ] API não bloqueia durante scraping
- [ ] Posso fazer polling enquanto job está processando

Se todos os itens foram marcados ✅, está pronto para deploy!

## Próximo Passo: Deploy em Produção

Após validar localmente:

```bash
git push origin main
```

Render detectará automaticamente e fará deploy da nova versão com o sistema assíncrono.

## Troubleshooting Rápido

### Problema: "Connection refused"
```bash
docker-compose up -d
```

### Problema: Script trava indefinidamente
Verifique credenciais no `.env`:
```bash
cat .env | grep -E "url_login|user|password"
```

### Problema: Job fica "processing" por >15 minutos
Verifique logs:
```bash
docker-compose logs scraper-api | tail -50
```

### Problema: Job falha com erro de credenciais
Atualize `.env` com credenciais TubeHunt válidas

## Documentação Completa

Para informações detalhadas, consulte:

- **LOCAL_TESTING_QUICK_START.md** - Referência rápida
- **ASYNC_TESTING_GUIDE.md** - Guia completo com todos os detalhes
- **TESTING_SUMMARY.md** - Overview técnico da implementação

## Perguntas Frequentes

### P: Quanto tempo leva o scraping?
R: Típicamente 5-10 minutos dependendo de quantos canais estão no site.

### P: O que acontece se interromper o script?
R: O job continua rodando em background. Use o job_id para consultar status depois.

### P: Posso fazer múltiplos requests simultaneamente?
R: Sim! A API suporta até 5 jobs em paralelo.

### P: O resultado é armazenado em banco de dados?
R: Não, em memória. Será perdido se API reiniciar. Para Fase 3, podemos adicionar persistência.

### P: Como integrar com n8n?
R: Use o job_id para fazer polling no workflow. Ver **ASYNC_TESTING_GUIDE.md** para exemplo.

---

**Dúvidas?** Consulte a documentação completa ou os arquivos de exemplo de teste.

**Próximo passo**: Executar `python test_job_queue_quick.py` e validar que está tudo funcionando! 🚀
