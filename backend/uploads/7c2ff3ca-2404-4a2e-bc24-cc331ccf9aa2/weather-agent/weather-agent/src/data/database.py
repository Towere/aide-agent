import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.utils.config import Config


class Database:
    """SQLite 数据库管理"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or Config.DB_PATH
        self._ensure_db_dir()
        self._init_db()

    def _ensure_db_dir(self):
        """确保数据库目录存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """初始化数据库表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 反馈表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city TEXT NOT NULL,
                    temperature REAL NOT NULL,
                    weather TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    feedback TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 对话历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()

    # 反馈相关操作

    def add_feedback(self, city: str, temperature: float, weather: str,
                     recommendation: str, feedback: str) -> int:
        """添加用户反馈"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO feedback (city, temperature, weather, recommendation, feedback)
                VALUES (?, ?, ?, ?, ?)
            ''', (city, temperature, weather, recommendation, feedback))
            conn.commit()
            return cursor.lastrowid

    def get_recent_feedback(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的反馈记录"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT city, temperature, weather, recommendation, feedback, timestamp
                FROM feedback
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_feedback_by_temp_range(self, temp_min: float, temp_max: float) -> List[Dict[str, Any]]:
        """获取指定温度范围内的反馈"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT city, temperature, weather, recommendation, feedback, timestamp
                FROM feedback
                WHERE temperature BETWEEN ? AND ?
                ORDER BY timestamp DESC
            ''', (temp_min, temp_max))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def format_feedback_for_prompt(self) -> str:
        """将反馈历史格式化为 prompt 可用的字符串"""
        feedbacks = self.get_recent_feedback(10)
        if not feedbacks:
            return "暂无用户反馈记录。"

        lines = ["最近的用户反馈记录："]
        for fb in feedbacks:
            lines.append(
                f"- 温度: {fb['temperature']}°C, 天气: {fb['weather']}, "
                f"推荐: {fb['recommendation'][:50]}..., "
                f"反馈: {fb['feedback']}"
            )
        return "\n".join(lines)

    # 对话历史相关操作

    def add_chat_message(self, session_id: str, role: str, content: str) -> int:
        """添加聊天消息"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO chat_history (session_id, role, content)
                VALUES (?, ?, ?)
            ''', (session_id, role, content))
            conn.commit()
            return cursor.lastrowid

    def get_chat_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取会话的聊天历史"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT role, content, timestamp
                FROM chat_history
                WHERE session_id = ?
                ORDER BY timestamp ASC
                LIMIT ?
            ''', (session_id, limit))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def clear_chat_history(self, session_id: str):
        """清除会话的聊天历史"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM chat_history WHERE session_id = ?', (session_id,))
            conn.commit()
