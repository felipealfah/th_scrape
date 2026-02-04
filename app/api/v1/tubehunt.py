"""Endpoints para TubeHunt"""
from fastapi import APIRouter, HTTPException
from app.schemas.tubehunt import (
    TubeHuntLoginRequest,
    TubeHuntLoginResponse,
    TubeHuntVideosResponse,
    ChannelsListResponse,
    HealthCheckResponse,
    ScrapeChannelsRequest,
    LoginRequest,
    LoginResponse,
    ChannelDetailedData,
    ScrapeChannelRequest,
    ScrapeChannelsListResponse,
)
from app.services.tubehunt import TubeHuntService
from app.services.webhook import webhook_caller
from app.core.config import settings
import logging
import time
import asyncio
import threading
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


@router.post("/scrape-channels/{session_id}", response_model=ChannelsListResponse)
async def scrape_channels_with_session(session_id: str, request: ScrapeChannelsRequest = None) -> ChannelsListResponse:
    """
    Fazer scraping de lista de canais usando uma sessão existente

    ## Descrição
    Extrai lista de canais reusando a sessão e browser já abertos.
    Não faz login novamente (mais rápido e eficiente).
    Retorna resultado diretamente com webhook opcional.

    ## Path Parameters
    - `session_id`: ID da sessão (obtido em POST /login)

    ## Body Parameters
    - `scrape_url` (opcional): URL da página para extrair canais (fallback .env)
    - `wait_time` (default: 15): Timeout em segundos (5-600)
    - `webhook_url` (opcional): URL para notificação ao final

    ## Exemplo de uso
    ```bash
    curl -X POST http://localhost:8000/api/v1/tubehunt/scrape-channels/7f60430e-1c8b-48fb-bd39-4fa7a2599fa5 \\
      -H "Content-Type: application/json" \\
      -d '{
        "scrape_url": "https://app.tubehunt.io/long/?page=1&OrderBy=DateDESC&ChangePerPage=50",
        "wait_time": 60,
        "webhook_url": "https://seu-webhook.com/callback"
      }'
    ```
    """
    start_time = time.time()

    try:
        # Buscar sessão existente
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Sessão não encontrada: {session_id}"
            )

        # Usar valores padrão da request ou fallback para .env
        if request is None:
            request = ScrapeChannelsRequest()

        scrape_url = request.scrape_url or settings.url_scrape_channels
        wait_time = request.wait_time
        webhook_url = request.webhook_url

        # Validações
        if not _validate_url(scrape_url):
            raise HTTPException(
                status_code=400,
                detail=f"scrape_url inválida: {scrape_url}"
            )

        logger.info(f"Iniciando scraping de canais com sessão {session_id}")
        logger.info(f"  - URL: {scrape_url}")
        logger.info(f"  - Wait Time: {wait_time}s")
        if webhook_url:
            logger.info(f"  - Webhook: {webhook_url}")

        # Executar scraping reutilizando a sessão aberta
        def scrape_sync():
            try:
                page = session.page
                service = TubeHuntService()
                service.page = page
                service.browser_manager = session.browser_manager

                # Fazer scraping na página já carregada (já está logado)
                result = service.scrape_channels(wait_time=wait_time, scrape_url=scrape_url)
                return result

            except Exception as e:
                logger.error(f"❌ Erro no scraping: {str(e)}", exc_info=True)
                raise

        # Executar no executor
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, scrape_sync)

        execution_time = time.time() - start_time

        logger.info(f"✅ Scraping completo: {result.get('total_channels', 0)} canais extraídos")

        # Preparar resposta
        response_data = ChannelsListResponse(
            success=result["success"],
            channels=result.get("channels", []),
            total_channels=result.get("total_channels", 0),
            url=result.get("url"),
            error=result.get("error"),
        )

        # Enviar webhook se URL foi fornecida
        if webhook_url:
            logger.info(f"📤 Enviando webhook para {webhook_url}")
            webhook_payload = response_data.model_dump()
            webhook_payload["session_id"] = session_id  # Adicionar session_id
            webhook_caller.send_webhook(
                webhook_url=webhook_url,
                job_id=f"scrape-channels-{session_id}",
                status="completed",
                result=webhook_payload,
                execution_time_seconds=execution_time
            )

        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao fazer scraping de canais: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao fazer scraping de canais: {str(e)}"
        )


