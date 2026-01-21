"""Teste da extração de dados CORRIGIDA"""
import logging
from app.services.notion import NotionNichosService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_extraction():
    """Testar extração corrigida"""

    notion_url = "https://victorgonwp.notion.site/PASTA-100-NICHOS-PRO-2e7620bdb33e813db5dac38194635f51"

    logger.info("="*100)
    logger.info("TESTE DE EXTRAÇÃO CORRIGIDA")
    logger.info("="*100)
    logger.info("")

    try:
        with NotionNichosService() as service:
            logger.info("🚀 Iniciando scrape...")
            result = service.scrape_nichos(notion_url, wait_time=15)

            if result["success"]:
                logger.info(f"\n✅ SCRAPE CONCLUÍDO COM SUCESSO")
                logger.info(f"   Total de nichos: {result['total_nichos']}")
                logger.info("")

                logger.info("📋 Primeiros 10 nichos extraídos:")
                for i, nicho in enumerate(result["nichos"][:10], 1):
                    logger.info(f"\n   [{i}] {nicho.get('name', 'N/A')}")
                    logger.info(f"       RPM: {nicho.get('rpm', 'N/A')}")
                    logger.info(f"       Sub-nicho: {nicho.get('sub_niche', 'N/A')}")
                    logger.info(f"       Categoria: {nicho.get('category', 'N/A')}")
                    logger.info(f"       URL: {nicho.get('url', 'N/A')[:60]}")

                if result["total_nichos"] > 10:
                    logger.info(f"\n   ... e mais {result['total_nichos'] - 10} nichos")

            else:
                logger.error(f"❌ Erro no scrape: {result['error']}")

    except Exception as e:
        logger.error(f"❌ ERRO: {str(e)}", exc_info=True)

if __name__ == "__main__":
    test_extraction()
