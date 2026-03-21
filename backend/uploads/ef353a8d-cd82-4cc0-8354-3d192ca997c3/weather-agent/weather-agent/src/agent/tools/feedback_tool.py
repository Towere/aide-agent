"""用户反馈存储工具"""
import json
import sys
import os

# 添加上级目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

try:
    from src.data.database import Database
except ImportError:
    # 备用导入方式
    data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data'))
    sys.path.insert(0, data_path)
    from database import Database


def feedback_tool(city: str, temperature: float, weather: str,
                  recommendation: str, feedback: str) -> str:
    """
    存储用户的穿搭反馈。

    参数:
        city: 城市名称
        temperature: 当前温度（摄氏度）
        weather: 天气状况（如：晴、多云、雨等）
        recommendation: 给出的穿搭建议
        feedback: 用户反馈，可选值: "穿多了", "穿少了", "刚好"

    返回:
        操作结果的JSON字符串
    """
    try:
        db = Database()
        feedback_id = db.add_feedback(
            city=city,
            temperature=temperature,
            weather=weather,
            recommendation=recommendation,
            feedback=feedback
        )
        return json.dumps({
            "success": True,
            "feedback_id": feedback_id,
            "message": "反馈已保存，感谢您的反馈！"
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
