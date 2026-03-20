from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    PARSING_CODE = "parsing_code"
    ANALYZING_EXPERIMENT = "analyzing_experiment"
    GENERATING_PAPER = "generating_paper"
    COMPLETED = "completed"
    FAILED = "failed"

class InputType(str, Enum):
    GIT_URL = "git_url"
    ZIP_UPLOAD = "zip_upload"

class TaskCreateRequest(BaseModel):
    input_type: InputType
    input_source: Optional[str] = None

class TaskResponse(BaseModel):
    id: str
    status: TaskStatus
    progress: int
    created_at: datetime
    updated_at: datetime
    paper_content: Optional[str] = None
    error_message: Optional[str] = None

class MessageResponse(BaseModel):
    message: str
