"""API routes for scraping"""
from fastapi import APIRouter, HTTPException
from app.schemas.scrape import ScrapeRequest, ScrapeResponse
from app.services.scraper import ScraperService
import logging


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["scraping"])


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape(request: ScrapeRequest) -> ScrapeResponse:
    """
    Scrape a webpage and extract data

    - **url**: The URL to scrape
    - **wait_time**: Time to wait for page load (seconds)
    - **selectors**: CSS selectors for data extraction
    """
    try:
        scraper = ScraperService()
        scraper._create_driver()
        try:
            data = scraper.scrape(
                url=request.url,
                wait_time=request.wait_time,
                selectors=request.selectors
            )
            return ScrapeResponse(
                success=True,
                url=request.url,
                data=data,
                error=None
            )
        finally:
            scraper.close()

    except Exception as e:
        logger.error(f"Scraping error: {str(e)}")
        return ScrapeResponse(
            success=False,
            url=request.url,
            data=None,
            error=str(e)
        )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Scrape TH API is running"
    }
