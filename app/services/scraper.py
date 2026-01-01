"""Selenium-based web scraper service"""
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from app.core.config import settings
from typing import Optional, Dict, Any
import logging


logger = logging.getLogger(__name__)


class ScraperService:
    """Service for web scraping with Selenium"""

    def __init__(self, selenium_url: Optional[str] = None):
        """Initialize scraper with remote Selenium server"""
        self.selenium_url = selenium_url or settings.SELENIUM_URL
        self.driver: Optional[WebDriver] = None

    def __enter__(self):
        """Context manager entry"""
        self._create_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def _create_driver(self) -> WebDriver:
        """Create remote Selenium WebDriver"""
        try:
            chrome_options = Options()
            if settings.SELENIUM_HEADLESS:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

            self.driver = webdriver.Remote(
                command_executor=self.selenium_url,
                options=chrome_options
            )
            logger.info("Selenium WebDriver created successfully")
            return self.driver
        except Exception as e:
            logger.error(f"Failed to create WebDriver: {str(e)}")
            raise

    def get_driver(self) -> WebDriver:
        """Get or create WebDriver"""
        if self.driver is None:
            self._create_driver()
        return self.driver

    def close(self):
        """Close the WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {str(e)}")
            finally:
                self.driver = None

    def scrape(
        self,
        url: str,
        wait_time: int = 10,
        selectors: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Scrape a webpage and extract data using CSS selectors

        Args:
            url: URL to scrape
            wait_time: Maximum time to wait for page load in seconds
            selectors: Dictionary of {field_name: css_selector}

        Returns:
            Dictionary with extracted data
        """
        try:
            driver = self.get_driver()
            driver.get(url)

            # Wait for page to load
            WebDriverWait(driver, wait_time).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "body"))
            )

            extracted_data = {}

            if selectors:
                for field_name, selector in selectors.items():
                    try:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            # Return list of text if multiple elements, single text if one
                            if len(elements) == 1:
                                extracted_data[field_name] = elements[0].text
                            else:
                                extracted_data[field_name] = [elem.text for elem in elements]
                        else:
                            extracted_data[field_name] = None
                    except Exception as e:
                        logger.warning(f"Error extracting {field_name}: {str(e)}")
                        extracted_data[field_name] = None
            else:
                # Return page title and HTML if no selectors provided
                extracted_data["title"] = driver.title
                extracted_data["url"] = driver.current_url

            return extracted_data

        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            raise

    def screenshot(self, url: str, filename: str = "screenshot.png") -> str:
        """Take a screenshot of a webpage"""
        try:
            driver = self.get_driver()
            driver.get(url)
            driver.save_screenshot(filename)
            logger.info(f"Screenshot saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            raise
