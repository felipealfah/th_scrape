"""Endpoints para TubeHunt"""
from fastapi import APIRouter, HTTPException
from app.schemas.tubehunt import (
    TubeHuntLoginRequest,
    TubeHuntLoginResponse,
    TubeHuntVideosResponse,
    ChannelsListResponse,
    ChannelData,
    VideoData,
    HealthCheckResponse,
    JobStartResponse,
    JobStatusResponse,
    JobResultResponse,
    JobErrorResponse
)
from app.services.tubehunt import TubeHuntService
from app.core.job_queue import job_queue, JobStatus
import logging
import time
from datetime import datetime

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


@router.post("/scrape-channels", response_model=ChannelsListResponse)
async def scrape_channels() -> ChannelsListResponse:
    """
    Fazer login no TubeHunt e extrair dados detalhados de canais

    ## Descrição
    Este endpoint automatiza o login no TubeHunt e acessa a página de canais
    (long/?page=1&OrderBy=DateDESC&ChangePerPage=50).
    Extrai dados completos de cada canal incluindo:
    - Nome, link, handle (@), país, inscritos
    - Status de verificação e monetização
    - Estatísticas: views totais, views últimos 60 dias, média de views
    - Tempo desde o primeiro vídeo, total de vídeos, outlier score
    - 6 últimos vídeos populares com links, duração, views e comentários

    ## Resposta bem-sucedida
    ```json
    {
      "success": true,
      "channels": [
        {
          "channel_name": "Lately Fashionable",
          "channel_link": "/channel/UCyzJxq0foatsp3-ZwSuCKBg",
          "channel_handle": "@latelyfashionable",
          "country": "US",
          "subscribers": "2k",
          "is_verified": true,
          "is_monetized": true,
          "total_views": "149k",
          "views_last_60_days": "14k",
          "average_views_per_video": "981",
          "time_since_first_video": "há 6 anos",
          "total_videos": "152",
          "outlier_score": "71×",
          "recent_videos": [
            {
              "title": "Day One of cleaning my sewing studio...",
              "video_link": "https://youtube.com/watch?v=3iHy-TGCV1A",
              "thumbnail_url": "https://i.ytimg.com/vi/3iHy-TGCV1A/mqdefault.jpg",
              "duration": "1:53",
              "views": "2k",
              "comments": "3",
              "uploaded_time": "há 1 mês"
            }
          ]
        }
      ],
      "total_channels": 1,
      "timestamp": "2026-01-01T20:00:00.000000",
      "error": null
    }
    ```

    ## Erros possíveis
    - 500: Erro no login ou scraping de canais
    """
    try:
        logger.info("Requisição de scraping de canais recebida")

        # Criar serviço e executar scraping
        service = TubeHuntService()
        service._create_driver()

        try:
            result = service.scrape_channels(wait_time=15)

            logger.info(f"Scraping realizado com sucesso: {result['success']}")

            # Construir resposta com validação de schemas
            channels_data = []
            for ch in result.get("channels", []):
                try:
                    # Converter vídeos para VideoData
                    videos = [VideoData(**v) for v in ch.get("recent_videos", [])]

                    # Criar ChannelData validado
                    channel = ChannelData(
                        channel_name=ch["channel_name"],
                        channel_link=ch["channel_link"],
                        channel_handle=ch["channel_handle"],
                        country=ch["country"],
                        subscribers=ch["subscribers"],
                        is_verified=ch.get("is_verified", False),
                        is_monetized=ch.get("is_monetized", False),
                        total_views=ch["total_views"],
                        views_last_60_days=ch["views_last_60_days"],
                        average_views_per_video=ch["average_views_per_video"],
                        time_since_first_video=ch["time_since_first_video"],
                        total_videos=ch["total_videos"],
                        outlier_score=ch["outlier_score"],
                        recent_videos=videos
                    )
                    channels_data.append(channel)
                except Exception as e:
                    logger.error(f"Erro ao validar canal: {str(e)}")
                    continue

            return ChannelsListResponse(
                success=result["success"],
                channels=channels_data,
                total_channels=len(channels_data),
                error=result.get("error")
            )

        finally:
            # Garantir que o WebDriver é fechado
            service.close()

    except Exception as e:
        logger.error(f"❌ Erro no endpoint scrape-channels: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao fazer scraping de canais: {str(e)}"
        )


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

        # Verificar Selenium
        try:
            service = TubeHuntService()
            # Apenas tenta criar driver sem fazer operações pesadas
            driver = service.get_driver()
            if driver:
                services["selenium"] = "healthy"
                logger.info("✅ Selenium está acessível")
            else:
                services["selenium"] = "warning"
                overall_status = "degraded"
                messages.append("Selenium WebDriver não respondeu")
                logger.warning("⚠️ Selenium não respondeu")
            service.close()
        except Exception as e:
            services["selenium"] = "error"
            overall_status = "degraded"
            messages.append(f"Erro ao verificar Selenium: {str(e)}")
            logger.warning(f"⚠️ Erro ao verificar Selenium: {str(e)}")

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


