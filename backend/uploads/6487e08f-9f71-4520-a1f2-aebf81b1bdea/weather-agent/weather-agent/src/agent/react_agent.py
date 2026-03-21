"""ReAct Agent 核心实现"""
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from openai import OpenAI
import sys
import os

# 添加上级目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入模块 - 使用 try-except 处理不同导入情况
try:
    from src.utils.config import Config
    from src.agent.prompts import get_system_prompt, TOOLS
    from src.agent.tools.weather_tool import weather_tool
    from src.agent.tools.chart_tool import chart_tool
    from src.agent.tools.feedback_tool import feedback_tool
    from src.data.database import Database
except ImportError:
    # 备用导入方式
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../utils')))
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../data')))
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), './tools')))
    from config import Config
    from prompts import get_system_prompt, TOOLS
    from weather_tool import weather_tool
    from chart_tool import chart_tool
    from feedback_tool import feedback_tool
    from database import Database


class ReactAgent:
    """ReAct 模式的天气穿搭助手 Agent"""

    def __init__(self):
        self.client = OpenAI(
            api_key=Config.ARK_API_KEY,
            base_url=Config.ARK_BASE_URL
        )
        self.model = Config.ARK_MODEL
        self.db = Database()
        self.max_iterations = 10

        # 工具映射
        self.tool_map = {
            "weather_tool": weather_tool,
            "chart_tool": chart_tool,
            "feedback_tool": feedback_tool
        }

        # 状态存储
        self.current_weather_data: Optional[Dict[str, Any]] = None
        self.current_chart_path: Optional[str] = None
        self.last_recommendation: Optional[str] = None
        self.last_city: Optional[str] = None
        self.last_temperature: Optional[float] = None
        self.last_weather: Optional[str] = None

    def _get_feedback_context(self) -> str:
        """获取反馈历史上下文"""
        return self.db.format_feedback_for_prompt()

    def _parse_function_call(self, content: str) -> Optional[List[Dict[str, Any]]]:
        """解析函数调用"""
        # 尝试解析 <|FunctionCallBegin|>...<|FunctionCallEnd|> 格式
        pattern = r'<\|FunctionCallBegin\|>(.*?)<\|FunctionCallEnd\|>'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # 尝试解析直接的 JSON 数组
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError:
            pass

        return None

    def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> str:
        """执行工具"""
        if tool_name not in self.tool_map:
            return json.dumps({"error": f"未知工具: {tool_name}"}, ensure_ascii=False)

        try:
            result = self.tool_map[tool_name](**parameters)

            # 保存状态
            if tool_name == "weather_tool":
                try:
                    data = json.loads(result)
                    if "error" not in data:
                        self.current_weather_data = data
                        self.last_city = data.get("city")
                        self.last_temperature = data.get("current", {}).get("temperature")
                        self.last_weather = data.get("current", {}).get("weather")
                except:
                    pass
            elif tool_name == "chart_tool":
                try:
                    data = json.loads(result)
                    if "error" not in data:
                        self.current_chart_path = data.get("chart_path")
                except:
                    pass

            return result
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def chat(self, user_input: str, session_id: str = "default") -> Tuple[str, Optional[str]]:
        """
        与 Agent 对话

        返回:
            (回复内容, 图表路径)
        """
        # 检查是否是反馈
        feedback_match = self._check_feedback(user_input)
        if feedback_match and self.last_recommendation:
            self._save_feedback(feedback_match)
            return "感谢您的反馈！我会根据您的反馈调整后续的穿搭建议。", None

        # 保存用户消息
        self.db.add_chat_message(session_id, "user", user_input)

        # 获取历史消息
        history = self.db.get_chat_history(session_id, limit=10)
        messages = self._build_messages(history, user_input)

        # ReAct 循环
        iteration = 0
        final_answer = None

        while iteration < self.max_iterations:
            iteration += 1

            # 调用 LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=2000
            )

            choice = response.choices[0]
            message = choice.message

            # 检查是否有工具调用
            if message.tool_calls:
                # 添加 assistant 消息
                messages.append({
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in message.tool_calls
                    ]
                })

                # 执行工具调用
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        parameters = json.loads(tool_call.function.arguments)
                    except:
                        parameters = {}

                    observation = self._execute_tool(tool_name, parameters)

                    # 添加工具响应
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": observation
                    })
            else:
                # 没有工具调用，这是最终答案
                final_answer = message.content or ""
                break

        if final_answer is None:
            final_answer = "抱歉，我无法完成你的请求，请稍后再试。"

        # 保存最后推荐
        self.last_recommendation = final_answer

        # 保存助手回复
        self.db.add_chat_message(session_id, "assistant", final_answer)

        return final_answer, self.current_chart_path

    def _build_messages(self, history: List[Dict[str, Any]], user_input: str) -> List[Dict[str, Any]]:
        """构建消息列表"""
        messages = [
            {
                "role": "system",
                "content": get_system_prompt(self._get_feedback_context())
            }
        ]

        # 添加历史消息
        for msg in history:
            if msg["role"] != "system":
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        return messages

    def _check_feedback(self, user_input: str) -> Optional[str]:
        """检查用户输入是否是反馈"""
        feedback_keywords = {
            "穿多了": ["穿多了", "太多了", "热了", "太热了"],
            "穿少了": ["穿少了", "太少了", "冷了", "太冷了"],
            "刚好": ["刚好", "正好", "合适", "不错"]
        }

        for feedback_type, keywords in feedback_keywords.items():
            for keyword in keywords:
                if keyword in user_input:
                    return feedback_type

        return None

    def _save_feedback(self, feedback: str):
        """保存反馈"""
        if self.last_city and self.last_temperature is not None and self.last_weather:
            self._execute_tool("feedback_tool", {
                "city": self.last_city,
                "temperature": self.last_temperature,
                "weather": self.last_weather,
                "recommendation": self.last_recommendation or "",
                "feedback": feedback
            })

    def clear_session(self, session_id: str = "default"):
        """清除会话历史"""
        self.db.clear_chat_history(session_id)
        self.current_weather_data = None
        self.current_chart_path = None
        self.last_recommendation = None
        self.last_city = None
        self.last_temperature = None
        self.last_weather = None
