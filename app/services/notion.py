"""Serviço de scraping da página Notion de Nichos"""
import logging
import time
import json
from typing import Optional, Dict, Any, List
from playwright.sync_api import Page, sync_playwright
from app.core.browser import PlaywrightBrowserManager

logger = logging.getLogger(__name__)


class NotionNichosServiceAPI:
    """Serviço melhorado que usa API interception para extrair dados (baseado em test_ext.py)"""

    def __init__(self, headless: bool = True, viewport: Optional[Dict] = None):
        """Inicializar serviço com interception de API

        Viewport: 1920x1080 é o padrão para Notion
        """
        self.headless = headless
        self.viewport = viewport or {"width": 1920, "height": 1080}
        self.collected_responses = []
        self.niches = []

    def _get_niches_with_positions(self, page) -> List[Dict]:
        """Extrair nichos pelos elementos <h3>"""
        logger.info("▶ Mapeando nichos pelo DOM (<h3>)...")

        niches = []
        h3s = page.query_selector_all("h3")

        for h in h3s:
            try:
                text = h.inner_text().strip() if hasattr(h, 'inner_text') else h.text_content().strip()
                if not text:
                    continue

                y = h.evaluate("el => el.getBoundingClientRect().top + window.scrollY")

                niches.append({
                    "name": text,
                    "y": y
                })
            except:
                pass

        niches.sort(key=lambda x: x["y"])

        logger.info(f"✅ Nichos encontrados: {len(niches)}")
        for n in niches:
            logger.info(f"   - {n['name']}")

        return niches

    def _assign_niche_by_position(self, rows: List[Dict], niches: List[Dict], page) -> List[Dict]:
        """Atribuir nicho por posição dos cards"""
        logger.info("▶ Atribuindo nichos aos canais (via cards da tabela)...")

        # Pegar todos os cards visíveis da tabela
        cards = page.query_selector_all("div.notion-collection-item")
        logger.info(f"   Cards encontrados no DOM: {len(cards)}")

        card_positions = []

        for c in cards:
            try:
                text = c.inner_text().strip() if hasattr(c, 'inner_text') else c.text_content().strip()
                if not text:
                    continue

                y = c.evaluate("el => el.getBoundingClientRect().top + window.scrollY")

                card_positions.append({
                    "text": text,
                    "y": y
                })
            except:
                pass

        # Mapear rows
        for row in rows:
            row["niche"] = None
            title = (row.get("title") or "").strip()

            if not title:
                continue

            # Achar card correspondente pelo título
            matched_y = None
            for c in card_positions:
                if title in c["text"]:
                    matched_y = c["y"]
                    break

            if matched_y is None:
                continue

            # Achar nicho acima
            current = None
            for n in niches:
                if n["y"] <= matched_y:
                    current = n["name"]
                else:
                    break

            row["niche"] = current

        return rows

    def scrape_nichos(self, notion_url: str, wait_time: int = 20) -> Dict[str, Any]:
        """Fazer scraping de nichos da página Notion usando API interception"""
        try:
            logger.info("▶ Abrindo Notion e interceptando API...")
            self.collected_responses = []

            with sync_playwright() as p:
                # ========================
                # FASE 1: Interceptar API
                # ========================
                logger.info("FASE 1: Interceptando respostas da API Notion...")

                browser = p.chromium.launch(headless=self.headless)
                ctx = browser.new_context(viewport=self.viewport)
                page = ctx.new_page()

                # Handler para respostas
                def handle_response(resp):
                    try:
                        if "queryCollection" in resp.url or "syncRecordValues" in resp.url:
                            try:
                                self.collected_responses.append(resp.json())
                                logger.debug(f"📥 API: {resp.url.split('/')[-1]}")
                            except:
                                pass
                    except:
                        pass

                page.on("response", handle_response)

                # Abrir página
                logger.info(f"Navegando para: {notion_url}")
                page.goto(notion_url, timeout=120_000)
                logger.info(f"▶ Aguardando render inicial ({wait_time}s)...")
                time.sleep(wait_time)

                # Scroll leve para garantir lazy-load
                logger.info("▶ Scroll leve para garantir lazy-load...")
                for i in range(12):
                    page.mouse.wheel(0, 3000)
                    time.sleep(1.5)
                    if (i + 1) % 4 == 0:
                        logger.debug(f"   Scroll {i + 1}/12...")

                logger.info("▶ Esperando últimas respostas...")
                time.sleep(8)

                # Ler nichos do DOM
                self.niches = self._get_niches_with_positions(page)

                browser.close()

            # ========================
            # FASE 2: Extrair Rows da API
            # ========================
            logger.info(f"\n✅ Responses capturadas: {len(self.collected_responses)}")
            logger.info("FASE 2: Extraindo dados das respostas da API...")

            rows = []

            for blob in self.collected_responses:
                rm = blob.get("recordMap", {}).get("block", {})
                for b in rm.values():
                    v = b.get("value", {})
                    if v.get("type") == "page" and "properties" in v:
                        props = v["properties"]
                        row = {}
                        for k, val in props.items():
                            row[k] = "".join(x[0] for x in val if x)
                        rows.append(row)

            # Remover duplicados
            unique = {json.dumps(r, sort_keys=True): r for r in rows}
            rows = list(unique.values())

            logger.info(f"✅ TOTAL DE CANAIS (API): {len(rows)}")

            # ========================
            # FASE 3: Atribuir Nicho
            # ========================
            logger.info("FASE 3: Atribuindo nichos aos canais...")

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                ctx = browser.new_context(viewport=self.viewport)
                page = ctx.new_page()
                page.goto(notion_url, timeout=120_000)
                time.sleep(20)

                rows = self._assign_niche_by_position(rows, self.niches, page)

                browser.close()

            # ========================
            # FASE 4: Normalizar e retornar
            # ========================
            logger.info("FASE 4: Normalizando dados...")

            canais = []

            for r in rows:
                title = r.get("title")
                url = r.get("YhHt")  # Campo de URL
                rpm = r.get("V>qb")   # Campo de RPM
                tags = r.get("}zd>")  # Campo de tags
                niche = r.get("niche", "Sem nicho")

                if not title or not url or not url.startswith("http"):
                    continue

                canais.append({
                    "name": title.strip(),
                    "youtube_url": url.strip(),
                    "rpm": rpm.replace(" RPM", "").replace("$", "").strip() if rpm else None,
                    "tags": [t.strip() for t in tags.split(",")] if isinstance(tags, str) else [],
                    "niche": niche,
                    "url": url.strip()
                })

            logger.info(f"\n✅ TOTAL FINAL DE CANAIS: {len(canais)}")
            logger.info("=" * 80)

            return {
                "success": True,
                "nichos": canais,
                "total_nichos": len(canais),
                "url": notion_url,
                "error": None,
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


class NotionNichosService:
    """Serviço para extrair dados de nichos da página Notion"""

    def __init__(self, headless: bool = False, viewport: Optional[Dict] = None):
        """Inicializar serviço (headless=False necessário para renderizar Notion)

        Viewport ótimo: 1920x1080 (renderiza 202 cards)
        - 1280x720: apenas 9 cards
        - 1920x1080: 202 cards (MÁXIMO)
        - 1920x5000: 123 cards
        - 1920x10000: 165 cards
        """
        self.headless = headless
        self.viewport = viewport or {"width": 1920, "height": 1080}
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
