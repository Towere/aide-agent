from sqlalchemy import Column, String, Text, Integer, DateTime, Enum as SQLEnum, TypeDecorator
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.dialects import sqlite, mysql
from datetime import datetime
import enum
import uuid
import json
from core.database import Base


class JSONType(TypeDecorator):
    """
    兼容SQLite和MySQL的JSON类型
    SQLite使用Text存储JSON字符串
    MySQL使用原生JSON类型
    """
    impl = Text

    def load_dialect_impl(self, dialect):
        if dialect.name == 'mysql':
            return dialect.type_descriptor(mysql.JSON())
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'mysql':
            return value
        return json.dumps(value, ensure_ascii=False)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'mysql':
            return value
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    PARSING_CODE = "parsing_code"
    ANALYZING_EXPERIMENT = "analyzing_experiment"
    GENERATING_PAPER = "generating_paper"
    COMPLETED = "completed"
    FAILED = "failed"

class InputType(str, enum.Enum):
    GIT_URL = "git_url"
    ZIP_UPLOAD = "zip_upload"


class PaperLanguage(str, enum.Enum):
    """论文语言"""
    ENGLISH = "en"  # 纯英文
    CHINESE = "zh"  # 纯中文
    BILINGUAL = "bilingual"  # 双语（中英文对照）

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, index=True)
    input_type = Column(SQLEnum(InputType), nullable=False)
    input_source = Column(String(500), nullable=False)
    repo_path = Column(String(500), nullable=True)
    language = Column(SQLEnum(PaperLanguage), default=PaperLanguage.ENGLISH, nullable=False)

    progress = Column(Integer, default=0)

    code_analysis = Column(JSONType, nullable=True)
    experiment_analysis = Column(JSONType, nullable=True)
    paper_content = Column(Text, nullable=True)
    template_config = Column(JSONType, nullable=True)

    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "status": self.status.value if self.status else None,
            "input_type": self.input_type.value if self.input_type else None,
            "input_source": self.input_source,
            "progress": self.progress,
            "paper_content": self.paper_content,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
