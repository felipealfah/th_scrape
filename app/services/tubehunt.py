"""Serviço de automação de login e scrape no TubeHunt usando Playwright"""
import logging
import time
from typing import Optional, Dict, Any
from playwright.sync_api import Page
from app.core.browser import PlaywrightBrowserManager
from app.core.config import settings

logger = logging.getLogger(__name__)


class TubeHuntService:
    """Serviço para automatizar login e extração de dados do TubeHunt com Playwright"""

    def __init__(self):
        """Inicializar serviço com configurações"""
        self.login_url = settings.url_login
        self.username = settings.user
        self.password = settings.password
        self.timeout = settings.SELENIUM_TIMEOUT
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
            logger.info("Lançando navegador Playwright...")
            self.browser_manager = PlaywrightBrowserManager(
                headless=settings.SELENIUM_HEADLESS,
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

    def _access_login_page(self):
        """1. Acessar página de login"""
        logger.info(f"Acessando página de login: {self.login_url}")
        page = self.get_page()
        page.goto(self.login_url, timeout=120000)
        # Esperar formulário de login carregar
        try:
            page.wait_for_selector("input[type='email']", timeout=30000)
        except:
            logger.warning("⚠️ Formulário não carregou no tempo esperado, continuando...")
        time.sleep(3)
        logger.info("✅ Página de login carregada")

    def _find_email_field(self) -> Any:
        """2. Localizar campo de email"""
        logger.info("Localizando campo de email...")
        page = self.get_page()

        email_selectors = [
            "#email",
            "input[name='email']",
            "input[type='email']",
        ]

        for selector in email_selectors:
            try:
                element = page.query_selector(selector)
                if element:
                    logger.info(f"✅ Campo de email encontrado: {selector}")
                    return element
            except Exception:
                continue

        logger.error("❌ Campo de email não encontrado")
        raise Exception("Campo de email não encontrado")

    def _find_password_field(self) -> Any:
        """3. Localizar campo de password"""
        logger.info("Localizando campo de password...")
        page = self.get_page()

        password_selectors = [
            "#password",
            "input[name='password']",
            "input[type='password']",
        ]

        for selector in password_selectors:
            try:
                element = page.query_selector(selector)
                if element:
                    logger.info(f"✅ Campo de password encontrado: {selector}")
                    return element
            except Exception:
                continue

        logger.error("❌ Campo de password não encontrado")
        raise Exception("Campo de password não encontrado")

    def _fill_credentials(self):
        """4. Preencher email e password"""
        logger.info("Preenchendo credenciais...")
        page = self.get_page()

        # Preencher email
        email_field = self._find_email_field()
        email_field.fill(self.username)
        time.sleep(2)
        logger.info(f"✅ Email preenchido: {self.username}")

        # Preencher password
        password_field = self._find_password_field()
        password_field.fill(self.password)
        time.sleep(2)
        logger.info("✅ Password preenchido")

    def _find_submit_button(self) -> Any:
        """5. Localizar botão de submit"""
        logger.info("Localizando botão de submit...")
        page = self.get_page()

        submit_selectors = [
            "button[type='submit']",
            "button:has-text('Login')",
            "button:has-text('login')",
            "button:has-text('Entrar')",
        ]

        for selector in submit_selectors:
            try:
                element = page.query_selector(selector)
                if element:
                    logger.info(f"✅ Botão encontrado: {selector}")
                    return element
            except Exception:
                continue

        logger.error("❌ Botão de submit não encontrado")
        raise Exception("Botão de submit não encontrado")

    def _submit_form(self):
        """6. Submeter formulário"""
        logger.info("Submetendo formulário...")
        page = self.get_page()
        submit_button = self._find_submit_button()

        # Esperar botão estar visível e interativo antes de clicar
        try:
            page.wait_for_selector("button[type='submit']:enabled", timeout=10000)
        except:
            logger.warning("⚠️ Botão não ficou habilitado, tentando mesmo assim...")

        # Clicar no botão SEM aguardar navegação
        # Usar no_wait_after=True para não aguardar a navegação que pode levar muito tempo
        logger.info("Clicando no botão de login...")
        submit_button.click(no_wait_after=True)
        logger.info("✅ Formulário submetido (aguardando redirecionamento...)")

        # Aguardar um pouco para navegação ser iniciada
        time.sleep(3)

    def _wait_for_redirect(self):
        """7. Aguardar redirecionamento - verificar se login foi bem-sucedido"""
        logger.info(f"Aguardando redirecionamento do login...")
        page = self.get_page()

        # Aguardar a página mudar de URL (sinal de que login foi processado)
        max_wait = 30  # segundos (reducido pois o click já esperou)
        start_time = time.time()
        login_url_initial = page.url

        while time.time() - start_time < max_wait:
            current_url = page.url
            logger.info(f"URL atual: {current_url}")

            # Se saiu da página de login E não tem erro, login foi bem-sucedido
            if "login" not in current_url.lower() and "error" not in current_url.lower():
                logger.info(f"✅ Login realizado com sucesso! Redirecionado para: {current_url}")
                time.sleep(2)
                return current_url

            # Se tem erro na URL, login falhou
            if "error" in current_url.lower():
                logger.error(f"❌ Erro detectado na URL: {current_url}")
                return current_url

            time.sleep(1)

        # Se chegou aqui e ainda está em login, tenta aguardar page load mesmo assim
        current_url = page.url
        logger.warning(f"⚠️ URL não mudou após 30s. Tentando esperar page load...")

        try:
            page.wait_for_load_state("domcontentloaded", timeout=10000)
            logger.info("✅ DOM carregou mesmo com URL em /login")
        except Exception as e:
            logger.warning(f"⚠️ Timeout no wait_for_load_state: {e}")

        return current_url

    def _extract_element(self, selector: str) -> Optional[str]:
        """8. Extrair elemento selecionado"""
        logger.info(f"Extraindo elemento: {selector}")
        page = self.get_page()

        try:
            # Converter seletores CSS simples
            if selector.startswith("#"):
                css_selector = selector
            elif selector.startswith("."):
                css_selector = selector
            else:
                # Assumir que é um tag name
                css_selector = selector

            element = page.query_selector(css_selector)

            if element:
                text = element.text_content()
                logger.info(f"✅ Elemento extraído: '{text}'")
                return text
            else:
                logger.warning(f"⚠️ Elemento '{selector}' não encontrado")
                # Retornar title como fallback
                fallback = page.title()
                logger.info(f"✅ Usando title como fallback: '{fallback}'")
                return fallback

        except Exception as e:
            logger.warning(f"Erro ao extrair elemento: {e}")
            # Retornar title como fallback
            fallback = page.title()
            logger.info(f"✅ Usando title como fallback: '{fallback}'")
            return fallback

    def navigate_to_videos(self, wait_time: int = 15) -> Dict[str, Any]:
        """
        Fazer login e navegar até página de vídeos com paginação

        Args:
            wait_time: Tempo de espera para carregamento

        Returns:
            Dicionário com informações da página de vídeos
        """
        try:
            # Garantir que a página foi criada
            self.get_page()

            # 1. Fazer login
            self._access_login_page()
            self._fill_credentials()
            self._submit_form()
            self._wait_for_redirect()

            # 2. Navegar para página de vídeos
            videos_url = "https://app.tubehunt.io/long/?page=1&OrderBy=DateDESC&ChangePerPage=50"
            logger.info(f"Navegando para página de vídeos: {videos_url}")

            page = self.get_page()

            try:
                page.goto(videos_url, timeout=120000)
                logger.info("✅ Página de vídeos acessada")
            except Exception as e:
                logger.warning(f"⚠️ Timeout ao acessar página, continuando: {e}")
                time.sleep(5)

            # 3. Aguardar carregamento
            logger.info("Aguardando carregamento da página...")

            try:
                page.wait_for_selector(".item", timeout=wait_time * 1000)
                logger.info("✅ Items carregados")
            except Exception:
                logger.warning("⚠️ Timeout aguardando items, continuando")

            time.sleep(2)

            # 4. Extrair informações da página
            logger.info("Extraindo informações da página...")

            video_elements = page.query_selector_all(".video")
            links = page.query_selector_all("a")
            images = page.query_selector_all("img")
            buttons = page.query_selector_all("button")

            current_url = page.url
            page_title = page.title()

            logger.info("✅ Informações extraídas com sucesso")

            return {
                "success": True,
                "url": current_url,
                "title": page_title,
                "video_elements_count": len(video_elements),
                "links_count": len(links),
                "images_count": len(images),
                "buttons_count": len(buttons),
                "error": None,
            }

        except Exception as e:
            logger.error(f"❌ Erro na navegação: {str(e)}", exc_info=True)
            return {
                "success": False,
                "url": None,
                "title": None,
                "video_elements_count": 0,
                "links_count": 0,
                "images_count": 0,
                "buttons_count": 0,
                "error": str(e),
            }

    def _extract_channel_data(self, channel_card) -> Dict[str, Any]:
        """Extrair dados de um card de canal individual"""
        try:
            page = self.get_page()

            # Informações básicas
            channel_name_elem = channel_card.query_selector("a.fw-semibold.fs-4")
            channel_name = channel_name_elem.text_content() if channel_name_elem else "N/A"
            channel_link = channel_name_elem.get_attribute("href") if channel_name_elem else "N/A"

            # Handle (@) do canal
            channel_handle_elem = channel_card.query_selector(".small .fw-bold")
            channel_handle = channel_handle_elem.text_content() if channel_handle_elem else "N/A"

            # País
            country_elem = channel_card.query_selector(".country")
            country = country_elem.text_content().strip() if country_elem else "N/A"

            # Inscritos
            subscribers_elem = channel_card.query_selector(".small.text-secondary")
            subscribers_text = subscribers_elem.text_content() if subscribers_elem else ""
            subscribers = (
                subscribers_text.split("•")[1].strip().replace("inscritos", "").strip()
                if "•" in subscribers_text
                else "N/A"
            )

            # Verificado (presença do ícone)
            is_verified = bool(channel_card.query_selector("i.bi-patch-check-fill"))

            # Monetizado (presença do ícone)
            is_monetized = bool(channel_card.query_selector("i.bi-currency-dollar"))

            # Extrair stats cards
            stat_cards = channel_card.query_selector_all(".stat-card")
            stats = {}
            stat_labels = [
                "total_views",
                "views_last_60_days",
                "average_views_per_video",
                "time_since_first_video",
                "total_videos",
                "outlier_score"
            ]

            for idx, label in enumerate(stat_labels):
                try:
                    if idx < len(stat_cards):
                        stat_value_elem = stat_cards[idx].query_selector(".fs-4.fw-semibold")
                        stat_value = stat_value_elem.text_content() if stat_value_elem else "N/A"
                        stats[label] = stat_value
                    else:
                        stats[label] = "N/A"
                except Exception:
                    stats[label] = "N/A"

            # Extrair vídeos
            recent_videos = []
            video_elements = channel_card.query_selector_all(".entry-video")

            for video_elem in video_elements:
                try:
                    video_link_elem = video_elem.query_selector("a")
                    video_link = video_link_elem.get_attribute("href") if video_link_elem else "N/A"

                    thumbnail_elem = video_elem.query_selector(".video-thumb")
                    thumbnail_url = thumbnail_elem.get_attribute("src") if thumbnail_elem else "N/A"

                    # Duração
                    duration = "N/A"
                    duration_elem = video_elem.query_selector(".duration")
                    if duration_elem:
                        duration = duration_elem.text_content()

                    # Título
                    title_elem = video_elem.query_selector(".mt-2.mb-2.text-dark.fw-semibold.small")
                    title = title_elem.text_content() if title_elem else "N/A"

                    # Stats do vídeo
                    stats_elem = video_elem.query_selector(".small.text-secondary")
                    stats_text = stats_elem.text_content() if stats_elem else ""
                    parts = [p.strip() for p in stats_text.split("•")]

                    views = parts[0].replace("views", "").strip() if len(parts) > 0 else "N/A"
                    comments = parts[1].replace("comentários", "").strip() if len(parts) > 1 else "N/A"
                    uploaded_time = parts[2] if len(parts) > 2 else "N/A"

                    recent_videos.append({
                        "title": title,
                        "video_link": video_link,
                        "thumbnail_url": thumbnail_url,
                        "duration": duration,
                        "views": views,
                        "comments": comments,
                        "uploaded_time": uploaded_time
                    })
                except Exception as e:
                    logger.warning(f"Erro ao extrair vídeo: {e}")
                    continue

            return {
                "channel_name": channel_name,
                "channel_link": channel_link,
                "channel_handle": channel_handle,
                "country": country,
                "subscribers": subscribers,
                "is_verified": is_verified,
                "is_monetized": is_monetized,
                "total_views": stats.get("total_views", "N/A"),
                "views_last_60_days": stats.get("views_last_60_days", "N/A"),
                "average_views_per_video": stats.get("average_views_per_video", "N/A"),
                "time_since_first_video": stats.get("time_since_first_video", "N/A"),
                "total_videos": stats.get("total_videos", "N/A"),
                "outlier_score": stats.get("outlier_score", "N/A"),
                "recent_videos": recent_videos[:6]
            }

        except Exception as e:
            logger.error(f"❌ Erro ao extrair dados do canal: {str(e)}")
            raise

    def scrape_channels(self, wait_time: int = 15, scrape_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Fazer login, navegar para página de canais e extrair dados detalhados

        Args:
            wait_time: Tempo de espera para carregamento
            scrape_url: URL customizada para scraping (opcional, usa padrão se não fornecida)

        Returns:
            Dicionário com lista de canais e informações
        """
        try:
            # Garantir que a página foi criada
            self.get_page()

            # 1. Fazer login
            self._access_login_page()
            self._fill_credentials()
            self._submit_form()
            self._wait_for_redirect()

            # 2. Aguardar carregamento completo da página principal
            logger.info("Aguardando carregamento completo da página principal...")
            page = self.get_page()

            try:
                page.wait_for_selector(".container, main, .page", timeout=wait_time * 1000)
                logger.info("✅ Página principal carregada")
            except Exception:
                logger.warning("⚠️ Timeout aguardando página principal, continuando...")

            time.sleep(2)

            # 3. Navegar para página de canais
            # Usar URL customizada se fornecida, caso contrário usar padrão
            if not scrape_url:
                scrape_url = "https://app.tubehunt.io/long/?page=1&OrderBy=DateDESC&ChangePerPage=50"
            logger.info(f"Navegando para página de canais: {scrape_url}")

            try:
                page.goto(scrape_url, timeout=120000)
                logger.info("✅ Página de canais acessada")
            except Exception as e:
                logger.warning(f"⚠️ Timeout ao acessar página, continuando: {e}")
                time.sleep(5)

            # 4. Aguardar carregamento da página de canais
            logger.info("Aguardando carregamento da página de canais...")

            channels_loaded = False
            try:
                page.wait_for_selector(".channel-card", timeout=wait_time * 1000)
                logger.info("✅ Elementos de canal carregados no DOM")
                channels_loaded = True
            except Exception as e:
                logger.warning(f"⚠️ Timeout aguardando .channel-card: {str(e)}")

            # Aguardar um pouco mais para elementos ficarem visíveis
            time.sleep(3)

            # 5. Extrair dados de todos os canais
            logger.info("Extraindo dados dos canais...")
            channels = []
            channel_cards = page.query_selector_all(".channel-card")

            logger.info(f"Encontrados {len(channel_cards)} canais para extrair")

            if len(channel_cards) == 0:
                logger.warning("⚠️ Nenhum elemento .channel-card encontrado!")
                logger.info("Tentando seladores alternativos...")
                # Tentar outros seletores
                channel_cards = page.query_selector_all("[data-testid*='channel'], .card, [class*='channel']")
                logger.info(f"Encontrados {len(channel_cards)} elementos com seletores alternativos")

            for idx, channel_card in enumerate(channel_cards):
                try:
                    channel_data = self._extract_channel_data(channel_card)
                    channels.append(channel_data)
                    logger.info(f"✅ Canal {idx + 1}/{len(channel_cards)} extraído: {channel_data['channel_name']}")
                except Exception as e:
                    logger.error(f"❌ Erro ao processar canal {idx + 1}: {str(e)}")
                    continue

            logger.info(f"✅ {len(channels)} canais extraídos com sucesso")

            return {
                "success": True,
                "channels": channels,
                "total_channels": len(channels),
                "url": page.url,
                "error": None,
            }

        except Exception as e:
            logger.error(f"❌ Erro no scraping de canais: {str(e)}", exc_info=True)
            return {
                "success": False,
                "channels": [],
                "total_channels": 0,
                "url": None,
                "error": str(e),
            }

    def login_and_extract(self, wait_time: int = 15, extract_selector: str = "h1") -> Dict[str, Any]:
        """
        Executar fluxo completo de login e extração

        Args:
            wait_time: Tempo de espera para carregamento
            extract_selector: Seletor CSS para elemento a extrair

        Returns:
            Dicionário com resultado da operação
        """
        try:
            # Garantir que a página foi criada
            self.get_page()

            # 1. Acessar página de login
            self._access_login_page()

            # 2-6. Preencher credenciais e submeter
            self._fill_credentials()
            self._submit_form()

            # 7. Aguardar redirecionamento
            current_url = self._wait_for_redirect()

            # 8. Extrair elemento
            extracted_text = self._extract_element(extract_selector)

            logger.info("✅ Login e extração concluídos com sucesso")

            return {
                "success": True,
                "h1_text": extracted_text,
                "url": current_url,
                "error": None,
            }

        except Exception as e:
            logger.error(f"❌ Erro no login: {str(e)}", exc_info=True)
            return {
                "success": False,
                "h1_text": None,
                "url": None,
                "error": str(e),
            }
