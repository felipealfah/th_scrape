"""
Webhook Caller - Notificação de jobs completos

Este módulo implementa a lógica de envio de webhooks para n8n
com retry logic e exponential backoff.
"""

import requests
import time
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder para datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class WebhookCaller:
    """
    Classe para enviar webhooks com retry logic

    Responsável por:
    - Chamar webhook para n8n quando job termina
    - Implementar retry com exponential backoff
    - Logar cada tentativa
    """

    def __init__(self, max_retries: int = 3, timeout: int = 30):
        """
        Inicializa o webhook caller

        Args:
            max_retries: Máximo de tentativas (default: 3)
            timeout: Timeout em segundos por tentativa (default: 30)
        """
        self.max_retries = max_retries
        self.timeout = timeout
        # Delays em segundos: 2s, 4s, 8s
        self.retry_delays = [2, 4, 8]

    def send_webhook(
        self,
        webhook_url: str,
        job_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        execution_time_seconds: Optional[float] = None
    ) -> bool:
        """
        Envia webhook para n8n com retry logic

        Args:
            webhook_url: URL do webhook
            job_id: ID do job
            status: Status final (completed, failed)
            result: Resultado do scraping
            error: Mensagem de erro se falhou
            execution_time_seconds: Tempo de execução

        Returns:
            True se webhook foi enviado com sucesso, False caso contrário
        """
        payload = {
            "job_id": job_id,
            "status": status,
            "execution_time_seconds": execution_time_seconds,
            "timestamp": time.time()
        }

        if status == "completed" and result:
            payload["result"] = result
        elif status == "failed" and error:
            payload["error"] = error

        logger.info(f"[Webhook] Enviando webhook para {webhook_url}")
        logger.info(f"[Webhook] Payload: {payload}")

        for attempt in range(self.max_retries):
            try:
                logger.info(f"[Webhook] Tentativa {attempt + 1}/{self.max_retries}")

                response = requests.post(
                    webhook_url,
                    data=json.dumps(payload, cls=DateTimeEncoder),
                    timeout=self.timeout,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    logger.info(f"✅ [Webhook] Sucesso! Status: {response.status_code}")
                    return True

                logger.warning(f"⚠️ [Webhook] Status {response.status_code}: {response.text}")

                # Se é erro 4xx (exceto timeout), não tenta novamente
                if 400 <= response.status_code < 500 and response.status_code != 408:
                    logger.error(f"❌ [Webhook] Erro permanente ({response.status_code}), abortando")
                    return False

            except requests.Timeout:
                logger.warning(f"⚠️ [Webhook] Timeout (tentativa {attempt + 1})")

            except requests.ConnectionError as e:
                logger.warning(f"⚠️ [Webhook] Erro de conexão: {str(e)} (tentativa {attempt + 1})")

            except Exception as e:
                logger.error(f"❌ [Webhook] Erro inesperado: {str(e)}", exc_info=True)

            # Se não foi última tentativa, aguardar antes de retry
            if attempt < self.max_retries - 1:
                delay = self.retry_delays[attempt] if attempt < len(self.retry_delays) else 8
                logger.info(f"[Webhook] Aguardando {delay}s antes da próxima tentativa...")
                time.sleep(delay)

        logger.error(f"❌ [Webhook] Falhou após {self.max_retries} tentativas")
        return False


# Instância global do webhook caller
webhook_caller = WebhookCaller()