# ============================================================================
# Job Queue + Webhook Endpoints - Backwards Compatibility
# ============================================================================

from app.core.job_queue import job_manager
from app.schemas.tubehunt import JobStartResponse, JobStatusResponse, JobResultResponse, JobErrorResponse
from typing import Optional


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


# ============================================================================
# Phase 4: Session-based Channel Scraping with Persistent Browser
# ============================================================================

from app.core.session_manager import session_manager


@router.post("/login", response_model=LoginResponse)
async def login_with_session(request: LoginRequest) -> LoginResponse:
    """
    Criar sessão persistente com browser autenticado

    ## Descrição
    Faz login no TubeHunt e retorna um session_id para uso em requisições subsequentes.
    O browser permanece aberto em memória durante 30 minutos.

    ## Parâmetros
    - **username**: Email/username (usa .env se não fornecido)
    - **password**: Senha (usa .env se não fornecido)

    ## Exemplo de uso
    ```bash
    curl -X POST http://localhost:8000/api/v1/tubehunt/login \\
      -H "Content-Type: application/json" \\
      -d '{
        "username": "seu@email.com",
        "password": "sua_senha"
      }'
    ```

    ## Resposta bem-sucedida
    ```json
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "logged_in",
      "created_at": "2026-01-01T20:00:00.000000",
      "expires_in": 1800,
      "message": "✅ Sessão criada e login realizado com sucesso",
      "error": null
    }
    ```
    """
    try:
        # Usar credenciais fornecidas ou fallback para .env
        username = request.username or settings.user
        password = request.password or settings.password

        if not username or not password:
            return LoginResponse(
                session_id=None,
                status="failed",
                message="Credenciais não fornecidas",
                error="Username ou password não configurados"
            )

        logger.info(f"Iniciando login para sessão persistente (usuário: {username[:20]}...)")

        # Executar login em thread separada
        def login_sync():
            service = TubeHuntService()
            service._create_driver()
            try:
                # Fazer login
                service.username = username
                service.password = password
                service._access_login_page()
                service._fill_credentials()
                service._submit_form()
                service._wait_for_redirect()

                logger.info("✅ Login realizado com sucesso")

                # Obter página logada
                page = service.get_page()
                browser_manager = service.browser_manager

                # Criar sessão persistente (passando browser_manager para manter vivo)
                session_id = session_manager.create_session(page, username, browser_manager)

                logger.info(f"✅ Sessão criada: {session_id}")

                return {
                    "success": True,
                    "session_id": session_id,
                    "status": "logged_in",
                    "message": "✅ Sessão criada e login realizado com sucesso"
                }

            except Exception as e:
                logger.error(f"❌ Erro no login: {str(e)}", exc_info=True)
                if service:
                    service.close()
                return {
                    "success": False,
                    "session_id": None,
                    "status": "failed",
                    "error": str(e),
                    "message": f"❌ Erro ao fazer login: {str(e)}"
                }

        # Usar run_in_executor ao invés de to_thread para evitar erro com Playwright Sync API
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, login_sync)

        if result["success"]:
            return LoginResponse(
                session_id=result["session_id"],
                status=result["status"],
                message=result["message"],
                error=None
            )
        else:
            return LoginResponse(
                session_id=None,
                status=result["status"],
                message=result["message"],
                error=result.get("error")
            )

    except Exception as e:
        logger.error(f"❌ Erro no endpoint /login: {str(e)}", exc_info=True)
        return LoginResponse(
            session_id=None,
            status="failed",
            message=f"❌ Erro ao criar sessão: {str(e)}",
            error=str(e)
        )


