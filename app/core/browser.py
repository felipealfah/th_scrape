"""
Gerenciador de navegador Playwright com suporte a context manager.
"""

import logging
from typing import Optional
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Playwright
import threading

logger = logging.getLogger(__name__)

# Use threading.local() to store one Playwright instance per thread
# This avoids greenlet thread-binding errors when using Playwright sync API
# across multiple executor threads
_thread_local = threading.local()

def _get_or_create_playwright() -> Playwright:
    """
    Obter ou criar instância Playwright por thread.

    Playwright sync API usa greenlets que são bound a threads.
    Usar uma instância por thread evita erros de greenlet.
    """
    if not hasattr(_thread_local, 'playwright_instance') or _thread_local.playwright_instance is None:
        logger.info(f"Criando instância Playwright para thread: {threading.current_thread().name}")
        _thread_local.playwright_instance = sync_playwright().start()
        logger.info(f"✅ Instância Playwright criada para thread: {threading.current_thread().name}")

    return _thread_local.playwright_instance


class PlaywrightBrowserManager:
    """
    Gerenciador de navegador Playwright com ciclo de vida completo.

    Suporta inicialização automática e limpeza de recursos via context manager.
    """

    def __init__(self, headless: bool = True, browser_type: str = "chromium", viewport: Optional[dict] = None):
        """
        Inicializar PlaywrightBrowserManager.

        Args:
            headless: Se True, executa em modo headless (sem GUI)
            browser_type: Tipo de navegador ("chromium", "firefox", "webkit")
            viewport: Dicionário com "width" e "height" ou None para padrão
        """
        self.headless = headless
        self.browser_type = browser_type
        self.viewport = viewport or {"width": 1280, "height": 720}
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def __enter__(self):
        """Context manager entry - inicializar navegador."""
        self.launch()
        return self.page

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - limpar recursos."""
        self.close()
        return False

    def launch(self) -> Page:
        """
        Lançar navegador Playwright e criar nova página.

        Returns:
            Page: Instância de página Playwright para automação

        Raises:
            ValueError: Se browser_type inválido
            Exception: Se falhar ao conectar ao navegador
        """
        try:
            # Obter instância singleton do Playwright
            # (criada no tempo de carregamento do módulo, antes do event loop async)
            self.playwright = _get_or_create_playwright()
            logger.info("✅ Usando instância singleton do Playwright")

            # Selecionar tipo de navegador
            if self.browser_type == "chromium":
                browser_launcher = self.playwright.chromium
            elif self.browser_type == "firefox":
                browser_launcher = self.playwright.firefox
            elif self.browser_type == "webkit":
                browser_launcher = self.playwright.webkit
            else:
                raise ValueError(f"Browser type inválido: {self.browser_type}")

            # Lançar navegador
            self.browser = browser_launcher.launch(headless=self.headless)
            logger.info(f"✅ Navegador {self.browser_type} lançado (headless={self.headless})")

            # Criar contexto com viewport customizado
            self.context = self.browser.new_context(viewport=self.viewport)
            logger.info(f"✅ Contexto de navegador criado (viewport: {self.viewport['width']}x{self.viewport['height']})")

            # Criar página
            self.page = self.context.new_page()
            logger.info("✅ Página criada")

            return self.page

        except Exception as e:
            logger.error(f"❌ Erro ao lançar navegador: {str(e)}")
            self.close()
            raise

    def close(self):
        """
        Fechar navegador e limpar recursos.

        Fecha página, contexto e navegador.
        A instância Playwright (thread-local) permanece ativa para outras
        instâncias de PlaywrightBrowserManager na mesma thread.
        """
        try:
            if self.page:
                self.page.close()
                self.page = None
                logger.info("✅ Página fechada")

            if self.context:
                self.context.close()
                self.context = None
                logger.info("✅ Contexto fechado")

            if self.browser:
                self.browser.close()
                self.browser = None
                logger.info("✅ Navegador fechado")

            # Não fechamos self.playwright pois é compartilhada entre
            # múltiplas instâncias de PlaywrightBrowserManager na mesma thread.
            # Será limpa quando a thread terminar.
            self.playwright = None

        except Exception as e:
            logger.error(f"❌ Erro ao fechar navegador: {str(e)}")

    def get_page(self) -> Page:
        """
        Obter página atual ou lançar se não existe.

        Returns:
            Page: Instância de página Playwright
        """
        if self.page is None:
            self.launch()
        return self.page

    def is_ready(self) -> bool:
        """
        Verificar se navegador está pronto para usar.

        Returns:
            bool: True se navegador, contexto e página estão ativos
        """
        return (
            self.playwright is not None
            and self.browser is not None
            and self.context is not None
            and self.page is not None
        )
