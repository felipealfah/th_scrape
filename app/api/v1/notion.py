"""Endpoints para scraping de nichos Notion"""
import logging
from fastapi import APIRouter, HTTPException
from app.schemas.tubehunt import (
    ScrapeNichosRequest,
    NichosListResponse,
    JobStartResponse
)
from app.services.notion import NotionNichosService
from app.core.job_queue import job_manager
from datetime import datetime
import threading

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notion", tags=["Notion Nichos"])


def scrape_nichos_job(job_id: str, request: ScrapeNichosRequest):
    """Função que executa o scraping em background"""
    try:
        logger.info(f"[JOB {job_id}] Iniciando scraping de nichos...")
        job_manager.update_job_progress(job_id, 10)

        with NotionNichosService() as service:
            logger.info(f"[JOB {job_id}] Acessando Notion: {request.notion_url}")
            job_manager.update_job_progress(job_id, 20)

            result = service.scrape_nichos(
                notion_url=request.notion_url,
                wait_time=request.wait_time
            )

            logger.info(f"[JOB {job_id}] Scraping concluído. Nichos extraídos: {result.get('total_nichos')}")
            job_manager.update_job_progress(job_id, 90)

            # Salvar resultado
            job_manager.mark_job_completed(job_id, result=result)
            logger.info(f"[JOB {job_id}] Job concluído com sucesso")

            # Enviar webhook se fornecido
            if request.webhook_url:
                from app.services.webhook import send_webhook
                logger.info(f"[JOB {job_id}] Enviando webhook para: {request.webhook_url}")
                send_webhook(job_id, "completed", result, request.webhook_url)

    except Exception as e:
        logger.error(f"[JOB {job_id}] Erro no scraping: {str(e)}", exc_info=True)
        job_manager.mark_job_failed(job_id, error=str(e))

        # Enviar webhook de erro se fornecido
        if request.webhook_url:
            from app.services.webhook import send_webhook
            logger.info(f"[JOB {job_id}] Enviando webhook de erro para: {request.webhook_url}")
            send_webhook(job_id, "failed", None, request.webhook_url, error=str(e))


@router.post(
    "/scrape-nichos/start",
    response_model=JobStartResponse,
    summary="Iniciar scraping de nichos Notion",
    description="Inicia um job em background para fazer scraping de nichos da página Notion"
)
async def start_scrape_nichos(request: ScrapeNichosRequest):
    """
    Inicia um job de scraping de nichos da página Notion.

    - **notion_url**: URL da página Notion para fazer scraping
    - **wait_time**: Tempo de espera para carregamento (5-120 segundos)
    - **webhook_url**: URL opcional para callback quando o job terminar

    Retorna um `job_id` para polling do status e resultado.
    """
    try:
        # Validar URL
        if not request.notion_url or "notion.site" not in request.notion_url:
            raise HTTPException(
                status_code=400,
                detail="notion_url deve ser uma URL válida do Notion"
            )

        # Criar job
        job_id = job_manager.create_job()
        logger.info(f"[JOB {job_id}] Novo job criado para Notion scraping")

        # Executar scraping em thread separada
        thread = threading.Thread(
            target=scrape_nichos_job,
            args=(job_id, request),
            daemon=True
        )
        thread.start()

        return JobStartResponse(
            job_id=job_id,
            status="pending",
            message="Job enfileirado com sucesso",
            created_at=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao iniciar scraping: {str(e)}"
        )


@router.get(
    "/scrape-nichos/result/{job_id}",
    response_model=NichosListResponse,
    summary="Obter resultado do scraping de nichos",
    description="Obtém o resultado de um job de scraping de nichos"
)
async def get_scrape_nichos_result(job_id: str):
    """
    Obtém o resultado de um job de scraping de nichos.

    - **job_id**: ID do job retornado pelo endpoint `/scrape-nichos/start`

    Retorna:
    - Status `pending`: Job ainda está em processamento
    - Status `processing`: Job está em andamento
    - Status `completed`: Scraping concluído com sucesso
    - Status `failed`: Job falhou com erro
    """
    try:
        job = job_manager.get_job_dict(job_id)

        if not job:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} não encontrado"
            )

        status = job.get("status")

        # Se job ainda está pendente ou processando
        if status in ["pending", "processing"]:
            return NichosListResponse(
                success=False,
                nichos=[],
                total_nichos=0,
                error=f"Job ainda em processamento. Progresso: {job.get('progress', 0)}%"
            )

        # Se job falhou
        if status == "failed":
            return NichosListResponse(
                success=False,
                nichos=[],
                total_nichos=0,
                error=job.get("error", "Job falhou sem mensagem de erro")
            )

        # Se job completou com sucesso
        result = job.get("result", {})
        return NichosListResponse(
            success=result.get("success", False),
            nichos=result.get("nichos", []),
            total_nichos=result.get("total_nichos", 0),
            error=result.get("error")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter resultado do job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter resultado: {str(e)}"
        )


@router.get(
    "/health",
    summary="Health check do serviço Notion",
    description="Verifica se o serviço de scraping Notion está disponível"
)
async def notion_health():
    """
    Health check para o serviço de Notion.
    """
    return {
        "status": "healthy",
        "service": "notion-nichos-scraper",
        "version": "1.0"
    }
