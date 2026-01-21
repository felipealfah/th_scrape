"""Script para testar scrape Notion COM NAVEGADOR VISÍVEL (headless=False)"""
import logging
import time
from app.core.browser import PlaywrightBrowserManager
from app.services.notion import NotionNichosService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_notion_no_headless():
    """Testar scrape do Notion SEM headless (navegador visível)"""

    # URL da página Notion
    notion_url = "https://victorgonwp.notion.site/PASTA-100-NICHOS-PRO-2e7620bdb33e813db5dac38194635f51"

    logger.info("="*100)
    logger.info("TESTE DE SCRAPE NOTION SEM HEADLESS")
    logger.info("="*100)
    logger.info(f"URL: {notion_url}")
    logger.info("O navegador será aberto visualmente para você observar o comportamento")
    logger.info("")

    try:
        # 1. Criar navegador SEM headless
        logger.info("📱 Lançando navegador sem headless...")
        browser_manager = PlaywrightBrowserManager(
            headless=False,  # ← AQUI: SEM HEADLESS
            browser_type="chromium"
        )
        page = browser_manager.launch()
        logger.info("✅ Navegador aberto")
        logger.info("")

        # 2. Acessar a página
        logger.info("🌐 Acessando página Notion...")
        page.goto(notion_url, timeout=120000)
        logger.info("✅ Página carregada")
        logger.info("")

        # 3. Aguardar carregamento completo
        logger.info("⏳ Aguardando 20 segundos para carregamento completo...")
        logger.info("👀 Observe o navegador: está tudo carregando corretamente?")
        time.sleep(20)
        logger.info("✅ Tempo de espera concluído")
        logger.info("")

        try:
            # 4. Obter informações da página
            logger.info("📊 Analisando estado atual da página...")

            # Contar elementos
            cards_collection = page.query_selector_all(".notion-collection-item")
            cards_block = page.query_selector_all("div[data-block-id].notion-page-block")
            all_cards = cards_collection if cards_collection else cards_block

            logger.info(f"  Cards encontrados: {len(all_cards)}")

            # H3 (categorias)
            h3_elements = page.query_selector_all("h3")
            logger.info(f"  H3 (categorias) encontradas: {len(h3_elements)}")

            if h3_elements:
                logger.info("  Categorias detectadas:")
                for h3 in h3_elements[:10]:  # Mostrar primeiras 10
                    h3_text = h3.text_content().strip()
                    if h3_text:
                        logger.info(f"    - {h3_text}")

            logger.info("")

            # 5. Extrair primeiro card como exemplo
            if all_cards:
                logger.info("🔍 Analisando primeiro card em detalhe...")
                first_card = all_cards[0]

                # HTML do card
                logger.info("\n  📄 Estrutura HTML (primeiros 500 caracteres):")
                try:
                    html = first_card.evaluate("el => el.outerHTML")
                    logger.info(f"     {html[:500]}...")
                except Exception as e:
                    logger.info(f"     Erro ao obter HTML: {str(e)}")

                # Seletores disponíveis
                logger.info("\n  🔎 Seletores encontrados neste card:")

                # Spans
                spans = first_card.query_selector_all("span")
                logger.info(f"     - Spans: {len(spans)}")
                if spans:
                    for i, span in enumerate(spans[:5]):
                        text = span.text_content().strip()[:50]
                        if text:
                            logger.info(f"       [{i}] {text}")

                # Divs com style
                divs_style = first_card.query_selector_all("div[style*='color']")
                logger.info(f"     - Divs com color: {len(divs_style)}")

                # Links
                links = first_card.query_selector_all("a")
                logger.info(f"     - Links: {len(links)}")
                if links:
                    for i, link in enumerate(links[:3]):
                        href = link.get_attribute("href")
                        text = link.text_content().strip()[:50]
                        logger.info(f"       [{i}] href={href}, text={text}")

                # Imagens
                images = first_card.query_selector_all("img")
                logger.info(f"     - Imagens: {len(images)}")
                if images:
                    for i, img in enumerate(images[:3]):
                        src = img.get_attribute("src")
                        alt = img.get_attribute("alt")
                        logger.info(f"       [{i}] src={src[:60]}..., alt={alt}")

        except Exception as e:
            logger.error(f"Erro durante análise: {str(e)}", exc_info=False)

        logger.info("")
        logger.info("="*100)
        logger.info("TESTE CONCLUÍDO - Navegador ainda está aberto para você interagir")
        logger.info("="*100)
        logger.info("⏳ Feche o navegador quando terminar de observar (aguardando 120 segundos...)")

        # Deixar o navegador aberto por mais tempo
        time.sleep(120)

        logger.info("✅ Encerrando...")
        browser_manager.close()
        logger.info("✅ Navegador fechado")

    except Exception as e:
        logger.error(f"❌ ERRO: {str(e)}", exc_info=True)

if __name__ == "__main__":
    test_notion_no_headless()
