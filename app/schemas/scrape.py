"""Scraping request/response schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ScrapeRequest(BaseModel):
    """Request model for scraping"""
    url: str = Field(..., description="URL to scrape")
    wait_time: int = Field(default=10, description="Wait time in seconds for page to load")
    selectors: Optional[Dict[str, str]] = Field(default=None, description="CSS selectors to extract data")

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com",
                "wait_time": 10,
                "selectors": {
                    "title": "h1",
                    "description": ".description"
                }
            }
        }


class ScrapeResponse(BaseModel):
    """Response model for scraping"""
    success: bool = Field(..., description="Whether the scrape was successful")
    url: str = Field(..., description="URL that was scraped")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Extracted data")
    error: Optional[str] = Field(default=None, description="Error message if failed")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "url": "https://example.com",
                "data": {
                    "title": "Example Title",
                    "description": "Example Description"
                },
                "error": None
            }
        }
