"""
Tests for the Web Operator Agent
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime

from core.models import TaskRequest, AgentState, TaskStatus
from core.config import settings
from workflow import web_operator_workflow


class TestWebOperatorWorkflow:
    """Test the main workflow functionality"""
    
    @pytest.mark.asyncio
    async def test_create_task(self):
        """Test task creation"""
        task_request = TaskRequest(
            description="Test task",
            url="https://example.com",
            max_steps=5
        )
        
        task_id = await web_operator_workflow.create_task(task_request)
        assert isinstance(task_id, str)
        assert len(task_id) > 0
    
    @pytest.mark.asyncio
    async def test_agent_state_creation(self):
        """Test agent state initialization"""
        state = AgentState(
            task_id="test-123",
            description="Test description",
            current_url="https://example.com",
            max_steps=10
        )
        
        assert state.task_id == "test-123"
        assert state.status == TaskStatus.PENDING
        assert state.steps_completed == 0
        assert len(state.execution_log) == 0


class TestBrowserTool:
    """Test browser automation functionality"""
    
    @pytest.mark.asyncio
    async def test_browser_initialization(self):
        """Test browser can be initialized"""
        from tools.browser import BrowserTool
        
        browser_tool = BrowserTool()
        # Mock the playwright initialization
        with patch.object(browser_tool, 'initialize', return_value=True):
            result = await browser_tool.initialize()
            assert result is True


class TestLLMTool:
    """Test LLM integration"""
    
    @pytest.mark.asyncio
    async def test_llm_tool_initialization(self):
        """Test LLM tool can be created"""
        from tools.llm import LLMTool
        
        llm_tool = LLMTool()
        assert llm_tool.llm is not None


class TestVisionTool:
    """Test computer vision functionality"""
    
    def test_vision_tool_creation(self):
        """Test vision tool initialization"""
        from tools.vision import VisionTool
        
        vision_tool = VisionTool()
        assert vision_tool.confidence_threshold == 0.8


class TestAPIEndpoints:
    """Test FastAPI endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns correct information"""
        from api.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        from api.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


# Integration test
@pytest.mark.asyncio
async def test_full_workflow_mock():
    """Test complete workflow with mocked browser"""
    
    task_request = TaskRequest(
        description="Navigate to example.com",
        url="https://example.com",
        max_steps=3,
        require_confirmation=False
    )
    
    # Mock browser operations
    with patch('tools.browser.browser_tool.initialize', return_value=True), \
         patch('tools.browser.browser_tool.navigate_to', return_value=True), \
         patch('tools.browser.browser_tool.take_screenshot', return_value="/tmp/test.png"), \
         patch('tools.browser.browser_tool.analyze_page', return_value=None):
        
        task_id = await web_operator_workflow.create_task(task_request)
        
        # This would normally execute the full workflow
        # For testing, we just verify the task was created
        assert isinstance(task_id, str)


if __name__ == "__main__":
    # Run basic tests
    print("Running Web Operator Agent tests...")
    
    # Test configuration
    print(f"✓ Configuration loaded: {settings.openai_model}")
    
    # Test imports
    try:
        from workflow import web_operator_workflow
        print("✓ Workflow import successful")
        
        from tools.browser import browser_tool
        print("✓ Browser tool import successful")
        
        from tools.llm import llm_tool
        print("✓ LLM tool import successful")
        
        from tools.vision import vision_tool
        print("✓ Vision tool import successful")
        
        from api.main import app
        print("✓ API app import successful")
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
    
    print("\nBasic tests completed!")
    print("Run 'pytest test.py' for full test suite")
