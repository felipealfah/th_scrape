"""Explorar página visualmente para entender a estrutura"""
import logging
import time
from app.core.browser import PlaywrightBrowserManager

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

def explore_page():
    """Explorar página visualmente"""

    notion_url = "https://victorgonwp.notion.site/PASTA-100-NICHOS-PRO-2e7620bdb33e813db5dac38194635f51"

    logger.info("="*100)
    logger.info("EXPLORAÇÃO VISUAL DA PÁGINA")
    logger.info("="*100)
    logger.info("")
    logger.info("O navegador abrirá agora. Você pode:")
    logger.info("  - Observar a estrutura visual")
    logger.info("  - Ver se há botões para carregar mais")
    logger.info("  - Checar se há abas ou expandir/colapsar seções")
    logger.info("  - Fazer scroll manual")
    logger.info("")

    try:
        browser_manager = PlaywrightBrowserManager(
            headless=False,
            browser_type="chromium"
        )
        page = browser_manager.launch()

        logger.info("🌐 Acessando página...")
        page.goto(notion_url, timeout=120000)

        logger.info("⏳ Aguardando 15 segundos para carregamento...")
        time.sleep(15)

        logger.info("")
        logger.info("="*100)
        logger.info("ANÁLISE DO CONTEÚDO VISÍVEL")
        logger.info("="*100)
        logger.info("")

        # Análise de botões e elementos interativos
        logger.info("🔍 Procurando por elementos interativos:")

        # Botões "Load more"
        buttons = page.query_selector_all("button")
        logger.info(f"  Botões encontrados: {len(buttons)}")
        for i, btn in enumerate(buttons[:10]):
            text = btn.text_content().strip()[:50]
            if text:
                logger.info(f"    [{i}] {text}")

        # Elementos clicáveis
        clickables = page.query_selector_all("[role='button'], [role='tab'], [role='link']")
        logger.info(f"\n  Elementos clicáveis (role): {len(clickables)}")

        # Procurar por "load more" ou "ver mais"
        logger.info(f"\n  Procurando por 'load', 'more', 'show'...")
        try:
            all_text = page.inner_text("body")
            if "load more" in all_text.lower():
                logger.info(f"    ✅ Encontrado 'load more'")
            if "show more" in all_text.lower():
                logger.info(f"    ✅ Encontrado 'show more'")
            if "ver mais" in all_text.lower():
                logger.info(f"    ✅ Encontrado 'ver mais'")
            if "carregar mais" in all_text.lower():
                logger.info(f"    ✅ Encontrado 'carregar mais'")
        except:
            logger.info(f"    Não foi possível extrair texto da página")

        # Análise de frames (se houver iframe)
        logger.info(f"\n  Iframes encontrados: {len(page.query_selector_all('iframe'))}")

        # Análise de sections/divs com classes relevantes
        logger.info(f"\n  Seções (.notion-collection-view): {len(page.query_selector_all('.notion-collection-view'))}")
        logger.info(f"  Seções (.notion-gallery): {len(page.query_selector_all('.notion-gallery'))}")
        logger.info(f"  Seções (.notion-list): {len(page.query_selector_all('.notion-list'))}")

        # Ver o HTML completo (sample)
        logger.info(f"\n  Tamanho do HTML: {len(page.content())} bytes")

        # Procurar por data-attributes que possam indicar paginação
        logger.info(f"\n  Elementos com data-* que podem indicar carregamento:")
        elements_with_data = page.query_selector_all("[data-*]")
        logger.info(f"    Total: {len(elements_with_data)}")

        logger.info("")
        logger.info("="*100)
        logger.info("PÁGINA ABERTA PARA OBSERVAÇÃO MANUAL")
        logger.info("="*100)
        logger.info("")
        logger.info("⏳ Navegador permanecerá aberto por 300 segundos (5 minutos)")
        logger.info("   Você pode interagir com a página, fazer scroll, clicar em elementos, etc.")
        logger.info("   Quando terminar, a página será fechada automaticamente.")
        logger.info("")

        time.sleep(300)

        browser_manager.close()

    except Exception as e:
        logger.error(f"❌ ERRO: {str(e)}", exc_info=True)

if __name__ == "__main__":
    explore_page()
