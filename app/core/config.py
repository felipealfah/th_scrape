"""Application configuration"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # App
    APP_NAME: str = "Scrape TH API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Selenium
    SELENIUM_URL: str = "http://selenium-chrome:4444"
    SELENIUM_HEADLESS: bool = True
    SELENIUM_TIMEOUT: int = 30

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # TubeHunt
    url_login: str = "https://app.tubehunt.io/login"
    user: str = ""
    password: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
