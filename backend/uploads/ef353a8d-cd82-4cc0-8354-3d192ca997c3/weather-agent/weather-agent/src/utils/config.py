import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # 火山方舟 API
    ARK_API_KEY = os.getenv("ARK_API_KEY")
    ARK_BASE_URL = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    ARK_MODEL = os.getenv("ARK_MODEL")

    # OpenWeatherMap API
    OWM_API_KEY = os.getenv("OWM_API_KEY")
    OWM_BASE_URL = "https://api.openweathermap.org/data/2.5"

    # 数据库
    DB_PATH = os.getenv("DB_PATH", "data/weather_agent.db")

    # 图表存储
    CHART_DIR = "data"
