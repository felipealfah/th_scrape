"""Debug do viewport"""
import logging
import time
from app.core.browser import PlaywrightBrowserManager

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

url = "https://victorgonwp.notion.site/PASTA-100-NICHOS-PRO-2e7620bdb33e813db5dac38194635f51"

# Teste 1: headless + viewport grande
logger.info("Teste 1: headless=True, viewport=1920x10000")
manager1 = PlaywrightBrowserManager(headless=True, viewport={"width": 1920, "height": 10000})
page1 = manager1.launch()
page1.goto(url)
time.sleep(15)
cards1 = page1.query_selector_all("div.notion-collection-item")
logger.info(f"  Cards encontrados: {len(cards1)}")
manager1.close()

logger.info("")

# Teste 2: headless=False + viewport grande
logger.info("Teste 2: headless=False, viewport=1920x10000")
manager2 = PlaywrightBrowserManager(headless=False, viewport={"width": 1920, "height": 10000})
page2 = manager2.launch()
page2.goto(url)
time.sleep(15)
cards2 = page2.query_selector_all("div.notion-collection-item")
logger.info(f"  Cards encontrados: {len(cards2)}")
logger.info("  Navegador será fechado em 10 segundos...")
time.sleep(10)
manager2.close()
