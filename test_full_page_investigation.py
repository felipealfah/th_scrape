"""Investigar a página completa com scroll agressivo"""
import logging
import time
from app.core.browser import PlaywrightBrowserManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def investigate_full_page():
    """Investigar página com scroll agressivo sem headless"""

    notion_url = "https://victorgonwp.notion.site/PASTA-100-NICHOS-PRO-2e7620bdb33e813db5dac38194635f51"

    logger.info("="*100)
    logger.info("INVESTIGAÇÃO COMPLETA DA PÁGINA COM SCROLL AGRESSIVO")
    logger.info("="*100)
    logger.info("")

    try:
        # Lançar navegador COM VISUALIZAÇÃO
        logger.info("📱 Lançando navegador COM visualização...")
        browser_manager = PlaywrightBrowserManager(
            headless=False,
            browser_type="chromium"
        )
        page = browser_manager.launch()
        logger.info("✅ Navegador aberto\n")

        # Acessar página
        logger.info("🌐 Acessando página...")
        page.goto(notion_url, timeout=120000)
        logger.info("✅ Página carregada\n")

        # Aguardar carregamento inicial
        logger.info("⏳ Aguardando carregamento inicial (15s)...")
        time.sleep(15)
        logger.info("✅ Pronto para investigação\n")

        # Investigação: fazer scroll até o final
        logger.info("="*100)
        logger.info("COMEÇANDO SCROLL AGRESSIVO ATÉ O FINAL")
        logger.info("="*100)
        logger.info("")

        scroll_count = 0
        last_height = 0
        max_scrolls = 100  # Limite de segurança

        while scroll_count < max_scrolls:
            scroll_count += 1

            # Obter altura atual
            current_height = page.evaluate("() => document.body.scrollHeight")

            # Contar cards
            cards = page.query_selector_all("div.notion-collection-item")
            current_card_count = len(cards)

            logger.info(f"🔄 Scroll #{scroll_count}")
            logger.info(f"   Altura da página: {current_height}px")
            logger.info(f"   Cards no DOM: {current_card_count}")

            # Se não cresceu a altura, chegou ao fim
            if current_height == last_height:
                logger.info(f"   ⚠️ Altura não mudou - tentando 3 mais scrolls...")
                for attempt in range(3):
                    time.sleep(2)
                    page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(3)

                    new_height = page.evaluate("() => document.body.scrollHeight")
                    new_card_count = len(page.query_selector_all("div.notion-collection-item"))

                    logger.info(f"   Attempt {attempt+1}: altura={new_height}px, cards={new_card_count}")

                    if new_height > current_height or new_card_count > current_card_count:
                        last_height = new_height
                        break
                else:
                    logger.info(f"   ✅ FIM DA PÁGINA ATINGIDO!")
                    break
            else:
                last_height = current_height

            # Fazer scroll
            logger.info(f"   📜 Scrollando...")
            page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(4)  # Aguardar carregamento

        # Análise final
        logger.info("")
        logger.info("="*100)
        logger.info("ANÁLISE FINAL")
        logger.info("="*100)
        logger.info("")

        # Contar tudo
        final_cards = page.query_selector_all("div.notion-collection-item")
        final_height = page.evaluate("() => document.body.scrollHeight")
        h3_elements = page.query_selector_all("h3")

        logger.info(f"📊 Dados Finais:")
        logger.info(f"   Total de cards no DOM: {len(final_cards)}")
        logger.info(f"   Altura final da página: {final_height}px")
        logger.info(f"   H3 (categorias) encontrados: {len(h3_elements)}")
        logger.info("")

        logger.info("📋 Categorias encontradas:")
        for h3 in h3_elements[:20]:  # Mostrar primeiras 20
            h3_text = h3.text_content().strip()
            if h3_text:
                logger.info(f"   - {h3_text}")

        logger.info("")
        logger.info("⏳ Navegador permanecerá aberto por 60 segundos para você observar...")
        time.sleep(60)

        browser_manager.close()
        logger.info("✅ Navegador fechado")

    except Exception as e:
        logger.error(f"❌ ERRO: {str(e)}", exc_info=True)

if __name__ == "__main__":
    investigate_full_page()
