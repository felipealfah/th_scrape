"""Schemas para TubeHunt"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TubeHuntLoginRequest(BaseModel):
    """Request model para login e scrape no TubeHunt"""
    wait_time: int = Field(default=15, ge=5, le=60, description="Tempo de espera em segundos para carregamento da página")
    extract_selector: str = Field(default="h1", description="Seletor CSS para elemento a extrair (default: h1)")

    class Config:
        json_schema_extra = {
            "example": {
                "wait_time": 15,
                "extract_selector": "h1"
            }
        }


class TubeHuntLoginResponse(BaseModel):
    """Response model para login e scrape no TubeHunt"""
    success: bool = Field(..., description="Indica se o login e extração foram bem-sucedidos")
    h1_text: Optional[str] = Field(None, description="Texto do elemento extraído")
    url: Optional[str] = Field(None, description="URL após o login")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp da requisição")
    error: Optional[str] = Field(None, description="Mensagem de erro se falhou")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "h1_text": "TubeHunt.io",
                "url": "https://app.tubehunt.io/",
                "timestamp": "2026-01-01T18:51:36.640000",
                "error": None
            }
        }


class TubeHuntVideosResponse(BaseModel):
    """Response model para navegação até página de vídeos"""
    success: bool = Field(..., description="Indica se a navegação foi bem-sucedida")
    url: Optional[str] = Field(None, description="URL da página de vídeos")
    title: Optional[str] = Field(None, description="Título da página")
    video_elements_count: int = Field(default=0, description="Número de elementos com classe 'video'")
    links_count: int = Field(default=0, description="Número de links na página")
    images_count: int = Field(default=0, description="Número de imagens na página")
    buttons_count: int = Field(default=0, description="Número de botões na página")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp da requisição")
    error: Optional[str] = Field(None, description="Mensagem de erro se falhou")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "url": "https://app.tubehunt.io/long/?page=1&OrderBy=DateDESC&ChangePerPage=50",
                "title": "TubeHunt.io",
                "video_elements_count": 538,
                "links_count": 459,
                "images_count": 322,
                "buttons_count": 6,
                "timestamp": "2026-01-01T19:07:46.000000",
                "error": None
            }
        }


class VideoData(BaseModel):
    """Dados de um vídeo"""
    title: str = Field(..., description="Título do vídeo")
    video_link: str = Field(..., description="Link do vídeo no YouTube")
    thumbnail_url: str = Field(..., description="URL da thumbnail do vídeo")
    duration: Optional[str] = Field(None, description="Duração do vídeo (ex: '1:53')")
    views: Optional[str] = Field(None, description="Número de views (ex: '2k')")
    comments: Optional[str] = Field(None, description="Número de comentários")
    uploaded_time: Optional[str] = Field(None, description="Tempo desde o upload (ex: 'há 1 mês')")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Day One of cleaning my sewing studio, ten minutes at a time.",
                "video_link": "https://youtube.com/watch?v=3iHy-TGCV1A",
                "thumbnail_url": "https://i.ytimg.com/vi/3iHy-TGCV1A/mqdefault.jpg",
                "duration": "1:53",
                "views": "2k",
                "comments": "3",
                "uploaded_time": "há 1 mês"
            }
        }


class ChannelData(BaseModel):
    """Dados completos de um canal"""
    # Informações básicas
    channel_name: str = Field(..., description="Nome do canal")
    channel_link: str = Field(..., description="Link do canal")
    channel_handle: str = Field(..., description="@ do canal (handle)")
    country: str = Field(..., description="País do canal")
    subscribers: str = Field(..., description="Número de inscritos (ex: '2k')")
    is_verified: bool = Field(default=False, description="Se o canal é verificado")
    is_monetized: bool = Field(default=False, description="Se o canal é monetizado")
    categories: list[str] = Field(default_factory=list, description="Categorias do canal (ex: ['Military', 'Politics', 'Society'])")

    # Estatísticas
    total_views: str = Field(..., description="Total de views em vídeos longos")
    views_last_60_days: str = Field(..., description="Views em vídeos < 60 dias")
    average_views_per_video: str = Field(..., description="Média de views por vídeo")
    time_since_first_video: str = Field(..., description="Tempo desde o primeiro vídeo")
    total_videos: str = Field(..., description="Total de vídeos")
    outlier_score: str = Field(..., description="Outlier Score (ex: '71×')")

    # Vídeos
    recent_videos: list[VideoData] = Field(default_factory=list, description="6 últimos vídeos populares")

    class Config:
        json_schema_extra = {
            "example": {
                "channel_name": "Lately Fashionable",
                "channel_link": "/channel/UCyzJxq0foatsp3-ZwSuCKBg",
                "channel_handle": "@latelyfashionable",
                "country": "US",
                "subscribers": "2k",
                "is_verified": True,
                "is_monetized": True,
                "categories": ["Fashion", "Lifestyle"],
                "total_views": "149k",
                "views_last_60_days": "14k",
                "average_views_per_video": "981",
                "time_since_first_video": "há 6 anos",
                "total_videos": "152",
                "outlier_score": "71×",
                "recent_videos": [
                    {
                        "title": "Day One of cleaning my sewing studio...",
                        "video_link": "https://youtube.com/watch?v=3iHy-TGCV1A",
                        "thumbnail_url": "https://i.ytimg.com/vi/3iHy-TGCV1A/mqdefault.jpg",
                        "duration": "1:53",
                        "views": "2k",
                        "comments": "3",
                        "uploaded_time": "há 1 mês"
                    }
                ]
            }
        }


class ChannelsListResponse(BaseModel):
    """Response model para scraping de canais"""
    success: bool = Field(..., description="Indica se o scraping foi bem-sucedido")
    channels: list[ChannelData] = Field(default_factory=list, description="Lista de canais extraídos")
    total_channels: int = Field(default=0, description="Total de canais extraídos")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp da requisição")
    error: Optional[str] = Field(None, description="Mensagem de erro se falhou")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "channels": [
                    {
                        "channel_name": "Lately Fashionable",
                        "channel_link": "/channel/UCyzJxq0foatsp3-ZwSuCKBg",
                        "channel_handle": "@latelyfashionable",
                        "country": "US",
                        "subscribers": "2k",
                        "is_verified": True,
                        "is_monetized": True,
                        "categories": ["Fashion", "Lifestyle"],
                        "total_views": "149k",
                        "views_last_60_days": "14k",
                        "average_views_per_video": "981",
                        "time_since_first_video": "há 6 anos",
                        "total_videos": "152",
                        "outlier_score": "71×",
                        "recent_videos": []
                    }
                ],
                "total_channels": 1,
                "timestamp": "2026-01-01T20:00:00.000000",
                "error": None
            }
        }


class HealthCheckResponse(BaseModel):
    """Response model para health check da API"""
    status: str = Field(..., description="Status geral da API (ok, degraded, error)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp do health check")
    version: str = Field(default="1.5", description="Versão da API")
    services: dict = Field(default_factory=dict, description="Status de cada serviço")
    uptime_seconds: Optional[float] = Field(None, description="Tempo de uptime em segundos")
    message: Optional[str] = Field(None, description="Mensagem adicional sobre o status")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "timestamp": "2026-01-01T20:00:00.000000",
                "version": "1.5",
                "services": {
                    "api": "healthy",
                    "selenium": "healthy",
                    "docker": "healthy"
                },
                "uptime_seconds": 3600.5,
                "message": "API está funcionando corretamente com todos os serviços online"
            }
        }


class JobStartResponse(BaseModel):
    """Response ao iniciar um job de scraping"""
    job_id: str = Field(..., description="ID único do job")
    status: str = Field(..., description="Status inicial: pending")
    message: str = Field(..., description="Mensagem de sucesso")
    created_at: datetime = Field(..., description="Timestamp de criação do job")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "pending",
                "message": "Job enfileirado com sucesso",
                "created_at": "2026-01-01T20:00:00.000000"
            }
        }


class JobStatusResponse(BaseModel):
    """Response com status de um job em progresso"""
    job_id: str = Field(..., description="ID do job")
    status: str = Field(..., description="Status: pending, processing, completed, failed")
    progress: int = Field(..., description="Progresso em % (0-100)")
    message: str = Field(..., description="Mensagem descritiva do status")
    started_at: Optional[datetime] = Field(None, description="Timestamp de início")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "progress": 45,
                "message": "Extraindo dados de canais... 45/50 concluído",
                "started_at": "2026-01-01T20:01:00.000000"
            }
        }


class JobResultResponse(BaseModel):
    """Response com resultado completo de um job"""
    job_id: str = Field(..., description="ID do job")
    status: str = Field(..., description="Status final: completed")
    result: Optional[dict] = Field(None, description="Resultado do scraping (ChannelsListResponse)")
    execution_time_seconds: Optional[float] = Field(None, description="Tempo total de execução")
    completed_at: Optional[datetime] = Field(None, description="Timestamp de conclusão")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "result": {
                    "success": True,
                    "channels": [],
                    "total_channels": 50,
                    "timestamp": "2026-01-01T20:15:30.000000",
                    "error": None
                },
                "execution_time_seconds": 330.5,
                "completed_at": "2026-01-01T20:15:30.000000"
            }
        }


class JobErrorResponse(BaseModel):
    """Response quando um job falha"""
    job_id: str = Field(..., description="ID do job")
    status: str = Field(..., description="Status final: failed")
    error: str = Field(..., description="Mensagem de erro")
    failed_at: Optional[datetime] = Field(None, description="Timestamp da falha")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "failed",
                "error": "Erro ao fazer scraping: timeout na página",
                "failed_at": "2026-01-01T20:10:00.000000"
            }
        }


class ScrapeChannelsRequest(BaseModel):
    """Request model para iniciar scraping de canais com parâmetros dinâmicos"""
    # URLs (opcional, usa .env como fallback)
    login_url: Optional[str] = Field(None, description="URL de login (fallback: .env)")
    scrape_url: Optional[str] = Field(None, description="URL da página para scraping (fallback: .env)")

    # Credenciais (opcional, usa .env como fallback)
    username: Optional[str] = Field(None, description="Usuário/Email (fallback: .env)")
    password: Optional[str] = Field(None, description="Senha (fallback: .env)")

    # Webhook callback (opcional)
    webhook_url: Optional[str] = Field(None, description="URL para webhook callback quando job terminar")

    # Opções de scraping
    wait_time: int = Field(default=15, ge=5, le=600, description="Tempo de espera em segundos (máximo 10 minutos)")
    extract_selector: str = Field(default="h1", description="Seletor CSS para extrair (default: h1)")

    class Config:
        json_schema_extra = {
            "example": {
                "login_url": "https://app.tubehunt.io/login",
                "scrape_url": "https://app.tubehunt.io/long",
                "username": "usuario@email.com",
                "password": "senha123",
                "webhook_url": "https://n8n.example.com/webhook/abc123",
                "wait_time": 15,
                "extract_selector": "h1"
            }
        }


class WebhookPayload(BaseModel):
    """Payload enviado para webhook quando job termina"""
    job_id: str = Field(..., description="ID do job")
    status: str = Field(..., description="Status final: 'completed' ou 'failed'")
    result: Optional[dict] = Field(None, description="Resultado do scraping (ChannelsListResponse)")
    execution_time_seconds: Optional[float] = Field(None, description="Tempo total de execução")
    error: Optional[str] = Field(None, description="Mensagem de erro se falhou")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp do webhook")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "result": {
                    "success": True,
                    "channels": [],
                    "total_channels": 50,
                    "timestamp": "2026-01-01T20:15:30.000000",
                    "error": None
                },
                "execution_time_seconds": 330.5,
                "error": None,
                "timestamp": "2026-01-01T20:15:31.000000"
            }
        }
