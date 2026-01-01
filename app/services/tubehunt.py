"""Serviço de automação de login e scrape no TubeHunt"""
import logging
import time
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from app.core.config import settings

logger = logging.getLogger(__name__)


class TubeHuntService:
    """Serviço para automatizar login e extração de dados do TubeHunt"""

    def __init__(self):
        """Inicializar serviço com configurações"""
        self.login_url = settings.url_login
        self.username = settings.user
        self.password = settings.password
        self.selenium_url = settings.SELENIUM_URL
        self.timeout = settings.SELENIUM_TIMEOUT
        self.driver: Optional[WebDriver] = None

    def __enter__(self):
        """Context manager entry"""
        self._create_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def _create_driver(self) -> WebDriver:
        """Criar WebDriver remoto ou local"""
        try:
            # Configurar opções do Chrome
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            if settings.SELENIUM_HEADLESS:
                chrome_options.add_argument("--headless")

            logger.info(f"Conectando ao Selenium: {self.selenium_url}")

            # Tentar conexão remota primeiro
            try:
                self.driver = webdriver.Remote(
                    command_executor=self.selenium_url,
                    options=chrome_options
                )
                logger.info("✅ WebDriver remoto criado")
            except Exception as e:
                # Se falhar, usar WebDriver local
                logger.warning(f"Falha na conexão remota ({self.selenium_url}): {e}")
                logger.info("Tentando WebDriver local...")
                self.driver = webdriver.Chrome(options=chrome_options)
                logger.info("✅ WebDriver local criado")

            return self.driver

        except Exception as e:
            logger.error(f"❌ Erro ao criar WebDriver: {str(e)}")
            raise

    def get_driver(self) -> WebDriver:
        """Obter ou criar WebDriver"""
        if self.driver is None:
            self._create_driver()
        return self.driver

    def close(self):
        """Fechar WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("✅ WebDriver fechado")
            except Exception as e:
                logger.error(f"Erro ao fechar WebDriver: {str(e)}")
            finally:
                self.driver = None

    def _access_login_page(self):
        """1. Acessar página de login"""
        logger.info(f"Acessando página de login: {self.login_url}")
        driver = self.get_driver()
        driver.get(self.login_url)
        time.sleep(2)
        logger.info("✅ Página de login carregada")

    def _find_email_field(self) -> Any:
        """2. Localizar campo de email"""
        logger.info("Localizando campo de email...")
        driver = self.get_driver()

        email_selectors = [
            (By.ID, "email"),
            (By.NAME, "email"),
            (By.XPATH, "//input[@type='email']"),
            (By.CSS_SELECTOR, "input[type='email']"),
        ]

        for by, selector in email_selectors:
            try:
                email_input = driver.find_element(by, selector)
                logger.info(f"✅ Campo de email encontrado: {by}={selector}")
                return email_input
            except:
                continue

        logger.error("❌ Campo de email não encontrado")
        raise Exception("Campo de email não encontrado")

    def _find_password_field(self) -> Any:
        """3. Localizar campo de password"""
        logger.info("Localizando campo de password...")
        driver = self.get_driver()

        password_selectors = [
            (By.ID, "password"),
            (By.NAME, "password"),
            (By.XPATH, "//input[@type='password']"),
            (By.CSS_SELECTOR, "input[type='password']"),
        ]

        for by, selector in password_selectors:
            try:
                password_input = driver.find_element(by, selector)
                logger.info(f"✅ Campo de password encontrado: {by}={selector}")
                return password_input
            except:
                continue

        logger.error("❌ Campo de password não encontrado")
        raise Exception("Campo de password não encontrado")

    def _fill_credentials(self):
        """4. Preencher email e password"""
        logger.info("Preenchendo credenciais...")

        # Email
        email_input = self._find_email_field()
        email_input.clear()
        email_input.send_keys(self.username)
        time.sleep(1)
        logger.info(f"✅ Email preenchido: {self.username}")

        # Password
        password_input = self._find_password_field()
        password_input.clear()
        password_input.send_keys(self.password)
        time.sleep(1)
        logger.info("✅ Password preenchido")

    def _find_submit_button(self) -> Any:
        """5. Localizar botão de submit"""
        logger.info("Localizando botão de submit...")
        driver = self.get_driver()

        submit_selectors = [
            (By.XPATH, "//button[@type='submit']"),
            (By.XPATH, "//button[contains(text(), 'Login')]"),
            (By.XPATH, "//button[contains(text(), 'login')]"),
            (By.XPATH, "//button[contains(text(), 'Entrar')]"),
            (By.CSS_SELECTOR, "button[type='submit']"),
        ]

        for by, selector in submit_selectors:
            try:
                button = driver.find_element(by, selector)
                logger.info(f"✅ Botão encontrado: {by}={selector}")
                return button
            except:
                continue

        logger.error("❌ Botão de submit não encontrado")
        raise Exception("Botão de submit não encontrado")

    def _submit_form(self):
        """6. Submeter formulário"""
        logger.info("Submetendo formulário...")
        submit_button = self._find_submit_button()
        submit_button.click()
        time.sleep(2)
        logger.info("✅ Formulário submetido")

    def _wait_for_redirect(self):
        """7. Aguardar redirecionamento"""
        logger.info(f"Aguardando redirecionamento (timeout: {self.timeout}s)...")
        time.sleep(3)  # Dar tempo para redirecionar

        driver = self.get_driver()
        current_url = driver.current_url
        logger.info(f"✅ URL atual: {current_url}")

        if self.login_url in current_url:
            logger.warning("⚠️ Ainda na página de login - possível falha de login")

        return current_url

    def _extract_element(self, selector: str) -> Optional[str]:
        """8. Extrair elemento selecionado"""
        logger.info(f"Extraindo elemento: {selector}")
        driver = self.get_driver()

        try:
            # Se for um seletor CSS padrão (ex: h1, .class, #id)
            if selector.startswith("#"):
                elements = driver.find_elements(By.ID, selector[1:])
            elif selector.startswith("."):
                elements = driver.find_elements(By.CLASS_NAME, selector[1:])
            else:
                # Assumir que é um tag name (h1, h2, etc)
                elements = driver.find_elements(By.TAG_NAME, selector)

            if not elements:
                # Tentar como CSS selector genérico
                elements = driver.find_elements(By.CSS_SELECTOR, selector)

            if elements:
                text = elements[0].text
                logger.info(f"✅ Elemento extraído: '{text}'")
                return text
            else:
                logger.warning(f"⚠️ Elemento '{selector}' não encontrado")
                # Retornar title como fallback
                fallback = driver.title
                logger.info(f"✅ Usando title como fallback: '{fallback}'")
                return fallback

        except Exception as e:
            logger.warning(f"Erro ao extrair elemento: {e}")
            # Retornar title como fallback
            fallback = driver.title
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
            # Garantir que o driver foi criado
            self.get_driver()

            # 1. Fazer login
            self._access_login_page()
            self._fill_credentials()
            self._submit_form()
            self._wait_for_redirect()

            # 2. Navegar para página de vídeos
            videos_url = "https://app.tubehunt.io/long/?page=1&OrderBy=DateDESC&ChangePerPage=50"
            logger.info(f"Navegando para página de vídeos: {videos_url}")

            driver = self.get_driver()
            driver.set_page_load_timeout(120)  # 2 minutos

            try:
                driver.get(videos_url)
                logger.info("✅ Página de vídeos acessada")
            except Exception as e:
                logger.warning(f"⚠️ Timeout ao acessar página, continuando: {e}")
                time.sleep(5)

            # 3. Aguardar carregamento
            logger.info("Aguardando carregamento da página...")
            wait = WebDriverWait(driver, wait_time)

            try:
                # Esperar por elementos de vídeo
                wait.until(EC.presence_of_all_elements_located((By.XPATH, "//*[contains(@class, 'item')]")))
                logger.info("✅ Items carregados")
            except:
                logger.warning("⚠️ Timeout aguardando items, continuando")

            time.sleep(2)

            # 4. Extrair informações da página
            logger.info("Extraindo informações da página...")

            video_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'video')]")
            links = driver.find_elements(By.TAG_NAME, "a")
            images = driver.find_elements(By.TAG_NAME, "img")
            buttons = driver.find_elements(By.TAG_NAME, "button")

            current_url = driver.current_url
            page_title = driver.title

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
            # Informações básicas
            channel_name_elem = channel_card.find_element(By.CSS_SELECTOR, "a.fw-semibold.fs-4")
            channel_name = channel_name_elem.text
            channel_link = channel_name_elem.get_attribute("href")

            # Handle (@) do canal
            channel_handle_elem = channel_card.find_element(By.CSS_SELECTOR, ".small .fw-bold")
            channel_handle = channel_handle_elem.text

            # País
            country_elem = channel_card.find_element(By.CSS_SELECTOR, ".country")
            country = country_elem.text.strip()

            # Inscritos
            subscribers_text = channel_card.find_element(By.CSS_SELECTOR, ".small.text-secondary").text
            # Extrai "2k inscritos" de um texto como "@latelyfashionable • 2k inscritos • ..."
            subscribers = subscribers_text.split("•")[1].strip().replace("inscritos", "").strip()

            # Verificado (presença do ícone)
            is_verified = False
            try:
                channel_card.find_element(By.CSS_SELECTOR, "i.bi-patch-check-fill")
                is_verified = True
            except:
                pass

            # Monetizado (presença do ícone)
            is_monetized = False
            try:
                channel_card.find_element(By.CSS_SELECTOR, "i.bi-currency-dollar")
                is_monetized = True
            except:
                pass

            # Extrair stats cards
            stat_cards = channel_card.find_elements(By.CSS_SELECTOR, ".stat-card")
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
                        stat_value = stat_cards[idx].find_element(By.CSS_SELECTOR, ".fs-4.fw-semibold").text
                        stats[label] = stat_value
                    else:
                        stats[label] = "N/A"
                except:
                    stats[label] = "N/A"

            # Extrair vídeos
            recent_videos = []
            video_elements = channel_card.find_elements(By.CSS_SELECTOR, ".entry-video")

            for video_elem in video_elements:
                try:
                    video_link_elem = video_elem.find_element(By.CSS_SELECTOR, "a")
                    video_link = video_link_elem.get_attribute("href")

                    thumbnail_elem = video_elem.find_element(By.CSS_SELECTOR, ".video-thumb")
                    thumbnail_url = thumbnail_elem.get_attribute("src")

                    # Duração
                    duration = "N/A"
                    try:
                        duration_elem = video_elem.find_element(By.CSS_SELECTOR, ".duration")
                        duration = duration_elem.text
                    except:
                        pass

                    # Título
                    title_elem = video_elem.find_element(By.CSS_SELECTOR, ".mt-2.mb-2.text-dark.fw-semibold.small")
                    title = title_elem.text

                    # Stats do vídeo (views, comentários, tempo)
                    stats_text = video_elem.find_element(By.CSS_SELECTOR, ".small.text-secondary").text
                    # Formato: "2k views • 3 comentários • há 1 mês"
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
                "recent_videos": recent_videos[:6]  # Limitar a 6 vídeos
            }

        except Exception as e:
            logger.error(f"❌ Erro ao extrair dados do canal: {str(e)}")
            raise

    def scrape_channels(self, wait_time: int = 15) -> Dict[str, Any]:
        """
        Fazer login, navegar para página de canais e extrair dados detalhados

        Args:
            wait_time: Tempo de espera para carregamento

        Returns:
            Dicionário com lista de canais e informações
        """
        try:
            # Garantir que o driver foi criado
            self.get_driver()

            # 1. Fazer login
            self._access_login_page()
            self._fill_credentials()
            self._submit_form()
            self._wait_for_redirect()

            # 2. Aguardar carregamento completo da página principal
            logger.info("Aguardando carregamento completo da página principal...")
            driver = self.get_driver()
            wait = WebDriverWait(driver, wait_time)

            try:
                # Esperar por algum elemento principal ser visível
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".container, main, .page")))
                logger.info("✅ Página principal carregada")
            except:
                logger.warning("⚠️ Timeout aguardando página principal, continuando...")

            time.sleep(2)

            # 3. Navegar para página de canais
            channels_url = "https://app.tubehunt.io/long/?page=1&OrderBy=DateDESC&ChangePerPage=50"
            logger.info(f"Navegando para página de canais: {channels_url}")

            driver.set_page_load_timeout(120)  # 2 minutos

            try:
                driver.get(channels_url)
                logger.info("✅ Página de canais acessada")
            except Exception as e:
                logger.warning(f"⚠️ Timeout ao acessar página, continuando: {e}")
                time.sleep(5)

            # 4. Aguardar carregamento da página de canais
            logger.info("Aguardando carregamento da página de canais...")
            wait = WebDriverWait(driver, wait_time)

            try:
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".channel-card")))
                logger.info("✅ Canais carregados")
            except:
                logger.warning("⚠️ Timeout aguardando canais, continuando...")

            time.sleep(2)

            # 5. Extrair dados de todos os canais
            logger.info("Extraindo dados dos canais...")
            channels = []
            channel_cards = driver.find_elements(By.CSS_SELECTOR, ".channel-card")

            logger.info(f"Encontrados {len(channel_cards)} canais para extrair")

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
                "url": driver.current_url,
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
            # Garantir que o driver foi criado
            self.get_driver()

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