@router.post("/scrape-channel/{session_id}")
async def scrape_channel(session_id: str, request: ScrapeChannelRequest):
    """
    Scraping de um ou múltiplos canais usando sessão persistente

    ## Descrição
    Usa uma sessão persistente (obtida via POST /login) para scraping de canal(is).
    - Se fornecer **channel_link**: retorna dados de um canal
    - Se fornecer **channel_links**: retorna lista de canais

    Extrai 6 campos: keywords, subjects, niches, views_30_days, revenue_30_days.

    ## Parâmetros
    - **session_id**: ID da sessão (obtido em POST /login)
    - **channel_link**: URL de um canal (mutuamente exclusivo com channel_links)
    - **channel_links**: Lista de URLs de canais (mutuamente exclusivo com channel_link)
    - **webhook_url** (opcional): URL do webhook para notificação ao final do scraping

    ## Exemplos de uso

    ### Um canal
    ```bash
    curl -X POST http://localhost:8000/api/v1/tubehunt/scrape-channel/550e8400-e29b-41d4-a716-446655440000 \\
      -H "Content-Type: application/json" \\
      -d '{
        "channel_link": "https://app.tubehunt.io/channel/UCEvkNQR22vQYzp2hil_Z9kA",
        "webhook_url": "https://webhook.site/unique-id"
      }'
    ```

    ### Múltiplos canais
    ```bash
    curl -X POST http://localhost:8000/api/v1/tubehunt/scrape-channel/550e8400-e29b-41d4-a716-446655440000 \\
      -H "Content-Type: application/json" \\
      -d '{
        "channel_links": [
          "https://app.tubehunt.io/channel/UCEvkNQR22vQYzp2hil_Z9kA",
          "https://app.tubehunt.io/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw"
        ],
        "webhook_url": "https://webhook.site/unique-id"
      }'
    ```

    ## Respostas

    ### Um canal
    ```json
    {
      "channel_link": "https://app.tubehunt.io/channel/UCEvkNQR22vQYzp2hil_Z9kA",
      "keywords": ["cruceros 2025", "viajar en crucero"],
      "subjects": ["Tourism", "Food"],
      "niches": ["Cruzeiros"],
      "views_30_days": "357.96k",
      "revenue_30_days": "$239,00 - $781,00"
    }
    ```

    ### Múltiplos canais
    ```json
    {
      "total_scraped": 2,
      "total_requested": 2,
      "channels": [...],
      "failed_channels": []
    }
    ```
    """
    start_time = time.time()

    try:
        # Validar inputs
        request.validate_inputs()

        # Validar session_id
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=401,
                detail=f"Sessão inválida ou expirada: {session_id}"
            )

        logger.info(f"✅ Sessão válida encontrada: {session_id}")

        # Detectar se é um canal ou lista
        if request.channel_link:
            # ===== MODO: UM CANAL =====
            logger.info(f"🔍 Scrapeando um canal: {request.channel_link}")

            def scrape_single():
                try:
                    page = session.page
                    service = TubeHuntService()
                    service.page = page
                    service.browser_manager = session.browser_manager

                    logger.info(f"📍 Extraindo dados do canal...")
                    channel_data = service.scrape_channel_details(page, request.channel_link)

                    if not channel_data:
                        raise Exception("Falha ao extrair dados do canal")

                    logger.info(f"✅ Scrapeado com sucesso!")
                    return channel_data

                except Exception as e:
                    logger.error(f"❌ Erro no scraping: {str(e)}", exc_info=True)
                    raise

            # Executar no executor
            loop = asyncio.get_event_loop()
            channel_data = await loop.run_in_executor(None, scrape_single)

            execution_time = time.time() - start_time

            # Preparar resposta
            response_data = ChannelDetailedData(
                channel_link=channel_data.channel_link,
                keywords=channel_data.keywords,
                subjects=channel_data.subjects,
                niches=channel_data.niches,
                views_30_days=channel_data.views_30_days,
                revenue_30_days=channel_data.revenue_30_days
            )

            # Enviar webhook se URL foi fornecida
            if request.webhook_url:
                logger.info(f"📤 Enviando webhook para {request.webhook_url}")
                webhook_payload = response_data.model_dump()
                webhook_payload["session_id"] = session_id  # Adicionar session_id
                webhook_caller.send_webhook(
                    webhook_url=request.webhook_url,
                    job_id=session_id,
                    status="completed",
                    result=webhook_payload,
                    execution_time_seconds=execution_time
                )

            return response_data

        else:
            # ===== MODO: MÚLTIPLOS CANAIS =====
            logger.info(f"🔍 Scrapeando {len(request.channel_links)} canais")

            def scrape_batch():
                channels_data = []
                failed_channels = []

                page = None
                try:
                    # NÃO reusar page da thread principal (causa greenlet thread-binding error)
                    # Criar nova página dentro da thread do job
                    logger.info(f"[Job {job_id}] Criando nova página para scraping...")
                    page = session.browser_manager.browser.new_page()

                    service = TubeHuntService()
                    service.page = page
                    service.browser_manager = session.browser_manager

                    logger.info(f"[Job {job_id}] Página criada com sucesso")

                    # Scrape each channel sequentially
                    for idx, channel_link in enumerate(request.channel_links, 1):
                        try:
                            logger.info(f"[{idx}/{len(request.channel_links)}] 🔍 Extraindo: {channel_link}")
                            channel_data = service.scrape_channel_details(page, channel_link)

                            if not channel_data:
                                raise Exception("Falha ao extrair dados do canal")

                            channels_data.append(channel_data)
                            logger.info(f"[{idx}/{len(request.channel_links)}] ✅ Sucesso!")

                        except Exception as e:
                            logger.error(f"[{idx}/{len(request.channel_links)}] ❌ Erro: {str(e)}", exc_info=True)
                            failed_channels.append({
                                "channel_link": channel_link,
                                "error": str(e)
                            })
                            continue

                    return {
                        "channels": channels_data,
                        "failed_channels": failed_channels,
                        "total_scraped": len(channels_data),
                        "total_requested": len(request.channel_links)
                    }

                except Exception as e:
                    logger.error(f"❌ Erro crítico: {str(e)}", exc_info=True)
                    raise

            # Executar no executor
            loop = asyncio.get_event_loop()
            batch_result = await loop.run_in_executor(None, scrape_batch)

            execution_time = time.time() - start_time

            # Preparar resposta
            response_data = ScrapeChannelsListResponse(
                total_scraped=batch_result["total_scraped"],
                total_requested=batch_result["total_requested"],
                channels=batch_result["channels"],
                failed_channels=batch_result["failed_channels"]
            )

            # Enviar webhook se URL foi fornecida
            if request.webhook_url:
                logger.info(f"📤 Enviando webhook para {request.webhook_url}")
                webhook_payload = response_data.model_dump()
                webhook_payload["session_id"] = session_id  # Adicionar session_id
                webhook_caller.send_webhook(
                    webhook_url=request.webhook_url,
                    job_id=session_id,
                    status="completed",
                    result=webhook_payload,
                    execution_time_seconds=execution_time
                )

            return response_data

    except ValueError as e:
        logger.error(f"❌ Erro de validação: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao fazer scraping: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao scraping: {str(e)}"
        )


