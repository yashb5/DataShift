from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "DataShift"
    debug: bool = True
    
    database_url: str = "sqlite+aiosqlite:///./data/datashift.db"
    database_echo: bool = True
    
    encryption_key: str = "datashift-secret-key-16"
    
    server_port: int = 8080
    
    metrics_enabled: bool = True
    
    class Config:
        env_file = ".env"
        env_prefix = "DATASHIFT_"


@lru_cache
def get_settings() -> Settings:
    return Settings()
