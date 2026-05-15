from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # STS
    sts_url: str = Field(..., alias="STS_URL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
