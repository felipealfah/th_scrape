#!/usr/bin/env python3
"""
Test improved Notion scraping with better card detection
"""
import logging
from app.services.notion import NotionNichosService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_improved_notion():
    """Test improved Notion scraping"""
    notion_url = "https://victorgonwp.notion.site/PASTA-100-NICHOS-PRO-2e7620bdb33e813db5dac38194635f51"

    logger.info("=" * 100)
    logger.info("TESTE DE SCRAPING NOTION MELHORADO")
    logger.info("=" * 100)
    logger.info(f"URL: {notion_url}\n")

    try:
        with NotionNichosService() as service:
            result = service.scrape_nichos(
                notion_url=notion_url,
                wait_time=25  # Tempo maior para garantir carregamento
            )

            if result.get("success"):
                logger.info("\n" + "=" * 100)
                logger.info("✅ SUCESSO!")
                logger.info("=" * 100)

                nichos = result.get("nichos", [])
                total = result.get("total_nichos", 0)

                logger.info(f"Total de nichos extraídos: {total}\n")

                # Agrupar por categoria
                by_category = {}
                for nicho in nichos:
                    cat = nicho.get("category", "Sem categoria")
                    if cat not in by_category:
                        by_category[cat] = []
                    by_category[cat].append(nicho)

                logger.info("RESUMO POR CATEGORIA:")
                logger.info("-" * 100)
                for category in sorted(by_category.keys()):
                    items = by_category[category]
                    logger.info(f"\n{category}: {len(items)} nichos")
                    for item in items[:3]:  # Primeiros 3
                        logger.info(f"  • {item.get('name', 'N/A')} (RPM: {item.get('rpm', 'N/A')})")
                    if len(items) > 3:
                        logger.info(f"  ... e mais {len(items) - 3}")

                logger.info("\n" + "=" * 100)
                logger.info(f"✅ Total: {len(by_category)} categorias, {total} nichos extraídos")
                logger.info("=" * 100)
            else:
                logger.error("\n❌ ERRO NO SCRAPING:")
                logger.error(f"   {result.get('error')}")

    except Exception as e:
        logger.error(f"\n❌ EXCEÇÃO: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_improved_notion()
