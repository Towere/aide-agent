"""天气趋势图绘制工具"""
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import os
import sys

# 添加上级目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

try:
    from src.utils.config import Config
except ImportError:
    # 备用导入方式
    utils_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../utils'))
    sys.path.insert(0, utils_path)
    from config import Config


def chart_tool(weather_data_json: str) -> str:
    """
    根据天气数据绘制未来5天的天气趋势图。

    参数:
        weather_data_json: 天气数据的JSON字符串，格式同 weather_tool 返回的格式

    返回:
        包含图表路径的JSON字符串
    """
    try:
        data = json.loads(weather_data_json)
        forecast = data.get("forecast", [])
        city = data.get("city", "未知城市")

        if not forecast:
            return json.dumps({"error": "没有预报数据"}, ensure_ascii=False)

        # 提取数据
        dates = [f["date"] for f in forecast]
        temp_max = [f["temp_max"] for f in forecast]
        temp_min = [f["temp_min"] for f in forecast]
        temp_avg = [f["temp_avg"] for f in forecast]
        humidity = [f["humidity_avg"] for f in forecast]

        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [2, 1]})

        # 温度图
        ax1.plot(dates, temp_max, 'r-o', label='最高温', linewidth=2, markersize=6)
        ax1.plot(dates, temp_avg, color='orange', marker='s', linestyle='-', label='平均温', linewidth=2, markersize=6)
        ax1.plot(dates, temp_min, 'b-o', label='最低温', linewidth=2, markersize=6)
        ax1.fill_between(dates, temp_min, temp_max, alpha=0.2, color='gray')
        ax1.set_title(f'{city} 未来5天天气趋势', fontsize=14, fontweight='bold')
        ax1.set_ylabel('温度 (°C)', fontsize=12)
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        ax1.set_xticks(range(len(dates)))
        ax1.set_xticklabels(dates, rotation=0)

        # 湿度图
        ax2.bar(dates, humidity, color='skyblue', alpha=0.7, label='平均湿度')
        ax2.set_xlabel('日期', fontsize=12)
        ax2.set_ylabel('湿度 (%)', fontsize=12)
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.set_xticks(range(len(dates)))
        ax2.set_xticklabels(dates, rotation=0)

        # 保存图表
        chart_dir = getattr(Config, 'CHART_DIR', 'data')
        os.makedirs(chart_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chart_path = os.path.join(chart_dir, f"weather_chart_{timestamp}.png")
        plt.tight_layout()
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()

        return json.dumps({
            "success": True,
            "chart_path": chart_path,
            "city": city,
            "forecast_days": len(forecast)
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
