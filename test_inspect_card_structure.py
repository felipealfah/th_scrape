"""Script para inspeccionar a estrutura detalhada dos cards Notion"""
import logging
import json
from app.core.browser import PlaywrightBrowserManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def inspect_card_structure():
    """Inspeccionar estrutura HTML detalhada de um card"""

    notion_url = "https://victorgonwp.notion.site/PASTA-100-NICHOS-PRO-2e7620bdb33e813db5dac38194635f51"

    logger.info("="*100)
    logger.info("INSPEÇÃO DETALHADA DA ESTRUTURA DOS CARDS")
    logger.info("="*100)
    logger.info("")

    try:
        # Lançar navegador
        browser_manager = PlaywrightBrowserManager(
            headless=True,
            browser_type="chromium"
        )
        page = browser_manager.launch()

        # Acessar página
        page.goto(notion_url, timeout=120000)

        # Aguardar carregamento
        import time
        time.sleep(15)

        # Obter primeiro card
        cards = page.query_selector_all("div.notion-collection-item")
        logger.info(f"Cards encontrados: {len(cards)}")
        logger.info("")

        if cards:
            first_card = cards[0]

            # 1. HTML completo do card
            html = first_card.evaluate("el => el.outerHTML")
            logger.info("📄 HTML COMPLETO DO PRIMEIRO CARD:")
            logger.info("-" * 100)
            logger.info(html[:3000])  # Mostrar primeiros 3000 caracteres
            logger.info("-" * 100)
            logger.info("")

            # 2. Análise de seletores específicos
            logger.info("🔍 ANÁLISE DE SELETORES:")
            logger.info("")

            # Links
            links = first_card.query_selector_all("a")
            logger.info(f"Links ({len(links)}):")
            for i, link in enumerate(links):
                href = link.get_attribute("href")
                text = link.text_content()
                logger.info(f"  [{i}] href='{href}'")
                logger.info(f"      text='{text[:100]}'")

            logger.info("")

            # Divs com role="button"
            button_divs = first_card.query_selector_all("div[role='button']")
            logger.info(f"Divs com role='button' ({len(button_divs)}):")
            for i, div in enumerate(button_divs[:3]):
                text = div.text_content()
                logger.info(f"  [{i}] text='{text[:100]}'")

            logger.info("")

            # Spans
            spans = first_card.query_selector_all("span")
            logger.info(f"Spans ({len(spans)}):")
            for i, span in enumerate(spans):
                text = span.text_content().strip()
                if text:
                    classes = span.get_attribute("class") or ""
                    logger.info(f"  [{i}] '{text[:80]}' (class='{classes[:60]}')")

            logger.info("")

            # Imagens
            images = first_card.query_selector_all("img")
            logger.info(f"Imagens ({len(images)}):")
            for i, img in enumerate(images):
                src = img.get_attribute("src") or "N/A"
                alt = img.get_attribute("alt") or "N/A"
                logger.info(f"  [{i}] src='{src[:80]}...'")
                logger.info(f"      alt='{alt}'")

            logger.info("")

            # Divs com data-attribute
            logger.info("Divs com atributos data-*:")
            data_divs = first_card.query_selector_all("div[data-block-id]")
            logger.info(f"  Divs com data-block-id: {len(data_divs)}")
            data_divs = first_card.query_selector_all("div[data-id]")
            logger.info(f"  Divs com data-id: {len(data_divs)}")

            logger.info("")

            # 3. Tentar extrair usando diferentes estratégias
            logger.info("="*100)
            logger.info("ESTRATÉGIAS DE EXTRAÇÃO:")
            logger.info("="*100)
            logger.info("")

            # Estratégia 1: Usando primeiro span como nome
            result = {
                "estrategia_1_primeiro_span": "",
                "estrategia_2_link_text": "",
                "estrategia_3_content_editable": "",
                "estrategia_4_aria_label": "",
            }

            spans = first_card.query_selector_all("span")
            if spans:
                for span in spans:
                    text = span.text_content().strip()
                    if text and "$" not in text:  # Não é RPM
                        result["estrategia_1_primeiro_span"] = text
                        break

            # Estratégia 2: Link text
            link = first_card.query_selector("a")
            if link:
                result["estrategia_2_link_text"] = link.text_content().strip()

            # Estratégia 3: contenteditable
            ce = first_card.query_selector("[contenteditable='false']")
            if ce:
                result["estrategia_3_content_editable"] = ce.text_content().strip()

            # Estratégia 4: aria-label
            elem = first_card.query_selector("[aria-label]")
            if elem:
                result["estrategia_4_aria_label"] = elem.get_attribute("aria-label")

            logger.info("Resultados:")
            for strategy, value in result.items():
                logger.info(f"  {strategy}: '{value[:80]}'")

        browser_manager.close()

    except Exception as e:
        logger.error(f"❌ ERRO: {str(e)}", exc_info=True)

if __name__ == "__main__":
    inspect_card_structure()
