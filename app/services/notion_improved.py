"""
Versão melhorada do serviço Notion com detecção JavaScript nativa
"""
import logging
import time
from typing import Optional, Dict, Any, List
from playwright.sync_api import Page
from app.core.browser import PlaywrightBrowserManager

logger = logging.getLogger(__name__)


class NotionNichosServiceImproved:
    """Serviço melhorado para extrair dados de nichos da página Notion"""

    def __init__(self):
        """Inicializar serviço"""
        self.browser_manager: Optional[PlaywrightBrowserManager] = None
        self.page: Optional[Page] = None

    def __enter__(self):
        """Context manager entry"""
        self._create_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def _create_driver(self) -> Page:
        """Criar navegador Playwright"""
        try:
            logger.info("Lançando navegador Playwright para Notion...")
            self.browser_manager = PlaywrightBrowserManager(
                headless=True,
                browser_type="chromium"
            )
            self.page = self.browser_manager.launch()
            logger.info("✅ Navegador Playwright criado")
            return self.page

        except Exception as e:
            logger.error(f"❌ Erro ao criar navegador: {str(e)}")
            self.close()
            raise

    def get_page(self) -> Page:
        """Obter ou criar página Playwright"""
        if self.page is None:
            self._create_driver()
        return self.page

    def close(self):
        """Fechar navegador Playwright"""
        if self.browser_manager:
            try:
                self.browser_manager.close()
                logger.info("✅ Navegador fechado")
            except Exception as e:
                logger.error(f"Erro ao fechar navegador: {str(e)}")
            finally:
                self.browser_manager = None
                self.page = None

    def scrape_nichos(self, notion_url: str, wait_time: int = 25) -> Dict[str, Any]:
        """
        Fazer scraping de nichos da página Notion usando JavaScript nativo

        Args:
            notion_url: URL da página Notion para fazer scraping
            wait_time: Tempo de espera para carregamento em segundos

        Returns:
            Dicionário com lista de nichos extraídos
        """
        try:
            page = self.get_page()

            # 1. Acessar página
            logger.info(f"Acessando página Notion: {notion_url}")
            page.goto(notion_url, timeout=120000)
            logger.info("✅ Página acessada")

            # 2. Aguardar carregamento
            logger.info(f"Aguardando {wait_time}s para carregamento...")
            time.sleep(wait_time)

            # 3. Scroll progressivo para carregar conteúdo dinâmico
            logger.info("Fazendo scroll progressivo para carregar todo conteúdo...")
            for i in range(1, 5):
                pct = i * 25
                logger.info(f"  - Scroll {i}/4: {pct}%")
                page.evaluate(f"() => window.scrollTo(0, document.body.scrollHeight * {pct/100})")
                time.sleep(2)

            logger.info("  - Voltando ao topo...")
            page.evaluate("() => window.scrollTo(0, 0)")
            time.sleep(2)
            logger.info("✅ Scroll concluído")

            # 4. Usar JavaScript para extrair TODA a estrutura
            logger.info("Extraindo estrutura completa usando JavaScript...")

            extraction_result = page.evaluate("""() => {
                const result = {
                    sections: [],
                    cards_by_section: {}
                };

                // Procurar por h3s (seções de categorias)
                const h3s = document.querySelectorAll('h3');
                logger.info(`Encontrados ${h3s.length} h3s`);

                h3s.forEach((h3, idx) => {
                    const sectionName = h3.textContent.trim();
                    if (!sectionName) return;

                    const sectionData = {
                        index: idx,
                        name: sectionName,
                        position: h3.getBoundingClientRect().top,
                        cards: []
                    };

                    logger.info(`H3[${idx}]: "${sectionName}"`);

                    // Procurar cards após este h3
                    let sibling = h3.nextElementSibling;
                    let cardCount = 0;

                    while (sibling && sibling.tagName !== 'H3') {
                        // Procurar .notion-collection-item dentro
                        const items = sibling.querySelectorAll('.notion-collection-item');
                        cardCount += items.length;

                        // Procurar divs com img + link
                        const divs = sibling.querySelectorAll('div');
                        divs.forEach(div => {
                            const hasImg = div.querySelector('img') !== null;
                            const hasLink = div.querySelector('a') !== null;
                            const textLen = div.textContent.trim().length;

                            if (hasImg && hasLink && textLen > 20 && textLen < 3000) {
                                // Verificar se é único (não tem cards filhos)
                                if (!div.querySelector('.notion-collection-item')) {
                                    sectionData.cards.push({
                                        element: div,
                                        textPreview: div.textContent.trim().substring(0, 100)
                                    });
                                }
                            }
                        });

                        sibling = sibling.nextElementSibling;
                    }

                    if (sectionData.cards.length > 0) {
                        result.sections.push(sectionData);
                        result.cards_by_section[sectionName] = sectionData.cards.length;
                    }
                });

                return {
                    total_sections: result.sections.length,
                    cards_by_section: result.cards_by_section,
                    structure: result.sections.map(s => ({
                        name: s.name,
                        card_count: s.cards.length
                    }))
                };
            }""")

            logger.info(f"\nEstrutura extraída via JavaScript:")
            logger.info(f"Total de seções: {extraction_result['total_sections']}")
            logger.info(f"Cards por seção: {extraction_result['cards_by_section']}")

            return {
                "success": True,
                "nichos": [],  # TODO: Implementar extração de dados
                "total_nichos": 0,
                "url": page.url,
                "error": None,
                "debug_info": extraction_result
            }

        except Exception as e:
            logger.error(f"❌ Erro no scraping: {str(e)}", exc_info=True)
            return {
                "success": False,
                "nichos": [],
                "total_nichos": 0,
                "url": None,
                "error": str(e),
            }
