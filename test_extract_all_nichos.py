"""Extrair TODOS os 202 nichos usando viewport grande"""
import logging
import json
from app.core.browser import PlaywrightBrowserManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def extract_all_nichos():
    """Extrair todos os nichos com viewport grande"""

    notion_url = "https://victorgonwp.notion.site/PASTA-100-NICHOS-PRO-2e7620bdb33e813db5dac38194635f51"

    logger.info("="*100)
    logger.info("EXTRAÇÃO COMPLETA DE TODOS OS NICHOS")
    logger.info("="*100)
    logger.info("")

    try:
        # Lançar navegador
        logger.info("📱 Lançando navegador...")
        browser_manager = PlaywrightBrowserManager(
            headless=True,
            browser_type="chromium"
        )
        page = browser_manager.launch()
        logger.info("✅ Navegador aberto\n")

        # Acessar página
        logger.info("🌐 Acessando página...")
        page.goto(notion_url, timeout=120000)
        logger.info("✅ Página carregada\n")

        # Configurar viewport GRANDE para renderizar tudo
        logger.info("📏 Configurando viewport grande (1920x10000)...")
        page.set_viewport_size({"width": 1920, "height": 10000})
        logger.info("✅ Viewport configurado\n")

        # Aguardar carregamento
        logger.info("⏳ Aguardando carregamento completo (20s)...")
        import time
        time.sleep(20)
        logger.info("✅ Pronto para extração\n")

        # Extrair TODOS os cards
        logger.info("="*100)
        logger.info("EXTRAINDO TODOS OS CARDS")
        logger.info("="*100)
        logger.info("")

        cards = page.query_selector_all("div.notion-collection-item")
        logger.info(f"📊 Total de cards encontrados: {len(cards)}\n")

        nichos = []
        seen_urls = set()

        for idx, card in enumerate(cards, 1):
            try:
                name = "N/A"
                rpm = "N/A"
                sub_niche = "N/A"
                image_url = "N/A"
                url = "N/A"

                # Extrair spans
                spans = card.query_selector_all("span")

                # Procurar por notion-enable-hover
                name_span = card.query_selector("span.notion-enable-hover")
                if name_span:
                    name = name_span.text_content().strip()
                    if len(spans) > 1:
                        rpm = spans[1].text_content().strip()
                    if len(spans) > 2:
                        sub_niche = spans[2].text_content().strip()
                else:
                    # Sem classe
                    if len(spans) > 0:
                        first_span = spans[0].text_content().strip()
                        if first_span.startswith("$") and "RPM" in first_span:
                            rpm = first_span
                            if len(spans) > 1:
                                name = spans[1].text_content().strip()
                        else:
                            name = first_span
                            if len(spans) > 1:
                                rpm = spans[1].text_content().strip()

                    if len(spans) > 2:
                        sub_niche = spans[2].text_content().strip()

                # Extrair imagem
                img = card.query_selector("img")
                if img:
                    src = img.get_attribute("src")
                    if src:
                        image_url = src

                # Extrair URL
                link = card.query_selector("a")
                if link:
                    href = link.get_attribute("href")
                    if href:
                        url = href

                # Validar
                if url not in seen_urls and url != "N/A" and url.startswith("/") and name != "N/A":
                    seen_urls.add(url)
                    nichos.append({
                        "id": idx,
                        "name": name,
                        "rpm": rpm,
                        "sub_niche": sub_niche,
                        "url": url,
                        "image_url": image_url
                    })

                    # Log a cada 20
                    if len(nichos) % 20 == 0:
                        logger.info(f"  ✅ {len(nichos)} nichos extraídos...")

            except Exception as e:
                logger.debug(f"  ⚠️ Erro ao processar card {idx}: {str(e)}")
                continue

        logger.info("")
        logger.info(f"✅ EXTRAÇÃO COMPLETA: {len(nichos)} nichos extraídos")
        logger.info("")

        # Atribuir categorias
        logger.info("📂 Atribuindo categorias...")
        h3_elements = page.query_selector_all("h3")
        sections = []

        for h3 in h3_elements:
            h3_text = h3.text_content().strip()
            if h3_text:
                try:
                    h3_position = h3.evaluate("el => el.getBoundingClientRect().top")
                    sections.append({
                        "text": h3_text,
                        "position": h3_position
                    })
                except:
                    continue

        sections.sort(key=lambda x: x["position"])
        logger.info(f"✅ {len(sections)} categorias encontradas\n")

        # Atribuir categoria para cada nicho
        for nicho in nichos:
            try:
                current_category = "Sem categoria"
                closest_section_position = -float('inf')

                # Procurar elemento do nicho para obter posição
                url_part = nicho['url'].split('?')[0].split('/')[-1]
                nicho_card = page.query_selector(f"a[href*='{url_part}']")

                if nicho_card:
                    nicho_position = nicho_card.evaluate("el => el.getBoundingClientRect().top")

                    for section in sections:
                        if section["position"] < nicho_position and section["position"] > closest_section_position:
                            closest_section_position = section["position"]
                            current_category = section["text"]

                nicho["category"] = current_category
            except:
                nicho["category"] = "Sem categoria"

        logger.info("="*100)
        logger.info("RESULTADO FINAL")
        logger.info("="*100)
        logger.info("")

        # Agrupar por categoria
        by_category = {}
        for nicho in nichos:
            cat = nicho.get("category", "Sem categoria")
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(nicho)

        logger.info(f"📊 Total: {len(nichos)} nichos em {len(by_category)} categorias\n")

        for category, items in sorted(by_category.items()):
            logger.info(f"  📌 {category}: {len(items)} nichos")

        logger.info("")

        # Mostrar exemplos
        logger.info("📋 Primeiros 10 nichos:")
        for i, nicho in enumerate(nichos[:10], 1):
            logger.info(f"\n   [{i}] {nicho['name']}")
            logger.info(f"       RPM: {nicho['rpm']}")
            logger.info(f"       Sub-nicho: {nicho['sub_niche']}")
            logger.info(f"       Categoria: {nicho.get('category', 'N/A')}")

        if len(nichos) > 10:
            logger.info(f"\n   ... e mais {len(nichos) - 10} nichos")

        # Salvar JSON
        logger.info("")
        logger.info("💾 Salvando dados em JSON...")
        output_file = "/Users/felipefull/Documents/Projetos/scrape_th/nichos_extracted.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "total": len(nichos),
                "categories": len(by_category),
                "nichos": nichos,
                "by_category": {cat: [n['name'] for n in items] for cat, items in by_category.items()}
            }, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Dados salvos em: {output_file}")

        browser_manager.close()

    except Exception as e:
        logger.error(f"❌ ERRO: {str(e)}", exc_info=True)

if __name__ == "__main__":
    extract_all_nichos()
