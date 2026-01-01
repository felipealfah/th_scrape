# Health Check API - Guia Completo

## 📌 Visão Geral

O endpoint de health check permite verificar se a API e seus serviços estão funcionando corretamente. Útil para monitoramento, balanceamento de carga e alertas.

## 🔗 Endpoint

```
GET /api/v1/tubehunt/health
```

**Base URL:** `http://localhost:8000` (local) ou `http://<seu-servidor>` (produção)

## 📋 Resposta

### Status 200 OK (Sempre)

```json
{
  "status": "ok",
  "timestamp": "2026-01-01T20:00:00.000000",
  "version": "1.5",
  "services": {
    "api": "healthy",
    "selenium": "healthy",
    "docker": "running",
    "environment": "healthy"
  },
  "uptime_seconds": 3600.5,
  "message": "API está funcionando corretamente com todos os serviços online"
}
```

## 🎯 Interpretação dos Status

### Status Geral

| Status | Significado | Ação |
|--------|-------------|------|
| `ok` | Todos os serviços funcionam normalmente | ✅ API pronta para uso |
| `degraded` | Alguns serviços têm problemas, mas API funciona | ⚠️ Verificar serviços degradados |
| `error` | Erro crítico, API indisponível | ❌ Investigar imediatamente |

### Status dos Serviços

#### API (`api`)
- `healthy` - API respondendo normalmente
- `error` - Erro crítico na API

#### Selenium (`selenium`)
- `healthy` - WebDriver remoto acessível e funcionando
- `warning` - WebDriver não respondeu completamente
- `error` - WebDriver indisponível ou falha de conexão

#### Docker (`docker`)
- `running` - Detectado que está rodando em Docker
- `local` - Rodando localmente (não em Docker)
- `unknown` - Não foi possível determinar

#### Environment (`environment`)
- `healthy` - Todas as variáveis de ambiente necessárias carregadas
- `warning` - Algumas variáveis faltando
- `error` - Variáveis críticas não configuradas

## 📊 Exemplos de Uso

### 1. Verificação Simples com curl

```bash
curl http://localhost:8000/api/v1/tubehunt/health
```

### 2. Verificação com Formatação JSON

```bash
curl http://localhost:8000/api/v1/tubehunt/health | python3 -m json.tool
```

### 3. Verificação via Python

```python
import requests
import json

response = requests.get("http://localhost:8000/api/v1/tubehunt/health")
data = response.json()

print(f"Status: {data['status']}")
print(f"Uptime: {data['uptime_seconds']:.2f}s")
print(f"Mensagem: {data['message']}")

# Verificar serviços individuais
for service, status in data['services'].items():
    print(f"  {service}: {status}")
```

### 4. Verificação com Monitoramento

```python
import requests
import time

def monitor_api(interval=30, max_attempts=10):
    """Monitora a API a cada 'interval' segundos"""
    attempts = 0

    while attempts < max_attempts:
        try:
            response = requests.get(
                "http://localhost:8000/api/v1/tubehunt/health",
                timeout=5
            )
            data = response.json()

            timestamp = data['timestamp']
            status = data['status']
            uptime = data['uptime_seconds']

            print(f"[{timestamp}] Status: {status} | Uptime: {uptime:.0f}s")

            # Alertar se degraded
            if status == "degraded":
                print(f"⚠️  ALERTA: {data['message']}")

            # Alertar se error
            if status == "error":
                print(f"❌ ERRO: {data['message']}")

        except Exception as e:
            print(f"❌ Erro ao conectar: {e}")

        attempts += 1
        time.sleep(interval)

# Executar monitoramento
if __name__ == "__main__":
    monitor_api(interval=30, max_attempts=10)
```

### 5. Verificação em Docker

```bash
# Verificar saúde do serviço no Docker
docker-compose exec scraper-api curl http://localhost:8000/api/v1/tubehunt/health

# Ou com formatação
docker-compose exec scraper-api bash -c \
  'curl http://localhost:8000/api/v1/tubehunt/health | python3 -m json.tool'
```

## ⚙️ Interpretando Respostas

### Cenário 1: Tudo OK

```json
{
  "status": "ok",
  "services": {
    "api": "healthy",
    "selenium": "healthy",
    "docker": "running",
    "environment": "healthy"
  },
  "message": "API está funcionando corretamente com todos os serviços online"
}
```

