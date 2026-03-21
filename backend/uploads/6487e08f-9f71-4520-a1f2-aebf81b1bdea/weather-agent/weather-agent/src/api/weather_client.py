import requests
from typing import Dict, Any, List
from datetime import datetime, timedelta
import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.utils.config import Config


class WeatherClient:
    """天气客户端 - 支持多个数据源"""

    def __init__(self):
        self.api_key = Config.OWM_API_KEY
        self.base_url = Config.OWM_BASE_URL
        self.use_mock = False

    def _make_request_owm(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """发送 OpenWeatherMap API 请求"""
        params["appid"] = self.api_key
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    def _get_weather_wttr(self, city: str) -> Dict[str, Any]:
        """从 wttr.in 获取天气数据（免费，无需 API key）"""
        try:
            # 尝试使用 wttr.in
            url = f"https://wttr.in/{requests.utils.quote(city)}?format=j1"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except:
            return None

    def _convert_wttr_current(self, data: Dict[str, Any], city: str) -> Dict[str, Any]:
        """转换 wttr.in 当前天气格式"""
        current = data["current_condition"][0]
        astronomy = data["weather"][0]["astronomy"][0]

        return {
            "city": city,
            "country": data.get("nearest_area", [{}])[0].get("country", [{}])[0].get("value", ""),
            "temperature": float(current["temp_C"]),
            "feels_like": float(current["FeelsLikeC"]),
            "temp_min": float(data["weather"][0]["mintempC"]),
            "temp_max": float(data["weather"][0]["maxtempC"]),
            "humidity": int(current["humidity"]),
            "pressure": int(current["pressure"]),
            "wind_speed": float(current["windspeedKmph"]) / 3.6,  # km/h to m/s
            "wind_deg": int(current.get("winddirDegree", 0)),
            "weather": current["weatherDesc"][0]["value"],
            "weather_description": current["weatherDesc"][0]["value"],
            "weather_icon": "",
            "clouds": int(current.get("cloudcover", 0)),
            "visibility": int(current.get("visibility", 0)) * 1000,  # km to meters
            "timestamp": datetime.now().isoformat(),
            "sunrise": astronomy["sunrise"],
            "sunset": astronomy["sunset"]
        }

    def _convert_wttr_forecast(self, data: Dict[str, Any], days: int) -> List[Dict[str, Any]]:
        """转换 wttr.in 预报格式"""
        forecasts = []
        for i, day in enumerate(data["weather"][:days]):
            date_obj = datetime.now() + timedelta(days=i)
            forecasts.append({
                "date": date_obj.date().isoformat(),
                "temp_avg": (float(day["mintempC"]) + float(day["maxtempC"])) / 2,
                "temp_min": float(day["mintempC"]),
                "temp_max": float(day["maxtempC"]),
                "humidity_avg": int(day.get("hourly", [{}])[0].get("humidity", 50)),
                "wind_speed_avg": float(day.get("hourly", [{}])[0].get("windspeedKmph", 10)) / 3.6,
                "weather": day.get("hourly", [{}])[0].get("weatherDesc", [{}])[0].get("value", "Clear")
            })
        return forecasts

    def _get_mock_weather(self, city: str) -> Dict[str, Any]:
        """生成模拟天气数据（最后的备选方案）"""
        base_temp = random.uniform(15, 30)
        current = {
            "city": city,
            "country": "CN",
            "temperature": round(base_temp, 1),
            "feels_like": round(base_temp + random.uniform(-2, 2), 1),
            "temp_min": round(base_temp - 3, 1),
            "temp_max": round(base_temp + 5, 1),
            "humidity": random.randint(40, 80),
            "pressure": random.randint(1000, 1030),
            "wind_speed": round(random.uniform(1, 5), 1),
            "wind_deg": random.randint(0, 360),
            "weather": random.choice(["晴", "多云", "阴", "小雨"]),
            "weather_description": random.choice(["晴朗", "多云", "阴天", "小雨"]),
            "weather_icon": "",
            "clouds": random.randint(0, 100),
            "visibility": random.randint(5000, 15000),
            "timestamp": datetime.now().isoformat(),
            "sunrise": "06:30",
            "sunset": "18:30"
        }

        forecast = []
        for i in range(5):
            day_temp = base_temp + random.uniform(-3, 3)
            forecast.append({
                "date": (datetime.now() + timedelta(days=i)).date().isoformat(),
                "temp_avg": round(day_temp, 1),
                "temp_min": round(day_temp - 4, 1),
                "temp_max": round(day_temp + 4, 1),
                "humidity_avg": random.randint(45, 75),
                "wind_speed_avg": round(random.uniform(2, 6), 1),
                "weather": random.choice(["晴", "多云", "阴", "小雨"])
            })

        return {"current": current, "forecast": forecast}

    def get_current_weather(self, city: str) -> Dict[str, Any]:
        """获取当前天气（尝试多个数据源）"""
        # 首先尝试 OpenWeatherMap
        if self.api_key and not self.use_mock:
            try:
                params = {
                    "q": city,
                    "units": "metric",
                    "lang": "zh_cn"
                }
                data = self._make_request_owm("weather", params)
                return self._format_current_weather(data)
            except Exception as e:
                print(f"OpenWeatherMap failed: {e}, trying wttr.in...")

        # 然后尝试 wttr.in
        wttr_data = self._get_weather_wttr(city)
        if wttr_data:
            try:
                return self._convert_wttr_current(wttr_data, city)
            except Exception as e:
                print(f"wttr.in parsing failed: {e}, using mock data...")

        # 最后使用模拟数据
        mock_data = self._get_mock_weather(city)
        return mock_data["current"]

    def get_forecast(self, city: str, days: int = 5) -> List[Dict[str, Any]]:
        """获取 5 天预报（尝试多个数据源）"""
        # 首先尝试 OpenWeatherMap
        if self.api_key and not self.use_mock:
            try:
                params = {
                    "q": city,
                    "units": "metric",
                    "lang": "zh_cn"
                }
                data = self._make_request_owm("forecast", params)
                return self._format_forecast(data, days)
            except Exception as e:
                print(f"OpenWeatherMap forecast failed: {e}, trying wttr.in...")

        # 然后尝试 wttr.in
        wttr_data = self._get_weather_wttr(city)
        if wttr_data:
            try:
                return self._convert_wttr_forecast(wttr_data, days)
            except Exception as e:
                print(f"wttr.in forecast parsing failed: {e}, using mock data...")

        # 最后使用模拟数据
        mock_data = self._get_mock_weather(city)
        return mock_data["forecast"]

    def get_weather_and_forecast(self, city: str) -> Dict[str, Any]:
        """获取当前天气和预报"""
        current = self.get_current_weather(city)
        forecast = self.get_forecast(city)
        return {
            "current": current,
            "forecast": forecast,
            "city": city
        }

    def _format_current_weather(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化当前天气数据（OpenWeatherMap 格式）"""
        return {
            "city": data["name"],
            "country": data["sys"]["country"],
            "temperature": round(data["main"]["temp"], 1),
            "feels_like": round(data["main"]["feels_like"], 1),
            "temp_min": round(data["main"]["temp_min"], 1),
            "temp_max": round(data["main"]["temp_max"], 1),
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "wind_speed": round(data["wind"]["speed"], 1),
            "wind_deg": data["wind"].get("deg", 0),
            "weather": data["weather"][0]["main"],
            "weather_description": data["weather"][0]["description"],
            "weather_icon": data["weather"][0]["icon"],
            "clouds": data["clouds"]["all"],
            "visibility": data.get("visibility", 0),
            "timestamp": datetime.fromtimestamp(data["dt"]).isoformat(),
            "sunrise": datetime.fromtimestamp(data["sys"]["sunrise"]).isoformat(),
            "sunset": datetime.fromtimestamp(data["sys"]["sunset"]).isoformat()
        }

    def _format_forecast(self, data: Dict[str, Any], days: int) -> List[Dict[str, Any]]:
        """格式化预报数据，按天聚合（OpenWeatherMap 格式）"""
        forecasts = []
        daily_data = {}

        for item in data["list"]:
            dt = datetime.fromtimestamp(item["dt"])
            date_str = dt.date().isoformat()

            if date_str not in daily_data:
                daily_data[date_str] = {
                    "date": date_str,
                    "temps": [],
                    "humidity": [],
                    "wind_speed": [],
                    "weather": [],
                    "samples": 0
                }

            daily_data[date_str]["temps"].append(item["main"]["temp"])
            daily_data[date_str]["humidity"].append(item["main"]["humidity"])
            daily_data[date_str]["wind_speed"].append(item["wind"]["speed"])
            daily_data[date_str]["weather"].append(item["weather"][0]["main"])
            daily_data[date_str]["samples"] += 1

        # 取前 N 天
        sorted_dates = sorted(daily_data.keys())[:days]

        for date_str in sorted_dates:
            d = daily_data[date_str]
            # 取出现频率最高的天气
            from collections import Counter
            weather_counts = Counter(d["weather"])
            most_common_weather = weather_counts.most_common(1)[0][0]

            forecasts.append({
                "date": date_str,
                "temp_avg": round(sum(d["temps"]) / len(d["temps"]), 1),
                "temp_min": round(min(d["temps"]), 1),
                "temp_max": round(max(d["temps"]), 1),
                "humidity_avg": round(sum(d["humidity"]) / len(d["humidity"])),
                "wind_speed_avg": round(sum(d["wind_speed"]) / len(d["wind_speed"]), 1),
                "weather": most_common_weather
            })

        return forecasts
