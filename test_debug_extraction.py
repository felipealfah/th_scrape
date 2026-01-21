"""Debug detalhado da extração"""
import logging
from app.core.browser import PlaywrightBrowserManager

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

def debug_extraction():
    """Debug extração card by card"""

    notion_url = "https://victorgonwp.notion.site/PASTA-100-NICHOS-PRO-2e7620bdb33e813db5dac38194635f51"

    logger.info("="*100)
    logger.info("DEBUG: EXTRAÇÃO DE CADA CARD")
    logger.info("="*100)
    logger.info("")

    try:
        browser_manager = PlaywrightBrowserManager(
            headless=True,
            browser_type="chromium"
        )
        page = browser_manager.launch()
        page.goto(notion_url, timeout=120000)

        import time
        time.sleep(15)

        cards = page.query_selector_all("div.notion-collection-item")
        logger.info(f"Total de cards: {len(cards)}\n")

        for card_idx, card in enumerate(cards, 1):
            logger.info(f"CARD #{card_idx}")
            logger.info("-" * 80)

            # Extrair spans
            spans = card.query_selector_all("span")
            logger.info(f"  Spans found: {len(spans)}")

            for span_idx, span in enumerate(spans):
                text = span.text_content().strip()
                classes = span.get_attribute("class") or "no-class"
                logger.info(f"    [{span_idx}] '{text}' (class: {classes})")

            # Extrair URL
            link = card.query_selector("a")
            url = "N/A"
            if link:
                url = link.get_attribute("href") or "N/A"

            logger.info(f"  URL: {url}\n")

        browser_manager.close()

    except Exception as e:
        logger.error(f"❌ ERRO: {str(e)}", exc_info=True)

if __name__ == "__main__":
    debug_extraction()
