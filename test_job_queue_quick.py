#!/usr/bin/env python3
"""Quick test for async job queue - simplified version"""

import requests
import time
import json

API_URL = "http://localhost:8000/api/v1/tubehunt"

print("\n" + "="*60)
print("TESTE DO SISTEMA ASSÍNCRONO - JOB QUEUE")
print("="*60 + "\n")

# Test 1: Start a job
print("1️⃣  Iniciando job de scraping...")
response = requests.post(f"{API_URL}/scrape-channels/start")
result = response.json()
job_id = result['job_id']
print(f"   Job ID: {job_id}")
print(f"   Status: {result['status']}")
print(f"   Message: {result['message']}\n")

# Test 2: Polling with intervals
print("2️⃣  Fazendo polling do status... (interrompa com Ctrl+C)")
print("   Aguardando resultado (pode levar 5-10 minutos)...\n")

start_time = time.time()
poll_count = 0
last_progress = -1

try:
    while True:
        response = requests.get(f"{API_URL}/scrape-channels/result/{job_id}")
        data = response.json()

        poll_count += 1
        elapsed = time.time() - start_time
        status = data.get('status')
        progress = data.get('progress', 0)

        # Only print on status change or progress change
        if status != 'processing' or progress != last_progress or poll_count <= 3:
            print(f"   [{elapsed:>6.0f}s | Tentativa {poll_count:>2}] Status: {status:>10} | Progresso: {progress:>3}%")
            last_progress = progress

        if status == 'completed':
            print(f"\n✅ JOB COMPLETADO!")
            print(f"   Tempo total: {elapsed:.1f}s")

            if 'result' in data and data['result']:
                result_data = data['result']
                print(f"   Canais extraídos: {result_data.get('total_channels', 0)}")
                print(f"   Sucesso: {result_data.get('success')}")

            if 'execution_time_seconds' in data:
                print(f"   Tempo de execução: {data['execution_time_seconds']:.1f}s")
            break

        elif status == 'failed':
            print(f"\n❌ JOB FALHOU!")
            print(f"   Erro: {data.get('error')}")
            break

        # Wait before next poll
        time.sleep(5)

except KeyboardInterrupt:
    print(f"\n\n⚠️  Teste interrompido pelo usuário")
    print(f"   Job ID para referência: {job_id}")

print("\n" + "="*60 + "\n")
