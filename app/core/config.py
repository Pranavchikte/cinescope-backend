from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # TMDB
    TMDB_API_KEY: str
    TMDB_BASE_URL: str = "https://api.themoviedb.org/3"
    
    # Indian content configuration
    INDIAN_LANGUAGES: List[str] = ["hi", "mr", "ta", "te", "pa", "ml", "kn", "bn", "gu"]
    INDIAN_OTT_PROVIDERS: List[int] = [122, 8, 119, 232, 237]  # Hotstar, Netflix IN, Prime IN, Zee5, SonyLIV
    INDIAN_REGION: str = "IN"
    
    # CORS
    ALLOWED_ORIGINS: str
    
    RESEND_API_KEY: str
    EMAIL_FROM: str = "onboarding@resend.dev"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()