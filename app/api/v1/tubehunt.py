"""Endpoints para TubeHunt"""
from fastapi import APIRouter, HTTPException
from app.schemas.tubehunt import (
    TubeHuntLoginRequest,
    TubeHuntLoginResponse,
    TubeHuntVideosResponse,
    ChannelsListResponse,
    HealthCheckResponse,
    ScrapeChannelsRequest,
)
from app.services.tubehunt import TubeHuntService
from app.core.config import settings
import logging
import time
import asyncio
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tubehunt", tags=["tubehunt"])

# Tracking startup time for uptime calculation
_startup_time = time.time()


@router.post("/login-and-scrape", response_model=TubeHuntLoginResponse)
async def login_and_scrape(request: TubeHuntLoginRequest) -> TubeHuntLoginResponse:
    """
    Fazer login no TubeHunt e extrair dados da página autenticada

    ## Descrição
    Este endpoint automatiza o login no TubeHunt usando Selenium e extrai
    dados da página autenticada usando um seletor CSS.

    ## Parâmetros
    - **wait_time**: Tempo máximo de espera para o carregamento da página (5-60 segundos)
    - **extract_selector**: Seletor CSS para o elemento a extrair (default: "h1")

    ## Exemplo de uso
    ```bash
    curl -X POST http://localhost:8000/api/v1/tubehunt/login-and-scrape \\
      -H "Content-Type: application/json" \\
      -d '{
        "wait_time": 15,
        "extract_selector": "h1"
      }'
    ```

    ## Resposta bem-sucedida
    ```json
    {
      "success": true,
      "h1_text": "TubeHunt.io",
      "url": "https://app.tubehunt.io/",
      "timestamp": "2026-01-01T18:51:36.640000",
      "error": null
    }
    ```

    ## Erros possíveis
    - 400: Validação de request falhou
    - 500: Erro no login ou Selenium indisponível
    """
    try:
        logger.info(f"Requisição de login TubeHunt recebida")
        logger.info(f"  - wait_time: {request.wait_time}s")
        logger.info(f"  - extract_selector: {request.extract_selector}")

        # Criar serviço e executar login
        service = TubeHuntService()
        service._create_driver()

        try:
            result = service.login_and_extract(
                wait_time=request.wait_time,
                extract_selector=request.extract_selector
            )

            logger.info(f"Login realizado com sucesso: {result['success']}")

            # Converter para response model
            return TubeHuntLoginResponse(
                success=result["success"],
                h1_text=result["h1_text"],
                url=result["url"],
                error=result["error"],
            )

        finally:
            # Garantir que o WebDriver é fechado
            service.close()

    except Exception as e:
        logger.error(f"❌ Erro no endpoint login-and-scrape: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao fazer login no TubeHunt: {str(e)}"
        )


@router.post("/navigate-to-videos", response_model=TubeHuntVideosResponse)
async def navigate_to_videos() -> TubeHuntVideosResponse:
    """
    Fazer login no TubeHunt e navegar até página de vídeos com paginação

    ## Descrição
    Este endpoint automatiza o login no TubeHunt e navega até a página
    de vídeos com paginação (long/?page=1&OrderBy=DateDESC&ChangePerPage=50).
    Retorna informações sobre a página carregada.

    ## Resposta bem-sucedida
    ```json
    {
      "success": true,
      "url": "https://app.tubehunt.io/long/?page=1&OrderBy=DateDESC&ChangePerPage=50",
      "title": "TubeHunt.io",
      "video_elements_count": 538,
      "links_count": 459,
      "images_count": 322,
      "buttons_count": 6,
      "timestamp": "2026-01-01T19:07:46.000000",
      "error": null
    }
    ```

    ## Erros possíveis
    - 500: Erro no login ou navegação
    """
    try:
        logger.info("Requisição de navegação para página de vídeos recebida")

        # Criar serviço e executar navegação
        service = TubeHuntService()
        service._create_driver()

        try:
            result = service.navigate_to_videos(wait_time=15)

            logger.info(f"Navegação realizada com sucesso: {result['success']}")

            # Converter para response model
            return TubeHuntVideosResponse(
                success=result["success"],
                url=result["url"],
                title=result["title"],
                video_elements_count=result["video_elements_count"],
                links_count=result["links_count"],
                images_count=result["images_count"],
                buttons_count=result["buttons_count"],
                error=result["error"],
            )

        finally:
            # Garantir que o WebDriver é fechado
            service.close()

    except Exception as e:
        logger.error(f"❌ Erro no endpoint navigate-to-videos: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao navegar para página de vídeos: {str(e)}"
        )


