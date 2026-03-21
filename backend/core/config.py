from typing import Optional
import os
from pathlib import Path
from dotenv import load_dotenv

# Find .env file - look in project root
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
env_file = project_root / ".env"

if not env_file.exists():
    env_file = backend_dir / ".env"

# Load .env file explicitly
if env_file.exists():
    load_dotenv(dotenv_path=env_file, override=True)

class Settings:
    # Server
    server_host: str = os.getenv("SERVER_HOST", "localhost")
    server_port: int = int(os.getenv("SERVER_PORT", "7348"))
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"
    cors_allow_origins: Optional[str] = os.getenv("CORS_ALLOW_ORIGINS")
    log_level: Optional[str] = os.getenv("LOG_LEVEL")

    # Database
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "3306"))
    db_user: str = os.getenv("DB_USER", "root")
    db_password: str = os.getenv("DB_PASSWORD", "")
    db_name: str = os.getenv("DB_NAME", "code_to_paper")
    db_type: str = os.getenv("DB_TYPE", "sqlite")  # "mysql" or "sqlite"

    # Redis
    redis_host: str = os.getenv("REDIS_HOST", "127.0.0.1")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: str = os.getenv("REDIS_PASSWORD", "")
    redis_db: int = int(os.getenv("REDIS_DB", "0"))

    # LLM - 豆包
    ark_api_key: str = os.getenv("ARK_API_KEY", "")
    ark_base_url: str = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    doubao_model: str = os.getenv("DOUBA_MODEL", "")

    # LLM - 通义千问（可选）
    dashscope_api_key: Optional[str] = os.getenv("DASHSCOPE_API_KEY")
    dashscope_model: Optional[str] = os.getenv("DASHSCOPE_MODEL")

    # File storage
    upload_dir: str = os.getenv("UPLOAD_DIR", "./uploads")
    output_dir: str = os.getenv("OUTPUT_DIR", "./outputs")

    @property
    def database_url(self) -> str:
        if self.db_type == "sqlite":
            return "sqlite:///./code_to_paper.db"
        # MySQL connection
        return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

settings = Settings()

# Create directories
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.output_dir, exist_ok=True)

