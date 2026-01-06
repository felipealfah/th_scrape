"""
Job Queue Manager - Gerenciador de jobs para scraping assíncrono

Este módulo implementa um gerenciador de jobs em memória com thread-safety
para executar tarefas de scraping em background e rastrear seu status.
"""

import uuid
import time
import threading
from typing import Dict, Optional, Any
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """Estados possíveis de um job"""
    PENDING = "pending"          # Enfileirado, aguardando execução
    PROCESSING = "processing"    # Em execução
    COMPLETED = "completed"      # Finalizou com sucesso
    FAILED = "failed"            # Falhou com erro


class Job:
    """Classe que representa um job de scraping"""

    def __init__(self, job_id: str):
        self.job_id = job_id
        self.status = JobStatus.PENDING
        self.created_at = datetime.now().isoformat()
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.progress: int = 0  # 0-100
        self.execution_time_seconds: float = 0.0
        self._start_time: Optional[float] = None

    def mark_processing(self):
        """Marca o job como em processamento"""
        self.status = JobStatus.PROCESSING
        self.started_at = datetime.now().isoformat()
        self._start_time = time.time()

    def mark_completed(self, result: Dict[str, Any]):
        """Marca o job como completo com resultado"""
        self.status = JobStatus.COMPLETED
        self.result = result
        self.progress = 100
        self.completed_at = datetime.now().isoformat()
        if self._start_time:
            self.execution_time_seconds = time.time() - self._start_time

    def mark_failed(self, error: str):
        """Marca o job como falhado com erro"""
        self.status = JobStatus.FAILED
        self.error = error
        self.completed_at = datetime.now().isoformat()
        if self._start_time:
            self.execution_time_seconds = time.time() - self._start_time

    def update_progress(self, progress: int):
        """Atualiza o progresso do job (0-100)"""
        self.progress = max(0, min(100, progress))

    def to_dict(self) -> Dict[str, Any]:
        """Converte o job para dicionário"""
        data = {
            "job_id": self.job_id,
            "status": self.status.value,
            "created_at": self.created_at,
            "progress": self.progress,
        }

        if self.started_at:
            data["started_at"] = self.started_at

        if self.status == JobStatus.PROCESSING:
            data["message"] = f"Job em processamento... {self.progress}% completo"
        elif self.status == JobStatus.COMPLETED:
            data["result"] = self.result
            data["completed_at"] = self.completed_at
            data["execution_time_seconds"] = self.execution_time_seconds
        elif self.status == JobStatus.FAILED:
            data["error"] = self.error
            data["completed_at"] = self.completed_at
            data["execution_time_seconds"] = self.execution_time_seconds
        else:  # PENDING
            data["message"] = "Job enfileirado, aguardando execução"

        return data


class JobManager:
    """
    Gerenciador de jobs com thread-safety

    Responsável por:
    - Criar novos jobs
    - Armazenar e recuperar jobs
    - Atualizar status dos jobs
    - Limpeza automática de jobs antigos
    """

    def __init__(self, cleanup_hours: int = 24):
        """
        Inicializa o gerenciador de jobs

        Args:
            cleanup_hours: Horas após as quais um job será removido
        """
        self.jobs: Dict[str, Job] = {}
        self.lock = threading.RLock()
        self.cleanup_hours = cleanup_hours

    def create_job(self) -> str:
        """
        Cria um novo job e retorna seu ID

        Returns:
            ID único do job (UUID)
        """
        job_id = str(uuid.uuid4())
        job = Job(job_id)

        with self.lock:
            self.jobs[job_id] = job

        return job_id

    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Recupera um job pelo ID

        Args:
            job_id: ID do job

        Returns:
            Job ou None se não encontrado
        """
        with self.lock:
            return self.jobs.get(job_id)

    def update_job_status(self, job_id: str, status: JobStatus):
        """
        Atualiza o status de um job

        Args:
            job_id: ID do job
            status: Novo status
        """
        with self.lock:
            job = self.jobs.get(job_id)
            if job:
                job.status = status
                if status == JobStatus.PROCESSING and not job.started_at:
                    job.mark_processing()

    def mark_job_processing(self, job_id: str):
        """Marca um job como em processamento"""
        with self.lock:
            job = self.jobs.get(job_id)
            if job:
                job.mark_processing()

    def mark_job_completed(self, job_id: str, result: Dict[str, Any]):
        """
        Marca um job como completo com resultado

        Args:
            job_id: ID do job
            result: Resultado do scraping (formato canais_extraidos_simples.json)
        """
        with self.lock:
            job = self.jobs.get(job_id)
            if job:
                job.mark_completed(result)

    def mark_job_failed(self, job_id: str, error: str):
        """
        Marca um job como falhado

        Args:
            job_id: ID do job
            error: Mensagem de erro
        """
        with self.lock:
            job = self.jobs.get(job_id)
            if job:
                job.mark_failed(error)

    def update_job_progress(self, job_id: str, progress: int):
        """
        Atualiza o progresso de um job

        Args:
            job_id: ID do job
            progress: Progresso (0-100)
        """
        with self.lock:
            job = self.jobs.get(job_id)
            if job:
                job.update_progress(progress)

    def get_job_dict(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupera um job como dicionário

        Args:
            job_id: ID do job

        Returns:
            Dicionário com dados do job ou None
        """
        with self.lock:
            job = self.jobs.get(job_id)
            if job:
                return job.to_dict()
            return None

    def list_jobs(self) -> Dict[str, Dict[str, Any]]:
        """
        Lista todos os jobs

        Returns:
            Dicionário com todos os jobs
        """
        with self.lock:
            return {
                job_id: job.to_dict()
                for job_id, job in self.jobs.items()
            }

    def cleanup_old_jobs(self):
        """
        Remove jobs mais antigos que cleanup_hours
        Pode ser chamado periodicamente em background
        """
        cutoff_time = time.time() - (self.cleanup_hours * 3600)

        with self.lock:
            job_ids_to_delete = []
            for job_id, job in self.jobs.items():
                # Parse ISO format datetime
                created_timestamp = datetime.fromisoformat(job.created_at).timestamp()
                if created_timestamp < cutoff_time:
                    job_ids_to_delete.append(job_id)

            for job_id in job_ids_to_delete:
                del self.jobs[job_id]

    def delete_job(self, job_id: str) -> bool:
        """
        Remove um job (útil para testes)

        Args:
            job_id: ID do job

        Returns:
            True se removido, False se não encontrado
        """
        with self.lock:
            if job_id in self.jobs:
                del self.jobs[job_id]
                return True
            return False


# Instância global do gerenciador de jobs
job_manager = JobManager()