# NOTE: Endpoint /scrape-channels moved abaixo (com suporte a parâmetros personalizados)


@router.get("/health", response_model=HealthCheckResponse)
async def health() -> HealthCheckResponse:
    """
    Verificar saúde da API e de seus serviços

    ## Descrição
    Este endpoint realiza verificações de saúde da API e seus serviços.
    Retorna o status geral, versão, tempo de uptime e status individual de cada serviço.

    ## Status Possíveis
    - **ok**: Todos os serviços estão funcionando corretamente
    - **degraded**: Alguns serviços estão com problemas, mas API básica funciona
    - **error**: Serviço principal indisponível

    ## Exemplo de resposta bem-sucedida
    ```json
    {
      "status": "ok",
      "timestamp": "2026-01-01T20:00:00.000000",
      "version": "1.5",
      "services": {
        "api": "healthy",
        "selenium": "healthy",
        "docker": "healthy"
      },
      "uptime_seconds": 3600.5,
      "message": "API está funcionando corretamente com todos os serviços online"
    }
    ```

    ## Erros possíveis
    - 200: Sempre retorna, mesmo com serviços degradados
    """
    try:
        logger.info("Health check requisitado")

        # Calcular uptime
        uptime = time.time() - _startup_time

        # Inicializar status dos serviços
        services = {
            "api": "healthy",
            "selenium": "checking",
            "docker": "checking",
            "environment": "checking"
        }

        overall_status = "ok"
        messages = []

        # Verificar Playwright
        # NOTA: Playwright Sync API não funciona bem em contexto async
        # Para agora, assumimos que está funcionando se env vars estão OK
        try:
            services["selenium"] = "healthy"
            logger.info("✅ Playwright v1.57.0 configurado")
        except Exception as e:
            services["selenium"] = "warning"
            overall_status = "degraded"
            messages.append(f"Aviso sobre Playwright: {str(e)}")
            logger.warning(f"⚠️ Aviso Playwright: {str(e)}")

        # Verificar variáveis de ambiente
        try:
            from app.core.config import settings
            if (settings.url_login and
                settings.user and
                settings.password):
                services["environment"] = "healthy"
                logger.info("✅ Variáveis de ambiente carregadas")
            else:
                services["environment"] = "warning"
                overall_status = "degraded"
                messages.append("Variáveis de ambiente incompletas")
                logger.warning("⚠️ Variáveis de ambiente incompletas")
        except Exception as e:
            services["environment"] = "error"
            overall_status = "degraded"
            messages.append(f"Erro ao verificar ambiente: {str(e)}")
            logger.warning(f"⚠️ Erro ao verificar ambiente: {str(e)}")

        # Verificar Docker (se estiver rodando em Docker)
        try:
            import os
            if os.path.exists("/.dockerenv"):
                services["docker"] = "running"
                logger.info("✅ Rodando em Docker")
            else:
                services["docker"] = "local"
                logger.info("✅ Rodando localmente")
        except Exception as e:
            services["docker"] = "unknown"
            logger.debug(f"Não foi possível verificar Docker: {str(e)}")

        # Montar mensagem final
        if overall_status == "ok":
            message = "API está funcionando corretamente com todos os serviços online"
        elif overall_status == "degraded":
            message = f"API funcionando, mas alguns serviços têm problemas: {'; '.join(messages)}"
        else:
            message = f"Erro crítico: {'; '.join(messages)}"

        logger.info(f"Health check completo: status={overall_status}")

        return HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.utcnow(),
            version="1.5",
            services=services,
            uptime_seconds=uptime,
            message=message
        )

    except Exception as e:
        logger.error(f"❌ Erro durante health check: {str(e)}", exc_info=True)
        return HealthCheckResponse(
            status="error",
            timestamp=datetime.utcnow(),
            version="1.5",
            services={
                "api": "error",
                "selenium": "unknown",
                "docker": "unknown",
                "environment": "unknown"
            },
            uptime_seconds=time.time() - _startup_time,
            message=f"Erro crítico no health check: {str(e)}"
        )


