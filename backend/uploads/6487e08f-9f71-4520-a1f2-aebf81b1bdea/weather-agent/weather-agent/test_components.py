"""测试各个组件"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("测试天气 API 客户端...")
print("=" * 60)
from src.api.weather_client import WeatherClient

try:
    client = WeatherClient()
    data = client.get_weather_and_forecast("北京")
    print(f"✓ 成功获取 {data['city']} 的天气")
    print(f"  当前温度: {data['current']['temperature']}°C")
    print(f"  天气: {data['current']['weather']}")
    print(f"  预报天数: {len(data['forecast'])}")
except Exception as e:
    print(f"✗ 天气 API 测试失败: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("测试数据库...")
print("=" * 60)
from src.data.database import Database

try:
    db = Database()
    fb_id = db.add_feedback("北京", 15.0, "多云", "建议穿薄外套", "穿多了")
    print(f"✓ 成功添加反馈，ID: {fb_id}")
    recent = db.get_recent_feedback(5)
    print(f"✓ 成功获取 {len(recent)} 条反馈记录")
except Exception as e:
    print(f"✗ 数据库测试失败: {e}")

print("\n" + "=" * 60)
print("测试天气工具...")
print("=" * 60)
from src.agent.tools.weather_tool import weather_tool

try:
    result = weather_tool("上海")
    print("✓ weather_tool 调用成功")
except Exception as e:
    print(f"✗ weather_tool 测试失败: {e}")

print("\n" + "=" * 60)
print("测试图表工具...")
print("=" * 60)
from src.agent.tools.chart_tool import chart_tool

try:
    result = chart_tool(result)
    print("✓ chart_tool 调用成功")
    import json
    data = json.loads(result)
    if "error" in data:
        print(f"  错误: {data['error']}")
    else:
        print(f"  图表已保存到: {data['chart_path']}")
except Exception as e:
    print(f"✗ chart_tool 测试失败: {e}")

print("\n" + "=" * 60)
print("测试反馈工具...")
print("=" * 60)
from src.agent.tools.feedback_tool import feedback_tool

try:
    result = feedback_tool("深圳", 25.0, "晴", "建议穿短袖", "刚好")
    print("✓ feedback_tool 调用成功")
except Exception as e:
    print(f"✗ feedback_tool 测试失败: {e}")

print("\n" + "=" * 60)
print("所有组件测试完成！")
print("=" * 60)
