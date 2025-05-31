import os
from typing import List

class Settings:
    def __init__(self):
        # Database
        self.DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/linkedin_automation")
        
        # Security
        self.SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
        self.ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
        self.REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
        
        # CORS - Split comma-separated strings into lists
        hosts_str = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0")
        self.ALLOWED_HOSTS = [host.strip() for host in hosts_str.split(",") if host.strip()]
        
        origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173")
        self.CORS_ORIGINS = [origin.strip() for origin in origins_str.split(",") if origin.strip()]
        
        # Redis
        self.REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        # LinkedIn OAuth
        self.LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "")
        self.LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")
        
        # App Settings
        self.DEBUG = os.getenv("DEBUG", "False").lower() == "true"
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "info")

settings = Settings()