"""Job Queue Manager para gerenciar tarefas assíncronas de scraping"""
import uuid
import time
import threading
from typing import Dict, Optional, Callable, Any
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Estados possíveis de um job"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job:
    """Representa um job de scraping"""

    def __init__(self, job_id: str):
        self.job_id = job_id
        self.status = JobStatus.PENDING
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.progress: int = 0  # 0-100
        self.message: str = "Job enfileirado"

    def to_dict(self) -> Dict[str, Any]:
        """Converter job para dicionário"""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
            "message": self.message,
            "result": self.result,
            "error": self.error,
        }


class JobQueue:
    """Gerenciador de fila de jobs com armazenamento em memória"""

    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self._lock = threading.RLock()

    def create_job(self) -> str:
        """Criar novo job e retornar job_id"""
        job_id = str(uuid.uuid4())
        job = Job(job_id)

        with self._lock:
            self.jobs[job_id] = job
            logger.info(f"Job criado: {job_id}")

        return job_id

    def get_job(self, job_id: str) -> Optional[Job]:
        """Obter job por ID"""
        with self._lock:
            return self.jobs.get(job_id)

    def update_job(
        self,
        job_id: str,
        status: Optional[JobStatus] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> bool:
        """Atualizar status e progresso do job"""
        with self._lock:
            job = self.jobs.get(job_id)
            if not job:
                return False

            if status:
                job.status = status
                if status == JobStatus.PROCESSING and not job.started_at:
                    job.started_at = datetime.utcnow()
                elif status == JobStatus.COMPLETED:
                    job.completed_at = datetime.utcnow()
                elif status == JobStatus.FAILED:
                    job.completed_at = datetime.utcnow()

            if progress is not None:
                job.progress = max(0, min(100, progress))

            if message:
                job.message = message

            if result:
                job.result = result

            if error:
                job.error = error

            logger.info(f"Job atualizado: {job_id} -> {status}")
            return True

    def start_background_task(
        self, job_id: str, task_func: Callable[[], Dict[str, Any]]
    ) -> None:
        """Executar tarefa em background thread"""
        job = self.get_job(job_id)
        if not job:
            logger.error(f"Job não encontrado: {job_id}")
            return

        def run_task():
            try:
                # Marcar como processando
                self.update_job(job_id, status=JobStatus.PROCESSING, message="Iniciando scraping...")

                # Executar tarefa
                result = task_func()

                # Marcar como completo
                self.update_job(
                    job_id,
                    status=JobStatus.COMPLETED,
                    progress=100,
                    result=result,
                    message="Scraping completo com sucesso",
                )
                logger.info(f"Job completo: {job_id}")

            except Exception as e:
                error_msg = str(e)
                self.update_job(
                    job_id,
                    status=JobStatus.FAILED,
                    error=error_msg,
                    message=f"Erro ao fazer scraping: {error_msg}",
                )
                logger.error(f"Job falhou: {job_id} - {error_msg}", exc_info=True)

        # Executar em thread separada (daemon)
        thread = threading.Thread(target=run_task, daemon=True)
        thread.start()
        logger.info(f"Tarefa iniciada em background: {job_id}")

    def list_jobs(self, status: Optional[JobStatus] = None) -> list[Job]:
        """Listar todos os jobs, opcionalmente filtrados por status"""
        with self._lock:
            if status:
                return [job for job in self.jobs.values() if job.status == status]
            return list(self.jobs.values())

    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Remover jobs antigos (> max_age_hours). Retorna número de jobs removidos"""
        now = datetime.utcnow()
        removed_count = 0

        with self._lock:
            jobs_to_remove = []
            for job_id, job in self.jobs.items():
                age_hours = (now - job.created_at).total_seconds() / 3600
                if age_hours > max_age_hours:
                    jobs_to_remove.append(job_id)

            for job_id in jobs_to_remove:
                del self.jobs[job_id]
                removed_count += 1
                logger.info(f"Job antigo removido: {job_id}")

        return removed_count


# Instância global do job queue
job_queue = JobQueue()
