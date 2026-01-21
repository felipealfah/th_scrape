"""Serviço de scraping da página Notion de Nichos"""
import logging
import time
from typing import Optional, Dict, Any, List
from playwright.sync_api import Page
from app.core.browser import PlaywrightBrowserManager

logger = logging.getLogger(__name__)


class NotionNichosService:
    """Serviço para extrair dados de nichos da página Notion"""

    def __init__(self, headless: bool = False, viewport: Optional[Dict] = None):
        """Inicializar serviço (headless=False necessário para renderizar Notion)"""
        self.headless = headless
        self.viewport = viewport or {"width": 1920, "height": 10000}
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
        """Criar navegador Playwright com viewport grande para renderizar todos os cards"""
        try:
            logger.info("Lançando navegador Playwright para Notion...")
            self.browser_manager = PlaywrightBrowserManager(
                headless=self.headless,
                browser_type="chromium",
                viewport=self.viewport
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
        """Extrair detalhes do card tratando estruturas variáveis"""
        try:
            page = self.get_page()

            name = "N/A"
            rpm = "N/A"
            sub_niche = "N/A"
            image_url = "N/A"
            url = "N/A"

            # 1. Extrair spans do card
            spans = card_element.query_selector_all("span")

            # Tratamento de estruturas variáveis:
            # Estrutura 1 (com notion-enable-hover): [nome, RPM, sub-niche]
            # Estrutura 2 (sem notion-enable-hover): [RPM, nome/categoria, ...]

            if spans:
                # Procurar pelo span com class "notion-enable-hover" (é sempre o nome)
                name_span = card_element.query_selector("span.notion-enable-hover")
                if name_span:
                    # Encontrou estrutura 1: span com classe
                    name = name_span.text_content().strip()
                    # RPM é o segundo span
                    if len(spans) > 1:
                        rpm = spans[1].text_content().strip()
                    # Sub-niche é o terceiro span
                    if len(spans) > 2:
                        sub_niche = spans[2].text_content().strip()
                else:
                    # Estrutura 2: sem classe no nome
                    # spans[0] = RPM (contém "$X RPM")
                    # spans[1] = Nome/Categoria
                    # spans[2+] = Mais detalhes se houver

                    if len(spans) > 0:
                        first_span = spans[0].text_content().strip()
                        # Se começa com "$", é RPM
                        if first_span.startswith("$") and "RPM" in first_span:
                            rpm = first_span
                            # Nome é o segundo span
                            if len(spans) > 1:
                                name = spans[1].text_content().strip()
                        else:
                            # Se não começa com "$", assume que é nome
                            name = first_span
                            if len(spans) > 1:
                                rpm = spans[1].text_content().strip()

                    # Sub-niche pode estar em terceiro
                    if len(spans) > 2:
                        sub_niche = spans[2].text_content().strip()

            # 2. Extrair imagem
            img_elem = card_element.query_selector("img")
            if img_elem:
                src = img_elem.get_attribute("src")
                if src:
                    image_url = src

            # 3. Extrair URL do link
            link = card_element.query_selector("a")
            if link:
                href = link.get_attribute("href")
                if href:
                    url = href

            # Retornar dados extraídos
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

            logger.info("\n" + "=" * 100)
            logger.info("EXTRAÇÃO COMPLETA DE TODOS OS NICHOS")
            logger.info("=" * 100)

            nichos = []
            seen_urls = set()

            # Extrair TODOS os cards
            logger.info("\nProcurando por cards no DOM...")
            cards = page.query_selector_all("div.notion-collection-item")
            logger.info(f"✅ {len(cards)} cards encontrados\n")

            logger.info("3️⃣ EXTRAIR: Extraindo dados dos cards...")
            for idx_card, card in enumerate(cards, 1):
                try:
                    card_data = self._extract_card_details(card)

                    if not card_data or card_data.get("name") == "N/A":
                        continue

                    url = card_data.get("url", "N/A")

                    # Verificar se já foi extraído
                    if url in seen_urls:
                        continue

                    # Validar dados
                    if url == "N/A" or url == "#main" or not url.startswith("/"):
                        continue

                    image_url = card_data.get("image_url", "N/A")
                    if "/icons/" in image_url or image_url.endswith(".svg"):
                        continue

                    # ✅ Card válido - adicionar
                    nichos.append(card_data)
                    seen_urls.add(url)

                    # Log a cada 20
                    if len(nichos) % 20 == 0:
                        logger.info(f"   ✅ {len(nichos)} nichos extraídos...")

                except Exception as e:
                    logger.debug(f"   Erro ao extrair card {idx_card}: {str(e)}")
                    continue

            logger.info(f"\n✅ Extração concluída: {len(nichos)} nichos únicos coletados")

            # 5. Atribuir categorias aos nichos extraídos
            logger.info("\nAtribuindo categorias aos nichos...")
            h3_elements = page.query_selector_all("h3")
            sections = []
            for h3 in h3_elements:
                h3_text = h3.text_content().strip()
                if h3_text:
                    try:
                        h3_position = h3.evaluate("el => el.getBoundingClientRect().top")
                        sections.append({
                            "text": h3_text,
                            "position": h3_position
                        })
                        logger.info(f"  - {h3_text} (posição: {h3_position:.2f})")
                    except Exception:
                        continue

            sections.sort(key=lambda x: x["position"])

            # 6. Atribuir categoria para cada nicho
            for nicho in nichos:
                try:
                    current_category = "Sem categoria"
                    closest_section_position = -float('inf')

                    # Procurar elemento do nicho no DOM para obter posição
                    url_part = nicho.get('url', '').split('?')[0].split('/')[-1]
                    nicho_card = page.query_selector(f"a[href*='{url_part}']")

                    if nicho_card:
                        nicho_position = nicho_card.evaluate("el => el.getBoundingClientRect().top")

                        for section in sections:
                            if section["position"] < nicho_position and section["position"] > closest_section_position:
                                closest_section_position = section["position"]
                                current_category = section["text"]

                    nicho["category"] = current_category
                except Exception:
                    nicho["category"] = "Sem categoria"

            logger.info(f"✅ {len(nichos)} nichos com categorias atribuídas")

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
