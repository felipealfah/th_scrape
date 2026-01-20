"""Serviço de scraping da página Notion de Nichos"""
import logging
import time
from typing import Optional, Dict, Any, List
from playwright.sync_api import Page
from app.core.browser import PlaywrightBrowserManager

logger = logging.getLogger(__name__)


class NotionNichosService:
    """Serviço para extrair dados de nichos da página Notion"""

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

    def _extract_card_details(self, card_element) -> Dict[str, Any]:
        """Extrair detalhes do card (dados visíveis + tentativa de link)"""
        try:
            page = self.get_page()

            # Nome do nicho - procurar em diferentes seletores
            name = "N/A"

            # Procurar pelo div de nome específico (dentro do card, after image)
            name_div = card_element.query_selector(
                "div[style*='position: relative; width: 100%; display: flex;']"
            )
            if name_div:
                name_elem = name_div.query_selector("[contenteditable='false']")
                if name_elem:
                    name = name_elem.text_content().strip()

            # Se não encontrou, tentar span com notion-enable-hover
            if name == "N/A":
                name_elem = card_element.query_selector("span.notion-enable-hover")
                if name_elem:
                    name = name_elem.text_content().strip()

            # Se ainda não encontrou, procurar em spans por tamanho
            if name == "N/A":
                spans = card_element.query_selector_all("span")
                if spans:
                    for span in spans:
                        text = span.text_content().strip()
                        # Filtrar tags (que são muito curtas) e RPM
                        if text and len(text) > 3 and "$" not in text and "RPM" not in text:
                            name = text
                            break

            # Imagem
            image_url = "N/A"
            img_elem = card_element.query_selector("img")
            if img_elem:
                image_url = img_elem.get_attribute("src") or "N/A"

            # RPM (tag em cor laranja)
            rpm = "N/A"
            rpm_elem = card_element.query_selector("div[style*='color: var(--c-oraTexPri)']")
            if rpm_elem:
                span = rpm_elem.query_selector("span")
                if span:
                    rpm = span.text_content().strip()

            # Sub-niche (tag em cor vermelha)
            sub_niche = "N/A"
            sub_niche_elem = card_element.query_selector("div[style*='color: var(--c-redTexPri)']")
            if sub_niche_elem:
                span = sub_niche_elem.query_selector("span")
                if span:
                    sub_niche = span.text_content().strip()

            # URL (tentar extrair do link do card)
            url = "N/A"
            link = card_element.query_selector("a")
            if link:
                href = link.get_attribute("href")
                if href:
                    url = href

            # Retornar dados extraídos (sem clicar para evitar timeouts)
            return {
                "name": name,
                "image_url": image_url,
                "rpm": rpm,
                "sub_niche": sub_niche,
                "data": "N/A",  # Não conseguimos extrair sem clicar
                "place": "N/A",  # Não conseguimos extrair sem clicar
                "url": url
            }

        except Exception as e:
            logger.error(f"⚠️ Erro ao extrair detalhes do card: {str(e)}")
            return {}


    def scrape_nichos(self, notion_url: str, wait_time: int = 15) -> Dict[str, Any]:
        """
        Fazer scraping de nichos da página Notion

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

            # 2. Aguardar carregamento completo
            logger.info("Aguardando carregamento da página...")
            time.sleep(wait_time)

            # 3. Procurar por cards de nichos
            logger.info("Procurando por cards de nichos...")

            # Seletores para encontrar os cards
            cards = page.query_selector_all(".notion-collection-item")
            logger.info(f"Encontrados {len(cards)} cards de nichos")

            # Também tentar seletor alternativo
            if not cards:
                cards = page.query_selector_all("div[data-block-id].notion-page-block")
                logger.info(f"Usando seletor alternativo: encontrados {len(cards)} elementos")

            nichos = []
            h3_sections = page.query_selector_all("h3")

            # Mapear cards por seção
            current_category = "Geral"

            for idx, card in enumerate(cards):
                try:
                    # Tentar determinar a categoria olhando para h3s anteriores
                    card_position = card.evaluate("el => el.getBoundingClientRect().top")

                    for h3 in h3_sections:
                        h3_position = h3.evaluate("el => el.getBoundingClientRect().top")
                        h3_text = h3.text_content().strip()

                        # Se o h3 está acima do card e é mais próximo que o anterior
                        if h3_position < card_position and h3_text:
                            current_category = h3_text

                    logger.info(f"Processando card {idx + 1}/{len(cards)} (Categoria: {current_category})...")
                    card_data = self._extract_card_details(card)

                    if card_data and card_data.get("name") != "N/A":
                        card_data["category"] = current_category
                        nichos.append(card_data)
                        logger.info(f"   ✅ Card extraído: {card_data.get('name')}")
                    else:
                        logger.warning(f"   ⚠️ Card não contém dados válidos")
                except Exception as e:
                    logger.error(f"   ❌ Erro ao processar card {idx + 1}: {str(e)}")
                    continue

            logger.info(f"✅ {len(nichos)} nichos extraídos com sucesso")

            return {
                "success": True,
                "nichos": nichos,
                "total_nichos": len(nichos),
                "url": page.url,
                "error": None,
            }

        except Exception as e:
            logger.error(f"❌ Erro no scraping de nichos: {str(e)}", exc_info=True)
            return {
                "success": False,
                "nichos": [],
                "total_nichos": 0,
                "url": None,
                "error": str(e),
            }
