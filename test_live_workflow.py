#!/usr/bin/env python3
"""Live test of async workflow - monitors job completion in real time"""

import requests
import time
import json
from datetime import datetime

API_URL = "http://localhost:8000/api/v1/tubehunt"

print("\n" + "="*70)
print("TESTE LIVE - FLUXO ASSÍNCRONO COMPLETO")
print("="*70)

# Step 1: Start job
print("\n[1/4] Iniciando job de scraping...")
response = requests.post(f"{API_URL}/scrape-channels/start", timeout=5)
result = response.json()

job_id = result['job_id']
print(f"  ✅ Job criado: {job_id}")
print(f"  Status inicial: {result['status']}")
print(f"  Timestamp: {result['created_at']}")

# Step 2: Check status progression
print(f"\n[2/4] Fazendo polling... (máximo 10 minutos)")
print(f"{'Tempo':<10} {'Status':<12} {'Progresso':<12} {'Mensagem':<40}")
print("-" * 75)

start_time = time.time()
last_status = None
poll_count = 0

while True:
    elapsed = time.time() - start_time
    poll_count += 1

    response = requests.get(f"{API_URL}/scrape-channels/result/{job_id}", timeout=5)
    data = response.json()

    status = data.get('status')
    progress = data.get('progress', 0)
    message = data.get('message', '')[:35]

    # Only print on status change
    if status != last_status or poll_count <= 5:
        time_str = f"{elapsed:.0f}s"
        print(f"{time_str:<10} {status:<12} {progress:>3}%          {message:<40}")
        last_status = status

    if status == 'completed':
        print(f"\n✅ JOB COMPLETADO EM {elapsed:.1f}s")
        break
    elif status == 'failed':
        print(f"\n❌ JOB FALHOU: {data.get('error')}")
        break

    time.sleep(10 if elapsed < 30 else 30)

    if elapsed > 600:  # 10 minutos
        print(f"\n⚠️  Timeout após {elapsed:.0f}s")
        break

# Step 3: Show final result
print(f"\n[3/4] Resultado final:")
if status == 'completed' and 'result' in data:
    result_data = data['result']
    print(f"  Sucesso: {result_data.get('success')}")
    print(f"  Canais extraídos: {result_data.get('total_channels', 0)}")
    if result_data.get('channels'):
        print(f"  Primeiro canal: {result_data['channels'][0].get('channel_name', 'N/A')}")
    if 'execution_time_seconds' in data:
        print(f"  Tempo de execução: {data['execution_time_seconds']:.1f}s")

# Step 4: Validation
print(f"\n[4/4] Validação:")
checks = [
    ("POST retornou job_id válido", job_id is not None and len(job_id) > 0),
    ("Status mudou para 'processing'", status in ['processing', 'completed', 'failed']),
    ("Job completou ou falhou", status in ['completed', 'failed']),
    ("Resultado contém dados", status == 'completed' and result_data.get('channels', [])),
]

all_passed = True
for check_name, passed in checks:
    status_str = "✅" if passed else "❌"
    print(f"  {status_str} {check_name}")
    if not passed:
        all_passed = False

print("\n" + "="*70)
if all_passed and status == 'completed':
    print("🎉 TESTE COMPLETO - TUDO FUNCIONANDO!")
elif all_passed:
    print("⚠️  Teste parcial - job falhou ou timeout")
else:
    print("❌ TESTE FALHOU - Algo deu errado")
print("="*70 + "\n")