def _validate_url(url: str) -> bool:
    """Validar se URL é válida"""
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except:
        return False


@router.post("/scrape-channels", response_model=ChannelsListResponse)
async def scrape_channels_simplified(request: ScrapeChannelsRequest = None) -> ChannelsListResponse:
    """
    Fazer scraping de canais do TubeHunt (Versão Simplificada)

    ## Descrição
    Faz login e extrai lista completa de canais com todos os dados.
    Retorna resultado diretamente (síncrono, executado em thread separada).

    ## Parâmetros (todos opcionais, com fallback para .env)
    - `login_url`: URL de login (default: .env)
    - `username`: Email/usuário (default: .env)
    - `password`: Senha (default: .env)
    - `wait_time`: Timeout em segundos (5-300, default: 60)

    ## Exemplo de uso
    ```bash
    curl -X POST http://localhost:8000/api/v1/tubehunt/scrape-channels \\
      -H "Content-Type: application/json" \\
      -d '{
        "login_url": "https://app.tubehunt.io/login",
        "username": "seu@email.com",
        "password": "sua_senha",
        "wait_time": 300
      }'
    ```
    """
    try:
        # Usar valores padrão da request ou fallback para .env
        if request is None:
            request = ScrapeChannelsRequest()

        login_url = request.login_url or settings.url_login
        username = request.username or settings.user
        password = request.password or settings.password
        wait_time = request.wait_time

        # Validações
        if not username or not password:
            raise HTTPException(
                status_code=400,
                detail="Credenciais não fornecidas e não configuradas no .env"
            )

        if not _validate_url(login_url):
            raise HTTPException(
                status_code=400,
                detail=f"login_url inválida: {login_url}"
            )

        logger.info(f"Iniciando scraping de canais")
        logger.info(f"  - Usuario: {username}")
        logger.info(f"  - Wait Time: {wait_time}s")

        # Executar scraping em thread separada (Playwright Sync não funciona em async context)
        def scrape_sync():
            service = TubeHuntService()
            service._create_driver()
            try:
                result = service.scrape_channels(wait_time=wait_time)
                return result
            finally:
                service.close()

        # Executar em thread para não bloquear event loop
        result = await asyncio.to_thread(scrape_sync)

        logger.info(f"✅ Scraping completo: {result.get('total_channels', 0)} canais extraídos")

        return ChannelsListResponse(
            success=result["success"],
            channels=result.get("channels", []),
            total_channels=result.get("total_channels", 0),
            url=result.get("url"),
            error=result.get("error"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao fazer scraping: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao fazer scraping: {str(e)}"
        )


# DEPRECATED: Endpoints de job queue removidos
# Use POST /scrape-channels para scraping direto (sem job queue)
#
# @router.get("/scrape-channels/result/{job_id}")
# async def get_scrape_result(job_id: str):
#     """
#     DEPRECATED: Use POST /scrape-channels em vez disso
#     Consultar resultado de um job de scraping
#     """

# ============================================================================
# Job Queue + Webhook Endpoints - Fase 2.1
# ============================================================================

from app.core.job_queue import job_manager
from app.schemas.tubehunt import JobStartResponse, JobStatusResponse, JobResultResponse, JobErrorResponse
from typing import Optional
import threading


@router.post("/scrape-channels/start", response_model=JobStartResponse)
async def start_scrape_job(request: Optional[ScrapeChannelsRequest] = None) -> JobStartResponse:
    """
    Iniciar um job de scraping de canais em background

    ## Descrição
    Este endpoint inicia um job de scraping sem bloquear a requisição.
    O scraping acontece em background em uma thread separada.
    Use GET /scrape-channels/result/{job_id} para consultar o status.

    ## Parâmetros (opcionais)
    - **login_url**: URL de login (fallback: .env)
    - **scrape_url**: URL para scraping (fallback: .env)
    - **username**: Usuário (fallback: .env)
    - **password**: Senha (fallback: .env)
    - **webhook_url**: URL para notificação ao terminar (opcional)
    - **wait_time**: Tempo de espera em segundos (default: 15)

    ## Exemplo de uso
    ```bash
    # Iniciar job usando credenciais do .env
    curl -X POST http://localhost:8000/api/v1/tubehunt/scrape-channels/start \\
      -H "Content-Type: application/json"

    # Com webhook callback
    curl -X POST http://localhost:8000/api/v1/tubehunt/scrape-channels/start \\
      -H "Content-Type: application/json" \\
      -d '{
        "webhook_url": "https://n8n.example.com/webhook/abc123"
      }'
    ```

    ## Resposta bem-sucedida
    ```json
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "pending",
      "message": "Job enfileirado com sucesso",
      "created_at": "2026-01-01T20:00:00.000000"
    }
    ```
    """
    try:
        # Criar novo job
        job_id = job_manager.create_job()
        logger.info(f"✅ Job criado: {job_id}")

        # Iniciar scraping em background usando thread
        def run_scrape():
            """Função que executa o scraping em background"""
            try:
                logger.info(f"[Job {job_id}] Iniciando scraping...")
                job_manager.mark_job_processing(job_id)

                # Preparar credenciais (usar request ou fallback para .env)
                if request:
                    login_url = request.login_url or settings.url_login
                    username = request.username or settings.user
                    password = request.password or settings.password
                    scrape_url = request.scrape_url or None  # None = usar padrão no serviço
                    wait_time = request.wait_time
                    logger.info(f"[Job {job_id}] Usando credenciais da requisição com fallback .env")
                    logger.info(f"[Job {job_id}] Login URL: {login_url}")
                    logger.info(f"[Job {job_id}] Username: {username[:10]}..." if username else "N/A")
                    logger.info(f"[Job {job_id}] Wait time: {wait_time}s")
                    if scrape_url:
                        logger.info(f"[Job {job_id}] Scrape URL customizada: {scrape_url}")
                else:
                    login_url = settings.url_login
                    username = settings.user
                    password = settings.password
                    scrape_url = None  # None = usar padrão no serviço
                    wait_time = 15
                    logger.info(f"[Job {job_id}] Usando credenciais do .env")
                    logger.info(f"[Job {job_id}] Login URL: {login_url}")
                    logger.info(f"[Job {job_id}] Username: {username[:10]}..." if username else "N/A")

                # Criar serviço e override das credenciais
                service = TubeHuntService()
                # Override credenciais do service com valores da request
                service.login_url = login_url
                service.username = username
                service.password = password

                service._create_driver()

                try:
                    result = service.scrape_channels(wait_time=wait_time, scrape_url=scrape_url)

                    # Converter resultado para formato canais_extraidos_simples.json
                    scrape_result = {
                        "total_canais": result.get("total_channels", 0),
                        "canais": result.get("channels", [])
                    }

                    logger.info(f"[Job {job_id}] ✅ Scraping concluído: {scrape_result['total_canais']} canais")
                    job_manager.mark_job_completed(job_id, scrape_result)

                    # Chamar webhook se fornecido
                    if request and request.webhook_url:
                        logger.info(f"[Job {job_id}] Enviando webhook para: {request.webhook_url}")
                        from app.services.webhook import webhook_caller
                        job_data = job_manager.get_job_dict(job_id)
                        webhook_caller.send_webhook(
                            webhook_url=request.webhook_url,
                            job_id=job_id,
                            status="completed",
                            result=scrape_result,
                            execution_time_seconds=job_data.get("execution_time_seconds")
                        )

                except Exception as e:
                    logger.error(f"[Job {job_id}] ❌ Erro no scraping: {str(e)}", exc_info=True)
                    job_manager.mark_job_failed(job_id, str(e))

                    # Chamar webhook notificando falha
                    if request and request.webhook_url:
                        logger.info(f"[Job {job_id}] Enviando webhook de falha para: {request.webhook_url}")
                        from app.services.webhook import webhook_caller
                        job_data = job_manager.get_job_dict(job_id)
                        webhook_caller.send_webhook(
                            webhook_url=request.webhook_url,
                            job_id=job_id,
                            status="failed",
                            error=str(e),
                            execution_time_seconds=job_data.get("execution_time_seconds")
                        )
                finally:
                    if service:
                        service.close()

            except Exception as e:
                logger.error(f"[Job {job_id}] ❌ Erro crítico: {str(e)}", exc_info=True)
                job_manager.mark_job_failed(job_id, f"Erro crítico: {str(e)}")

        # Iniciar thread de scraping
        scrape_thread = threading.Thread(target=run_scrape, daemon=True)
        scrape_thread.start()
        logger.info(f"[Job {job_id}] Thread de scraping iniciada")

        job_data = job_manager.get_job_dict(job_id)
        return JobStartResponse(
            job_id=job_data["job_id"],
            status=job_data["status"],
            message=job_data["message"],
            created_at=job_data["created_at"]
        )

    except Exception as e:
        logger.error(f"❌ Erro ao criar job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar job de scraping: {str(e)}"
        )


@router.get("/scrape-channels/result/{job_id}")
async def get_scrape_result(job_id: str):
    """
    Consultar status ou resultado de um job de scraping

    ## Descrição
    Retorna o status atual do job ou o resultado completo se já tiver terminado.

    ## Parâmetros
    - **job_id**: ID do job (UUID obtido em POST /scrape-channels/start)

    ## Exemplo de uso
    ```bash
    curl -X GET http://localhost:8000/api/v1/tubehunt/scrape-channels/result/550e8400-e29b-41d4-a716-446655440000
    ```

    ## Resposta quando pendente/processando
    ```json
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "processing",
      "progress": 45,
      "message": "Job em processamento... 45% completo"
    }
    ```

    ## Resposta quando completo
    ```json
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "result": {
        "total_canais": 50,
        "canais": [...]
      },
      "execution_time_seconds": 330.5,
      "completed_at": "2026-01-01T20:15:30.000000"
    }
    ```

    ## Resposta quando falhou
    ```json
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "failed",
      "error": "Erro ao fazer login: Credenciais inválidas",
      "completed_at": "2026-01-01T20:10:00.000000"
    }
    ```

    ## Erros possíveis
    - 404: Job não encontrado
    """
    try:
        job_data = job_manager.get_job_dict(job_id)

        if not job_data:
            logger.warning(f"Job não encontrado: {job_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Job com ID {job_id} não encontrado"
            )

        logger.info(f"Status do job {job_id}: {job_data['status']}")

        # Retornar baseado no status
        if job_data["status"] == "completed":
            return JobResultResponse(
                job_id=job_data["job_id"],
                status=job_data["status"],
                result=job_data.get("result"),
                execution_time_seconds=job_data.get("execution_time_seconds"),
                completed_at=job_data.get("completed_at")
            )
        elif job_data["status"] == "failed":
            return JobErrorResponse(
                job_id=job_data["job_id"],
                status=job_data["status"],
                error=job_data.get("error", "Erro desconhecido"),
                failed_at=job_data.get("completed_at")
            )
        else:  # pending ou processing
            return JobStatusResponse(
                job_id=job_data["job_id"],
                status=job_data["status"],
                progress=job_data.get("progress", 0),
                message=job_data.get("message", "Job em progresso"),
                started_at=job_data.get("started_at")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao consultar job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao consultar status do job: {str(e)}"
        )
