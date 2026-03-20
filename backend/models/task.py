from sqlalchemy import Column, String, Text, Integer, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.dialects.mysql import CHAR
from datetime import datetime
import enum
import uuid
from core.database import Base

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

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING, index=True)
    input_type = Column(SQLEnum(InputType), nullable=False)
    input_source = Column(String(500), nullable=False)
    repo_path = Column(String(500), nullable=True)

    progress = Column(Integer, default=0)

    code_analysis = Column(JSON, nullable=True)
    experiment_analysis = Column(JSON, nullable=True)
    paper_content = Column(Text, nullable=True)

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
