"""Estratégia melhorada de scrape com scroll contínuo para carregar todos os cards"""
import logging
import time
from app.core.browser import PlaywrightBrowserManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_scroll_strategy():
    """Testar estratégia de scroll contínuo para carregar todos os cards"""

    notion_url = "https://victorgonwp.notion.site/PASTA-100-NICHOS-PRO-2e7620bdb33e813db5dac38194635f51"

    logger.info("="*100)
    logger.info("TESTE: ESTRATÉGIA DE SCROLL CONTÍNUO")
    logger.info("="*100)
    logger.info("")

    try:
        # Lançar navegador
        logger.info("📱 Lançando navegador...")
        browser_manager = PlaywrightBrowserManager(
            headless=False,
            browser_type="chromium"
        )
        page = browser_manager.launch()
        logger.info("✅ Navegador aberto")
        logger.info("")

        # Acessar página
        logger.info("🌐 Acessando página Notion...")
        page.goto(notion_url, timeout=120000)
        logger.info("✅ Página carregada")
        logger.info("")

        # Aguardar carregamento inicial
        logger.info("⏳ Aguardando carregamento inicial (15s)...")
        time.sleep(15)
        logger.info("✅ Pronto para scroll")
        logger.info("")

        # Estratégia: Scroll contínuo até não haver mais novos cards
        logger.info("="*100)
        logger.info("COMEÇANDO SCROLL CONTÍNUO COM COLETA DE CARDS")
        logger.info("="*100)
        logger.info("")

        nichos_coletados = []
        urls_vistas = set()
        scroll_count = 0
        last_card_count = 0

        while True:
            scroll_count += 1

            # 1. Contar cards atuais
            cards = page.query_selector_all("div.notion-collection-item")
            current_card_count = len(cards)

            logger.info(f"\n🔄 Scroll #{scroll_count}")
            logger.info(f"   Cards no DOM: {current_card_count}")

            # 2. Extrair dados dos cards que ainda não foram coletados
            cards_novos = 0
            for idx, card in enumerate(cards):
                try:
                    # Extrair dados do card
                    name = "N/A"
                    rpm = "N/A"
                    sub_niche = "N/A"
                    image_url = "N/A"
                    url = "N/A"

                    # Nome
                    spans = card.query_selector_all("span")
                    if spans and len(spans) > 0:
                        name = spans[0].text_content().strip()

                    # RPM (segundo span)
                    if spans and len(spans) > 1:
                        rpm = spans[1].text_content().strip()

                    # Sub-niche (terceiro span)
                    if spans and len(spans) > 2:
                        sub_niche = spans[2].text_content().strip()

                    # Imagem
                    img = card.query_selector("img")
                    if img:
                        image_url = img.get_attribute("src") or "N/A"

                    # URL (link)
                    link = card.query_selector("a")
                    if link:
                        url = link.get_attribute("href") or "N/A"

                    # Verificar se já foi coletado
                    if url not in urls_vistas and url != "N/A":
                        urls_vistas.add(url)
                        nichos_coletados.append({
                            "name": name,
                            "rpm": rpm,
                            "sub_niche": sub_niche,
                            "image_url": image_url,
                            "url": url
                        })
                        cards_novos += 1
                        logger.info(f"   ✅ [{len(nichos_coletados)}] {name}")

                except Exception as e:
                    logger.debug(f"   ⚠️ Erro ao processar card {idx}: {str(e)}")
                    continue

            logger.info(f"   Novos: {cards_novos} | Total coletado: {len(nichos_coletados)}")

            # 3. Verificar se chegou no final
            if current_card_count == last_card_count:
                logger.info(f"\n   ⚠️ Nenhum novo card apareceu após scroll")
                logger.info(f"   Tentando mais 2 scrolls para garantir...")

                for attempt in range(2):
                    time.sleep(2)
                    page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(3)
                    cards = page.query_selector_all("div.notion-collection-item")

                    if len(cards) > last_card_count:
                        logger.info(f"   ✅ Apareceram {len(cards) - last_card_count} novos cards no attempt {attempt + 1}")
                        last_card_count = len(cards)
                        break
                else:
                    logger.info(f"   ✅ Fim da página atingido!")
                    break
            else:
                last_card_count = current_card_count

            # 4. Fazer scroll para baixo
            logger.info(f"   📜 Fazendo scroll...")
            page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(3)  # Aguardar carregamento

        logger.info("")
        logger.info("="*100)
        logger.info(f"✅ SCRAPE CONCLUÍDO: {len(nichos_coletados)} nichos únicos coletados")
        logger.info("="*100)
        logger.info("")

        # Exibir resultado
        logger.info("📋 Primeiros 20 nichos coletados:")
        for i, nicho in enumerate(nichos_coletados[:20], 1):
            logger.info(f"\n   [{i}] {nicho['name']}")
            logger.info(f"       RPM: {nicho['rpm']}")
            logger.info(f"       Sub-nicho: {nicho['sub_niche']}")
            logger.info(f"       URL: {nicho['url']}")

        logger.info("")
        logger.info("⏳ Navegador permanecerá aberto por 60 segundos...")
        time.sleep(60)

        browser_manager.close()
        logger.info("✅ Navegador fechado")

    except Exception as e:
        logger.error(f"❌ ERRO: {str(e)}", exc_info=True)

if __name__ == "__main__":
    test_scroll_strategy()
