"""Session Manager para gerenciar browsers persistentes entre requisições"""
import logging
import threading
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from playwright.sync_api import Page

logger = logging.getLogger(__name__)


class Session:
    """Representa uma sessão de usuário com browser persistente"""

    def __init__(self, session_id: str, page: Page, username: str, browser_manager=None):
        self.session_id = session_id
        self.page = page
        self.username = username
        self.browser_manager = browser_manager  # Manter referência para não fechar durante garbage collection
        self.created_at = datetime.utcnow()
        self.last_used = datetime.utcnow()
        self.expires_in = 10800  # 3 horas (aumentado para processar batch de canais)
        self.is_active = True

    def update_last_used(self):
        """Atualiza o timestamp de último uso (heartbeat)"""
        self.last_used = datetime.utcnow()

    def is_expired(self) -> bool:
        """Verifica se a sessão expirou"""
        elapsed = (datetime.utcnow() - self.created_at).total_seconds()
        return elapsed > self.expires_in

    def close(self):
        """Fecha o browser e marca a sessão como inativa"""
        try:
            # Usar browser_manager se disponível (melhor para cleanup)
            if self.browser_manager:
                self.browser_manager.close()
            elif self.page and self.page.context:
                self.page.context.browser.close()
        except Exception as e:
            logger.warning(f"Erro ao fechar browser da sessão {self.session_id}: {e}")
        finally:
            self.is_active = False


class SessionManager:
    """Gerenciador de sessões de browser persistentes"""

    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.lock = threading.RLock()
        logger.info("SessionManager inicializado")

    def create_session(self, page: Page, username: str, browser_manager=None) -> str:
        """
        Cria uma nova sessão e retorna o session_id

        Args:
            page: Playwright Page object do browser logado
            username: Email/username do usuário logado
            browser_manager: PlaywrightBrowserManager para manter vivo durante a sessão

        Returns:
            session_id: UUID único para identificar a sessão
        """
        session_id = str(uuid.uuid4())

        with self.lock:
            self.sessions[session_id] = Session(session_id, page, username, browser_manager)
            logger.info(f"✅ Sessão criada: {session_id} (usuário: {username})")

        return session_id

    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Recupera uma sessão existente

        Args:
            session_id: ID da sessão

        Returns:
            Session object se encontrada e válida, None caso contrário
        """
        with self.lock:
            session = self.sessions.get(session_id)

            if not session:
                logger.warning(f"❌ Sessão não encontrada: {session_id}")
                return None

            if session.is_expired():
                logger.warning(f"❌ Sessão expirada: {session_id}")
                self._close_session_unsafe(session_id)
                return None

            if not session.is_active:
                logger.warning(f"❌ Sessão inativa: {session_id}")
                return None

            # Atualiza heartbeat
            session.update_last_used()
            return session

    def close_session(self, session_id: str) -> bool:
        """
        Fecha uma sessão e remove da memória

        Args:
            session_id: ID da sessão

        Returns:
            True se fechado com sucesso, False se não encontrado
        """
        with self.lock:
            return self._close_session_unsafe(session_id)

    def _close_session_unsafe(self, session_id: str) -> bool:
        """
        Fecha uma sessão (sem lock - usar apenas dentro de lock)

        Args:
            session_id: ID da sessão

        Returns:
            True se fechado com sucesso, False se não encontrado
        """
        session = self.sessions.get(session_id)
        if not session:
            logger.warning(f"❌ Tentativa de fechar sessão inexistente: {session_id}")
            return False

        session.close()
        del self.sessions[session_id]
        logger.info(f"✅ Sessão fechada: {session_id}")
        return True

    def cleanup_expired_sessions(self):
        """
        Background task para limpar sessões expiradas
        Deve ser executado periodicamente (ex: a cada 60 segundos)
        """
        with self.lock:
            expired_ids = [sid for sid, s in self.sessions.items() if s.is_expired()]

            for session_id in expired_ids:
                self._close_session_unsafe(session_id)

            if expired_ids:
                logger.info(f"🧹 Limpeza de sessões: {len(expired_ids)} sessão(ões) expirada(s) removida(s)")

    def get_active_session_count(self) -> int:
        """Retorna número de sessões ativas"""
        with self.lock:
            return len([s for s in self.sessions.values() if s.is_active and not s.is_expired()])


# Instância global do gerenciador
session_manager = SessionManager()