@router.post("/scrape-channels/start", response_model=JobStartResponse)
async def start_scrape_channels() -> JobStartResponse:
    """
    Iniciar job assíncrono de scraping de canais

    ## Descrição
    Este endpoint cria um job de scraping assíncrono que é executado em background.
    Retorna um job_id que pode ser usado para consultar o status e resultado do scraping.

    ## Fluxo
    1. Endpoint retorna imediatamente com job_id
    2. Scraping ocorre em background (não bloqueia a API)
    3. Use GET /scrape-channels/result/{job_id} para consultar o resultado

    ## Resposta bem-sucedida
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
    # 1. Iniciar job
    curl -X POST http://localhost:8000/api/v1/tubehunt/scrape-channels/start

    # 2. Consultar resultado (após alguns minutos)
    curl http://localhost:8000/api/v1/tubehunt/scrape-channels/result/{job_id}
    ```
    """
    try:
        logger.info("Requisição para iniciar scraping assíncrono de canais")

        # Criar novo job
        job_id = job_queue.create_job()
        job = job_queue.get_job(job_id)

        # Função que será executada em background
        def scrape_task():
            service = TubeHuntService()
            service._create_driver()
            try:
                result = service.scrape_channels(wait_time=15)
                return result
            finally:
                service.close()

        # Iniciar tarefa em background
        job_queue.start_background_task(job_id, scrape_task)

        logger.info(f"Job de scraping iniciado: {job_id}")

        return JobStartResponse(
            job_id=job_id,
            status="pending",
            message="Job enfileirado com sucesso",
            created_at=job.created_at,
        )

    except Exception as e:
        logger.error(f"❌ Erro ao iniciar scraping assíncrono: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao iniciar scraping: {str(e)}"
        )


@router.get("/scrape-channels/result/{job_id}")
async def get_scrape_result(job_id: str):
    """
    Consultar resultado de um job de scraping

    ## Descrição
    Retorna o status e resultado de um job iniciado com POST /scrape-channels/start.

    ## Estados Possíveis
    - **pending**: Job enfileirado, não iniciado
    - **processing**: Job em execução
    - **completed**: Job concluído com sucesso
    - **failed**: Job falhou

    ## Exemplos de Resposta

    ### Processando
    ```json
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "processing",
      "progress": 45,
      "message": "Extraindo dados de canais... 45/50 concluído",
      "started_at": "2026-01-01T20:01:00.000000"
    }
    ```

    ### Completo
    ```json
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "result": {
        "success": true,
        "channels": [...],
        "total_channels": 50,
        "timestamp": "2026-01-01T20:15:30.000000",
        "error": null
      },
      "execution_time_seconds": 330.5,
      "completed_at": "2026-01-01T20:15:30.000000"
    }
    ```

    ### Falhou
    ```json
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "failed",
      "error": "Erro ao fazer scraping: timeout na página",
      "failed_at": "2026-01-01T20:10:00.000000"
    }
    ```
    """
    try:
        logger.info(f"Consultando resultado do job: {job_id}")

        # Obter job
        job = job_queue.get_job(job_id)
        if not job:
            logger.warning(f"Job não encontrado: {job_id}")
            raise HTTPException(status_code=404, detail=f"Job não encontrado: {job_id}")

        # Retornar resposta apropriada baseada no status
        if job.status == JobStatus.PENDING or job.status == JobStatus.PROCESSING:
            return JobStatusResponse(
                job_id=job_id,
                status=job.status.value,
                progress=job.progress,
                message=job.message,
                started_at=job.started_at,
            )

        elif job.status == JobStatus.COMPLETED:
            execution_time = None
            if job.started_at and job.completed_at:
                execution_time = (job.completed_at - job.started_at).total_seconds()

            return JobResultResponse(
                job_id=job_id,
                status=job.status.value,
                result=job.result,
                execution_time_seconds=execution_time,
                completed_at=job.completed_at,
            )

        elif job.status == JobStatus.FAILED:
            return JobErrorResponse(
                job_id=job_id,
                status=job.status.value,
                error=job.error or "Erro desconhecido",
                failed_at=job.completed_at,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erro ao consultar resultado: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao consultar resultado: {str(e)}"
        )
