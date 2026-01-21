"""Explorar diferentes abordagens para acessar o Notion"""
import logging
import time
from app.core.browser import PlaywrightBrowserManager

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

def test_api_approach():
    """Testar se há uma API ou abordagem alternativa"""

    # URL original
    original_url = "https://victorgonwp.notion.site/PASTA-100-NICHOS-PRO-2e7620bdb33e813db5dac38194635f51"

    # Variações da URL
    urls_to_try = [
        original_url,
        original_url + "?v=c28dcf8e4dcd4b3ba0bef7c9ca30b7f8",  # Com parâmetro v
        original_url.replace("victorgonwp.notion.site", "www.notion.so/victorgonwp"),  # Formato alternativo
    ]

    logger.info("="*100)
    logger.info("TESTE DE DIFERENTES ABORDAGENS")
    logger.info("="*100)
    logger.info("")

    browser_manager = None

    try:
        browser_manager = PlaywrightBrowserManager(
            headless=True,
            browser_type="chromium"
        )
        page = browser_manager.launch()

        for idx, url in enumerate(urls_to_try, 1):
            logger.info(f"\n[{idx}] Testando URL: {url[:80]}...")

            try:
                page.goto(url, timeout=120000, wait_until="domcontentloaded")
                time.sleep(10)

                # Contar cards
                cards = page.query_selector_all("div.notion-collection-item")
                h3s = page.query_selector_all("h3")
                height = page.evaluate("() => document.body.scrollHeight")

                logger.info(f"    ✅ Cards: {len(cards)}, H3s: {len(h3s)}, Height: {height}px")

            except Exception as e:
                logger.info(f"    ❌ Erro: {str(e)[:80]}")

        # Agora vamos tentar descobrir se há uma versão "editable" ou "full"
        logger.info("")
        logger.info("="*100)
        logger.info("TENTANDO EXTRAIR INFORMAÇÕES DE ESTRUTURA")
        logger.info("="*100)
        logger.info("")

        page.goto(original_url, timeout=120000)
        time.sleep(15)

        # Procurar por elementos que possam conter mais dados
        logger.info("Procurando por diferentes seletores de cards...")

        selectors_to_try = [
            "div.notion-collection-item",
            "div[data-block-id]",
            "div.notion-page-block",
            "a[href*='/']",
            "div.notion-card",
            "div.gallery-item",
            "li[data-*]",
        ]

        for selector in selectors_to_try:
            try:
                elements = page.query_selector_all(selector)
                if elements:
                    logger.info(f"  {selector}: {len(elements)} elementos")
            except:
                pass

        # Verificar se há dados em comentários HTML ou atributos data-*
        logger.info("")
        logger.info("Verificando para dados armazenados em atributos...")

        data_attrs = page.query_selector_all("[data-nichos], [data-categories], [data-items]")
        logger.info(f"  Elementos com data-* específicos: {len(data_attrs)}")

        # Procurar por scripts com JSON
        logger.info("")
        logger.info("Procurando por dados JSON em scripts...")

        scripts = page.query_selector_all("script")
        logger.info(f"  Scripts encontrados: {len(scripts)}")

        for idx, script in enumerate(scripts):
            try:
                content = script.text_content()
                if "nichos" in content.lower() or "categories" in content.lower():
                    logger.info(f"    ✅ Script {idx} contém dados relevantes")
                    logger.info(f"       Tamanho: {len(content)} bytes")
                    # Tentar encontrar JSON
                    if "{" in content and "}" in content:
                        logger.info(f"       Contém JSON/objeto")
            except:
                pass

        # Último teste: mudar viewport e tentar carregar mais
        logger.info("")
        logger.info("Tentando aumentar viewport para ver mais conteúdo...")

        page.set_viewport_size({"width": 1920, "height": 5000})
        time.sleep(5)

        cards_after = page.query_selector_all("div.notion-collection-item")
        logger.info(f"  Cards após viewport grande: {len(cards_after)}")

        if browser_manager:
            browser_manager.close()

    except Exception as e:
        logger.error(f"❌ ERRO: {str(e)}", exc_info=True)

if __name__ == "__main__":
    test_api_approach()
