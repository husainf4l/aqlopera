"""
Data models and schemas for the Web Operator Agent
"""
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_USER_INPUT = "waiting_user_input"


class ActionType(str, Enum):
    """Types of actions the agent can perform"""
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    SCREENSHOT = "screenshot"
    EXTRACT_TEXT = "extract_text"
    WAIT = "wait"
    CONFIRM = "confirm"
    FILL_FORM = "fill_form"


class TaskRequest(BaseModel):
    """Request model for creating a new task"""
    description: str = Field(..., description="Natural language description of the task")
    url: Optional[str] = Field(None, description="Starting URL (optional)")
    max_steps: int = Field(default=10, description="Maximum number of steps to execute")
    require_confirmation: bool = Field(default=True, description="Whether to ask for user confirmation")
    custom_instructions: Optional[str] = Field(None, description="Additional custom instructions")


class ActionRequest(BaseModel):
    """Model for individual actions"""
    action_type: ActionType
    target: Optional[str] = Field(None, description="CSS selector or element description")
    value: Optional[str] = Field(None, description="Value to input (for type actions)")
    coordinates: Optional[tuple[int, int]] = Field(None, description="X, Y coordinates")
    reason: str = Field(..., description="Reason for this action")


class TaskResponse(BaseModel):
    """Response model for task operations"""
    task_id: str
    status: TaskStatus
    description: str
    current_step: int = 0
    total_steps: int = 0
    current_url: Optional[str] = None
    screenshot_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class TaskUpdate(BaseModel):
    """Model for task updates/progress"""
    task_id: str
    status: TaskStatus
    current_step: int
    action_description: str
    screenshot_path: Optional[str] = None
    requires_user_input: bool = False
    user_input_prompt: Optional[str] = None


class UserConfirmation(BaseModel):
    """Model for user confirmation requests"""
    task_id: str
    action_description: str
    screenshot_path: Optional[str] = None
    confirm: bool


class WebElement(BaseModel):
    """Model representing a web element"""
    tag: str
    text: Optional[str] = None
    attributes: Dict[str, str] = {}
    coordinates: tuple[int, int]
    size: tuple[int, int]
    is_visible: bool = True
    is_clickable: bool = False


class PageAnalysis(BaseModel):
    """Model for page analysis results"""
    url: str
    title: str
    elements: List[WebElement]
    screenshot_path: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class AgentState(BaseModel):
    """State model for the LangGraph agent"""
    task_id: str
    description: str
    current_url: Optional[str] = None
    steps_completed: int = 0
    max_steps: int = 10
    retry_count: int = 0
    max_retries: int = 2
    status: TaskStatus = TaskStatus.PENDING
    browser_context: Optional[Dict[str, Any]] = None
    last_screenshot: Optional[str] = None
    page_analysis: Optional[PageAnalysis] = None
    pending_actions: List[ActionRequest] = []
    completed_actions: List[ActionRequest] = []
    execution_log: List[str] = []
    requires_confirmation: bool = False
    confirmation_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
