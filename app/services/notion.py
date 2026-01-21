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


    def scrape_nichos(self, notion_url: str, wait_time: int = 20) -> Dict[str, Any]:
        """
        Fazer scraping de nichos da página Notion

        Args:
            notion_url: URL da página Notion para fazer scraping
            wait_time: Tempo de espera para carregamento em segundos (padrão: 20s)

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

            # 2.5 Fazer scroll repetido para forçar carregamento de TODOS os cards
            logger.info("Fazendo scroll repetido (6x com 3s cada) para carregar conteúdo dinâmico...")
            try:
                # Scroll múltiplo com espera maior entre cada um
                for scroll_num in range(6):
                    pct = (scroll_num + 1) * (100 / 6)
                    logger.info(f"  - Scroll {scroll_num + 1}/6: para {pct:.0f}%...")
                    page.evaluate(f"() => window.scrollTo(0, document.body.scrollHeight * {pct/100})")
                    time.sleep(3)  # 3 segundos entre scrolls

                # Voltar ao topo
                logger.info("  - Voltando ao topo...")
                page.evaluate("() => window.scrollTo(0, 0)")
                time.sleep(2)

                logger.info("✅ Scroll repetido concluído")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao fazer scroll: {str(e)}")

            # 3. Procurar por cards de nichos
            logger.info("Procurando por cards de nichos...")

            # Seletores para encontrar os cards - tentar múltiplas opções
            cards = page.query_selector_all(".notion-collection-item")
            logger.info(f"Seletor 1 (.notion-collection-item): encontrados {len(cards)} cards")

            # Se não encontrou ou encontrou poucos, tentar seletor alternativo
            if len(cards) < 10:
                cards_alt = page.query_selector_all("div[data-block-id].notion-page-block")
                logger.info(f"Seletor 2 (div[data-block-id].notion-page-block): encontrados {len(cards_alt)} cards")
                if len(cards_alt) > len(cards):
                    cards = cards_alt

            # Se ainda não encontrou suficientes, tentar abordagem por posição vertical
            if len(cards) < 20:
                logger.info("Tentando seletor 3: buscar elementos por posição vertical...")
                try:
                    # Procurar por divs que estão entre h3s (estrutura: h3 -> content -> cards -> h3)
                    found_cards = []
                    all_divs = page.query_selector_all("div")

                    for div in all_divs:
                        try:
                            # Verificar se tem img, link E está "entre" h3s (não é muito grande)
                            has_img = div.query_selector("img") is not None
                            has_link = div.query_selector("a") is not None
                            text_length = len(div.text_content().strip())

                            # Card typical: tem img, link, texto entre 20-3000 chars (não muito vazio, não é container gigante)
                            if has_img and has_link and 20 < text_length < 3000:
                                found_cards.append(div)
                        except Exception:
                            continue

                    # Usar JavaScript para remover duplicatas (mesmos elementos DOM)
                    if found_cards:
                        # Filtrar duplicatas usando características únicas (texto + classe)
                        seen_texts = set()
                        unique_cards = []
                        for card in found_cards:
                            try:
                                card_text = card.text_content().strip()[:100]  # Primeiros 100 chars
                                if card_text and card_text not in seen_texts:
                                    unique_cards.append(card)
                                    seen_texts.add(card_text)
                                    if len(unique_cards) >= 200:
                                        break
                            except Exception:
                                continue

                        if unique_cards and len(unique_cards) > len(cards):
                            cards = unique_cards
                            logger.info(f"Seletor 3: encontrados {len(cards)} elementos únicos")
                except Exception as e:
                    logger.warning(f"Erro ao usar seletor 3: {str(e)}")

            logger.info(f"Total de cards encontrados para processar: {len(cards)}")

            nichos = []

            # Extrair seções de h3 com suas posições e textos
            h3_elements = page.query_selector_all("h3")
            sections = []
            for h3 in h3_elements:
                h3_text = h3.text_content().strip()
                if h3_text:  # Ignorar h3s vazios
                    try:
                        h3_position = h3.evaluate("el => el.getBoundingClientRect().top")
                        sections.append({
                            "text": h3_text,
                            "position": h3_position,
                            "element": h3
                        })
                    except Exception as e:
                        logger.warning(f"⚠️ Erro ao calcular posição do h3 '{h3_text}': {str(e)}")
                        continue

            # Ordenar seções por posição (da mais alta para a mais baixa)
            sections.sort(key=lambda x: x["position"])

            logger.info(f"Encontradas {len(sections)} seções de categoria (h3s)")
            for sec in sections:
                logger.info(f"  - {sec['text']} (posição: {sec['position']:.2f})")

            # Mapear cards por seção
            for idx, card in enumerate(cards):
                try:
                    # Determinar a categoria olhando para h3s anteriores
                    card_position = card.evaluate("el => el.getBoundingClientRect().top")

                    # Encontrar o h3 mais próximo que está acima do card
                    current_category = "Sem categoria"
                    closest_section_position = -float('inf')

                    for section in sections:
                        section_position = section["position"]
                        # Se a seção está acima do card e é mais próxima que a anterior
                        if section_position < card_position and section_position > closest_section_position:
                            closest_section_position = section_position
                            current_category = section["text"]

                    logger.info(f"Processando card {idx + 1}/{len(cards)} (Categoria: {current_category})...")
                    card_data = self._extract_card_details(card)

                    if card_data and card_data.get("name") != "N/A":
                        card_data["category"] = current_category
                        nichos.append(card_data)
                        logger.info(f"   ✅ Card extraído: {card_data.get('name')} | RPM: {card_data.get('rpm', 'N/A')}")
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
