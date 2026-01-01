#!/usr/bin/env python3
"""
Script para testar o endpoint de health check da API
"""
import requests
import json
from datetime import datetime

def test_health_check():
    """Testa o endpoint /api/v1/tubehunt/health"""

    print("\n" + "="*60)
    print("TESTE: Health Check da API")
    print("="*60)

    url = "http://localhost:8000/api/v1/tubehunt/health"

    try:
        print(f"\n📍 Fazendo requisição para: {url}")
        response = requests.get(url, timeout=10)

        print(f"📊 Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            print("\n✅ RESPOSTA RECEBIDA COM SUCESSO\n")

            # Exibir dados estruturados
            print(f"Status Geral:        {data.get('status', 'N/A').upper()}")
            print(f"Versão da API:       {data.get('version', 'N/A')}")
            print(f"Timestamp:           {data.get('timestamp', 'N/A')}")
            print(f"Uptime (segundos):   {data.get('uptime_seconds', 'N/A'):.2f}s")
            print(f"\nMensagem:\n  {data.get('message', 'N/A')}")

            print("\n📋 Status dos Serviços:")
            services = data.get('services', {})
            for service, status in services.items():
                icon = "✅" if status == "healthy" else "⚠️" if "warning" in status or status == "degraded" else "❌"
                print(f"  {icon} {service.capitalize():20} -> {status}")

            # Validar resposta
            print("\n🔍 Validações:")
            validations = [
                ("Status presente", "status" in data),
                ("Timestamp presente", "timestamp" in data),
                ("Versão presente", "version" in data),
                ("Serviços presentes", "services" in data),
                ("Uptime presente", "uptime_seconds" in data),
                ("Mensagem presente", "message" in data),
                ("Status é ok/degraded/error", data.get("status") in ["ok", "degraded", "error"]),
            ]

            for validation_name, result in validations:
                icon = "✅" if result else "❌"
                print(f"  {icon} {validation_name}")

            # JSON completo
            print("\n📝 Resposta completa:")
            print(json.dumps(data, indent=2, default=str))

            all_passed = all(result for _, result in validations)
            if all_passed:
                print("\n✅ TODOS OS TESTES PASSARAM!")
                return True
            else:
                print("\n❌ ALGUNS TESTES FALHARAM")
                return False
        else:
            print(f"\n❌ Erro: Status code {response.status_code}")
            print(f"Resposta: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("\n❌ Erro de conexão: Não foi possível conectar ao servidor")
        print("   Verifique se a API está rodando em http://localhost:8000")
        return False
    except requests.exceptions.Timeout:
        print("\n❌ Erro: Requisição expirou (timeout)")
        return False
    except Exception as e:
        print(f"\n❌ Erro inesperado: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_health_check()
    exit(0 if success else 1)