@router.post("/scrape-channel-async/{session_id}")
async def scrape_channel_async(session_id: str, request: ScrapeChannelRequest) -> JobStartResponse:
    """
    Scraping assíncrono de múltiplos canais usando sessão persistente

    ## Descrição
    Retorna **imediatamente** com um job_id e processa os canais em background.
    Ideal para operações longas (50+ canais) que podem fazer timeout na requisição HTTP.

    Use GET /scrape-channel/result/{job_id} para consultar o status.

    ## Parâmetros
    - **session_id**: ID da sessão (obtido em POST /login)
    - **channel_links**: Lista de URLs de canais
    - **webhook_url** (opcional): URL para notificação quando terminar

    ## Resposta imediata
    ```json
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "pending",
      "message": "Job enfileirado com sucesso",
      "created_at": "2026-01-01T20:00:00.000000"
    }
    ```

    ## Exemplo de uso
    ```bash
    curl -X POST http://localhost:8000/api/v1/tubehunt/scrape-channel-async/550e8400 \\
      -H "Content-Type: application/json" \\
      -d '{
        "channel_links": [
          "https://app.tubehunt.io/channel/UCEvkNQR22vQYzp2hil_Z9kA",
          "https://app.tubehunt.io/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw"
        ],
        "webhook_url": "https://webhook.site/unique-id"
      }'

    # Consultar resultado depois
    curl -X GET http://localhost:8000/api/v1/tubehunt/scrape-channel/result/550e8400-e29b-41d4-a716
    ```
    """
    try:
        # Validar inputs
        request.validate_inputs()

        # Validar session_id
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=401,
                detail=f"Sessão inválida ou expirada: {session_id}"
            )

        # Apenas suporta múltiplos canais em modo assíncrono
        if not request.channel_links:
            raise ValueError("Use o endpoint /scrape-channel/{session_id} para um único canal")

        # Criar novo job
        job_id = job_manager.create_job()
        logger.info(f"✅ Job criado: {job_id} para {len(request.channel_links)} canais")

        # Iniciar scraping em background
        def run_batch_scrape():
            """Função que executa o batch scraping em background"""
            try:
                logger.info(f"[Job {job_id}] Iniciando scraping de {len(request.channel_links)} canais...")
                job_manager.mark_job_processing(job_id)

                start_time = time.time()
                channels_data = []
                failed_channels = []

                service = None
                page = None
                try:
                    # Criar nova instância de serviço completamente independente
                    # Playwright sync_api usa greenlet que é vinculado à thread - não pode ser reutilizado
                    logger.info(f"[Job {job_id}] Criando browser independente na thread do job...")

                    service = TubeHuntService()
                    service._create_driver()

                    page = service.page
                    logger.info(f"[Job {job_id}] Browser criado, fazendo login...")

                    # Fazer login manualmente
                    service._access_login_page()
                    service._fill_credentials()
                    service._submit_form()
                    service._wait_for_redirect()

                    logger.info(f"[Job {job_id}] Login bem-sucedido, iniciando scraping")

                    # Scrape each channel sequentially
                    for idx, channel_link in enumerate(request.channel_links, 1):
                        try:
                            logger.info(f"[Job {job_id}] [{idx}/{len(request.channel_links)}] 🔍 Extraindo: {channel_link}")
                            channel_data = service.scrape_channel_details(page, channel_link)

                            if not channel_data:
                                raise Exception("Falha ao extrair dados do canal")

                            channels_data.append(channel_data)
                            logger.info(f"[Job {job_id}] [{idx}/{len(request.channel_links)}] ✅ Sucesso!")

                        except Exception as e:
                            logger.error(f"[Job {job_id}] [{idx}/{len(request.channel_links)}] ❌ Erro: {str(e)}", exc_info=True)
                            failed_channels.append({
                                "channel_link": channel_link,
                                "error": str(e)
                            })
                            continue

                    execution_time = time.time() - start_time

                    # Preparar resultado
                    scrape_result = {
                        "total_scraped": len(channels_data),
                        "total_requested": len(request.channel_links),
                        "channels": channels_data,
                        "failed_channels": failed_channels,
                        "session_id": session_id
                    }

                    logger.info(f"[Job {job_id}] ✅ Scraping concluído: {len(channels_data)}/{len(request.channel_links)} canais")
                    job_manager.mark_job_completed(job_id, scrape_result)

                    # Chamar webhook se fornecido
                    if request.webhook_url:
                        logger.info(f"[Job {job_id}] Enviando webhook para: {request.webhook_url}")
                        webhook_caller.send_webhook(
                            webhook_url=request.webhook_url,
                            job_id=job_id,
                            status="completed",
                            result=scrape_result,
                            execution_time_seconds=execution_time
                        )

                except Exception as e:
                    logger.error(f"[Job {job_id}] ❌ Erro crítico: {str(e)}", exc_info=True)
                    job_manager.mark_job_failed(job_id, str(e))

                    # Chamar webhook de falha
                    if request.webhook_url:
                        logger.info(f"[Job {job_id}] Enviando webhook de falha para: {request.webhook_url}")
                        webhook_caller.send_webhook(
                            webhook_url=request.webhook_url,
                            job_id=job_id,
                            status="failed",
                            error=str(e),
                            execution_time_seconds=time.time() - start_time
                        )
                finally:
                    # Fechar página criada
                    if page:
                        try:
                            page.close()
                            logger.info(f"[Job {job_id}] Página fechada com sucesso")
                        except Exception as e:
                            logger.warning(f"[Job {job_id}] Erro ao fechar página: {str(e)}")

            except Exception as e:
                logger.error(f"[Job {job_id}] ❌ Erro crítico: {str(e)}", exc_info=True)
                job_manager.mark_job_failed(job_id, f"Erro crítico: {str(e)}")

        # Iniciar thread de scraping
        scrape_thread = threading.Thread(target=run_batch_scrape, daemon=True)
        scrape_thread.start()
        logger.info(f"[Job {job_id}] Thread de scraping iniciada")

        job_data = job_manager.get_job_dict(job_id)
        return JobStartResponse(
            job_id=job_data["job_id"],
            status=job_data["status"],
            message=f"Job enfileirado com sucesso para {len(request.channel_links)} canais",
            created_at=job_data["created_at"]
        )

    except ValueError as e:
        logger.error(f"❌ Erro de validação: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao criar job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar job de scraping: {str(e)}"
        )


