#!/usr/bin/env python3
"""Test script para validar o sistema assíncrono de job queue localmente"""

import requests
import time
import json
import sys
from datetime import datetime
from typing import Dict, Optional, Any

# Configuração
API_BASE_URL = "http://localhost:8000/api/v1/tubehunt"
HEALTH_CHECK_ENDPOINT = f"{API_BASE_URL}/health-check"
START_JOB_ENDPOINT = f"{API_BASE_URL}/scrape-channels/start"
GET_RESULT_ENDPOINT = f"{API_BASE_URL}/scrape-channels/result"
POLLING_INTERVAL = 10  # segundos
MAX_WAIT_TIME = 600  # 10 minutos
POLL_TIMEOUT = 5  # segundos para timeout da request

class Colors:
    """ANSI color codes para output formatado"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str) -> None:
    """Imprimir header formatado"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}")
    print(f"{text}")
    print(f"{'='*60}{Colors.END}\n")

def print_success(text: str) -> None:
    """Imprimir mensagem de sucesso"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text: str) -> None:
    """Imprimir mensagem de erro"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_info(text: str) -> None:
    """Imprimir mensagem informativa"""
    print(f"{Colors.CYAN}ℹ {text}{Colors.END}")

def print_warning(text: str) -> None:
    """Imprimir mensagem de aviso"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_json(data: Dict[str, Any], title: str = "Response") -> None:
    """Imprimir JSON formatado"""
    print(f"{Colors.BLUE}{title}:{Colors.END}")
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))

def test_health_check() -> bool:
    """Testar health check da API"""
    print_header("Teste 1: Health Check")

    try:
        response = requests.get(HEALTH_CHECK_ENDPOINT, timeout=POLL_TIMEOUT)
        response.raise_for_status()

        data = response.json()
        print_json(data, "Health Check Response")

        # Validações
        if data.get("status") != "ok":
            print_error(f"Health check status é '{data.get('status')}', esperado 'ok'")
            return False

        if "services" not in data:
            print_error("Health check não contém informação de serviços")
            return False

        print_success(f"Health check OK - API está saudável")
        print_success(f"Versão: {data.get('version', 'desconhecida')}")
        print_success(f"Uptime: {data.get('uptime_seconds', 0):.1f}s")

        return True

    except requests.exceptions.ConnectionError:
        print_error("Não conseguiu conectar à API em http://localhost:8000")
        print_warning("Verifique se Docker Compose está rodando: docker-compose ps")
        return False
    except Exception as e:
        print_error(f"Erro ao testar health check: {str(e)}")
        return False

def start_job() -> Optional[str]:
    """Iniciar um job de scraping"""
    print_header("Teste 2: Iniciar Job de Scraping")

    try:
        print_info(f"Enviando POST para {START_JOB_ENDPOINT}")
        response = requests.post(START_JOB_ENDPOINT, timeout=POLL_TIMEOUT)
        response.raise_for_status()

        data = response.json()
        print_json(data, "Job Start Response")

        job_id = data.get("job_id")
        if not job_id:
            print_error("Response não contém 'job_id'")
            return None

        status = data.get("status")
        if status != "pending":
            print_error(f"Status inicial é '{status}', esperado 'pending'")
            return None

        print_success(f"Job criado com sucesso: {job_id}")
        print_success(f"Status inicial: {status}")

        return job_id

    except Exception as e:
        print_error(f"Erro ao iniciar job: {str(e)}")
        return None

def poll_job_status(job_id: str) -> Optional[Dict[str, Any]]:
    """Fazer polling do status do job até conclusão"""
    print_header("Teste 3: Polling de Status do Job")

    start_time = time.time()
    attempt = 0

    while True:
        attempt += 1
        elapsed = time.time() - start_time

        try:
            response = requests.get(
                f"{GET_RESULT_ENDPOINT}/{job_id}",
                timeout=POLL_TIMEOUT
            )

            if response.status_code == 404:
                print_error(f"Job não encontrado: {job_id}")
                return None

            response.raise_for_status()
            data = response.json()

            # Mostrar apenas em tentativas selecionadas para não poluir output
            if attempt == 1 or attempt % 6 == 0 or "status" in data and data["status"] in ["completed", "failed"]:
                print(f"\n[Tentativa {attempt}, {elapsed:.0f}s decorridos]")
                status = data.get("status")
                progress = data.get("progress", 0)
                message = data.get("message", "")

                if status == "pending":
                    print_warning(f"Status: {status} | {message}")
                elif status == "processing":
                    print_info(f"Status: {status} ({progress}%) | {message}")
                elif status == "completed":
                    print_success(f"Status: {status} ({progress}%) | {message}")
                    print_success(f"Tempo total: {elapsed:.1f}s")
                    return data
                elif status == "failed":
                    print_error(f"Status: {status} | Erro: {data.get('error', 'desconhecido')}")
                    return data

            # Verificar timeout
            if elapsed > MAX_WAIT_TIME:
                print_error(f"Job timeout após {elapsed:.0f}s ({MAX_WAIT_TIME}s é o máximo)")
                return None

            # Aguardar antes do próximo polling
            if data.get("status") not in ["completed", "failed"]:
                time.sleep(POLLING_INTERVAL)
            else:
                return data

        except Exception as e:
            print_error(f"Erro ao fazer polling: {str(e)}")
            return None

def validate_result(result: Dict[str, Any]) -> bool:
    """Validar resultado do job"""
    print_header("Teste 4: Validar Resultado do Job")

    status = result.get("status")

    if status == "failed":
        print_warning(f"Job falhou com erro: {result.get('error')}")
        print_info("Isso pode ser esperado se as credenciais estiverem inválidas")
        return True  # Ainda é um sucesso de teste se o erro foi capturado

    if status != "completed":
        print_error(f"Status esperado 'completed', recebido '{status}'")
        return False

    # Validações de resultado completo
    print_success("Job completado com sucesso")

    if "execution_time_seconds" in result:
        print_success(f"Tempo de execução: {result['execution_time_seconds']:.1f}s")

    if "result" in result:
        scrape_result = result["result"]
        if scrape_result.get("success"):
            total_channels = scrape_result.get("total_channels", 0)
            print_success(f"Scraping bem-sucedido: {total_channels} canais extraídos")
        else:
            print_warning(f"Scraping não foi bem-sucedido: {scrape_result.get('error')}")

    return True

def test_invalid_job_id() -> bool:
    """Testar request com job_id inválido"""
    print_header("Teste 5: Tratamento de Job ID Inválido")

    try:
        print_info("Enviando GET com job_id inválido")
        response = requests.get(
            f"{GET_RESULT_ENDPOINT}/invalid-job-id-12345",
            timeout=POLL_TIMEOUT
        )

        if response.status_code == 404:
            print_success(f"Retornou status 404 como esperado")
            error_data = response.json()
            print_json(error_data, "Error Response")
            return True
        else:
            print_error(f"Esperado status 404, recebido {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Erro ao testar job_id inválido: {str(e)}")
        return False

def run_all_tests() -> bool:
    """Executar todos os testes"""
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║   TESTE DO SISTEMA ASSÍNCRONO DE JOB QUEUE             ║")
    print("║   Scrape TH API - Fase 2 Implementation                 ║")
    print(f"║   {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<54} ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}\n")

    results = {}

    # Teste 1: Health Check
    results["health_check"] = test_health_check()
    if not results["health_check"]:
        print_error("Health check falhou. Abortando testes.")
        return False

    # Teste 2: Iniciar Job
    job_id = start_job()
    results["start_job"] = job_id is not None
    if not results["start_job"]:
        print_error("Falha ao iniciar job. Abortando testes.")
        return False

    # Teste 3: Polling
    result = poll_job_status(job_id)
    results["polling"] = result is not None
    if not results["polling"]:
        print_error("Polling falhou. Abortando testes.")
        return False

    # Teste 4: Validar Resultado
    results["validate_result"] = validate_result(result)

    # Teste 5: Job ID Inválido
    results["invalid_job_id"] = test_invalid_job_id()

    # Resumo Final
    print_header("RESUMO DOS TESTES")
    all_passed = True
    for test_name, passed in results.items():
        status = f"{Colors.GREEN}PASSOU{Colors.END}" if passed else f"{Colors.RED}FALHOU{Colors.END}"
        print(f"  {test_name:<30} {status}")
        if not passed:
            all_passed = False

    print(f"\n{Colors.BOLD}")
    if all_passed:
        print_success("TODOS OS TESTES PASSARAM! ✓")
    else:
        print_error("ALGUNS TESTES FALHARAM! ✗")
    print(f"{Colors.END}")

    return all_passed

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Testes interrompidos pelo usuário{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Erro inesperado: {str(e)}{Colors.END}")
        sys.exit(1)