✅ **Ação:** API pronta para produção. Todos os endpoints podem ser usados normalmente.

---

### Cenário 2: Selenium com Problemas

```json
{
  "status": "degraded",
  "services": {
    "api": "healthy",
    "selenium": "error",
    "docker": "running",
    "environment": "healthy"
  },
  "message": "API funcionando, mas alguns serviços têm problemas: Erro ao verificar Selenium: Connection refused"
}
```

⚠️ **Ação:**
- Verificar se o container Selenium está rodando: `docker-compose ps`
- Reiniciar Selenium: `docker-compose restart selenium-chrome`
- Verificar logs: `docker-compose logs selenium-chrome`

---

### Cenário 3: Variáveis de Ambiente Faltando

```json
{
  "status": "degraded",
  "services": {
    "api": "healthy",
    "selenium": "healthy",
    "docker": "running",
    "environment": "warning"
  },
  "message": "API funcionando, mas alguns serviços têm problemas: Variáveis de ambiente incompletas"
}
```

⚠️ **Ação:**
- Verificar arquivo `.env`
- Garantir que existem: `TUBEHUNT_URL`, `TUBEHUNT_USER`, `TUBEHUNT_PASSWORD`
- Reiniciar API: `docker-compose restart scraper-api`

---

### Cenário 4: Erro Crítico

```json
{
  "status": "error",
  "services": {
    "api": "error",
    "selenium": "unknown",
    "docker": "unknown",
    "environment": "unknown"
  },
  "message": "Erro crítico no health check: Module 'app' not found"
}
```

❌ **Ação:**
- Verificar logs da API: `docker-compose logs scraper-api`
- Verificar se dependências estão instaladas: `pip install -r requirements.txt`
- Reiniciar tudo: `docker-compose restart`

## 📈 Métricas Disponíveis

### Uptime (uptime_seconds)

Tempo em segundos desde que a API foi iniciada.

```python
uptime = data['uptime_seconds']
uptime_hours = uptime / 3600
uptime_minutes = (uptime % 3600) / 60

print(f"Uptime: {int(uptime_hours)}h {int(uptime_minutes)}m")
```

### Timestamp

Hora exata do health check (UTC).

```python
from datetime import datetime

timestamp_str = data['timestamp']
timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
print(f"Hora do check: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
```

## 🔄 Ciclo de Vida da API

1. **Startup (0-5s)** - API iniciando, serviços sendo carregados
   - Status pode ser `degraded` até estar completamente pronto

2. **Running** - API normal
   - Status deve ser `ok`
   - Uptime aumenta continuamente

3. **Restart** - Uptime volta a 0
   - Pode ser reinício automático ou manual
   - Services podem estar verificando durante restart

## 🚀 Produção

### Exemplo de Health Check em Produção

```bash
# Verificação rápida
curl -f http://seu-api.com/api/v1/tubehunt/health > /dev/null && echo "API OK" || echo "API DOWN"

# Com timeout
curl -f --max-time 5 http://seu-api.com/api/v1/tubehunt/health > /dev/null && echo "API OK" || echo "API DOWN"

# Em um script cron (a cada 5 minutos)
*/5 * * * * curl -f --max-time 5 http://seu-api.com/api/v1/tubehunt/health || mail -s "API DOWN" admin@example.com
```

### Exemplo com Prometheus/Grafana

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'tubehunt-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/v1/tubehunt/health'
    scrape_interval: 30s
```

## 🔗 Endpoints Relacionados

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/tubehunt/health` | GET | Health check completo |
| `/api/health` | GET | Health check básico |
| `/docs` | GET | Documentação Swagger |
| `/api/v1/tubehunt/login-and-scrape` | POST | Realizar scraping |

## 📞 Troubleshooting

### "Connection refused"
- A API não está rodando
- Iniciar: `docker-compose up -d` ou `python -m app.main`

### "Timeout"
- API está lenta ou indisponível
- Aumentar timeout do curl: `curl --max-time 30`

### "Status degraded mas não vejo erro"
- Verificar os serviços individuais na resposta
- Ver logs: `docker-compose logs scraper-api`

### "Selenium error"
- Verificar se Selenium está rodando: `docker-compose ps`
- Reiniciar: `docker-compose restart selenium-chrome`

---

**Última atualização:** 2026-01-01
**Versão:** 1.5
