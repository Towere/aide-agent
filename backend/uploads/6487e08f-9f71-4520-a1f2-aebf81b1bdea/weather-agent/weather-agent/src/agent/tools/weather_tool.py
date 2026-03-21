"""天气查询工具"""
import json
import sys
import os

# 添加上级目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

try:
    from src.api.weather_client import WeatherClient
except ImportError:
    # 备用导入方式
    api_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../api'))
    sys.path.insert(0, api_path)
    from weather_client import WeatherClient


def weather_tool(city: str) -> str:
    """
    查询指定城市的天气信息。

    参数:
        city: 城市名称（中文或英文）

    返回:
        包含当前天气和5天预报的JSON字符串
    """
    try:
        client = WeatherClient()
        data = client.get_weather_and_forecast(city)
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
