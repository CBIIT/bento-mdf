from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, ValidationError
import logging
import re
import os
from pdb import set_trace

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARN)
class Settings(BaseSettings):
    # STS
    sts_url: str = Field(..., alias="STS_URL")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


try:
    settings = Settings()
except ValidationError as e:
    if re.findall("STS_URL", str(e)):
        logger.warn("STS_URL env not set: use .env or explicitly set; setting to 'http://localhost:8000/v2'")
        os.environ['STS_URL'] = 'http://localhost:8000/v2'
        settings = Settings()
    else:
        raise(e)