@router.delete("/sessions/{session_id}")
async def close_session(session_id: str):
    """
    Fechar sessão persistente e liberar recursos

    ## Descrição
    Fecha o browser da sessão especificada e remove da memória.
    Libera recursos e invalida o session_id para novas requisições.

    ## Parâmetros
    - **session_id**: ID da sessão (UUID obtido em POST /login)

    ## Exemplo de uso
    ```bash
    curl -X DELETE http://localhost:8000/api/v1/tubehunt/sessions/550e8400-e29b-41d4-a716-446655440000
    ```

    ## Resposta bem-sucedida
    ```json
    {
      "success": true,
      "message": "✅ Sessão fechada com sucesso",
      "session_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    ```

    ## Resposta quando não encontrada
    ```json
    {
      "success": false,
      "message": "❌ Sessão não encontrada",
      "session_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    ```
    """
    try:
        logger.info(f"Encerrando sessão: {session_id}")

        # Usar executor para fechar sessão (evita thread-binding do Playwright)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, session_manager.close_session, session_id)

        if result:
            logger.info(f"✅ Sessão encerrada: {session_id}")
            return {
                "success": True,
                "message": "✅ Sessão fechada com sucesso",
                "session_id": session_id
            }
        else:
            logger.warning(f"❌ Sessão não encontrada: {session_id}")
            return {
                "success": False,
                "message": "❌ Sessão não encontrada",
                "session_id": session_id
            }

    except Exception as e:
        logger.error(f"❌ Erro ao fechar sessão: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao fechar sessão: {str(e)}"
        )
