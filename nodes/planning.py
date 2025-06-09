"""
Task planning and initialization node
"""
from typing import Dict, Any
from core.models import AgentState, TaskStatus
from tools.llm import llm_tool
from tools.browser import browser_tool
from core.logging import app_logger


async def plan_task_node(state: AgentState) -> AgentState:
    """
    Initial node that analyzes the task and creates an execution plan
    """
    app_logger.info(f"Planning task: {state.description}")
    
    try:
        # Initialize browser if needed
        if not browser_tool.browser:
            await browser_tool.initialize()
        
        # If a starting URL is provided, navigate to it
        if state.current_url:
            success = await browser_tool.navigate_to(state.current_url)
            if not success:
                updated_state = state.copy()
                updated_state.status = TaskStatus.FAILED
                updated_state.error = f"Failed to navigate to {state.current_url}"
                updated_state.execution_log = state.execution_log + [f"Navigation failed: {state.current_url}"]
                return updated_state
        
        # Take initial screenshot
        screenshot_path = await browser_tool.take_screenshot(state.task_id)
        
        # Analyze the current page
        page_analysis = await browser_tool.analyze_page()
        
        if page_analysis:
            # Plan initial actions
            actions = await llm_tool.plan_actions(state.description, page_analysis)
            
            # Return updated state
            updated_state = state.copy()
            updated_state.status = TaskStatus.RUNNING
            updated_state.page_analysis = page_analysis
            updated_state.pending_actions = actions
            updated_state.last_screenshot = screenshot_path
            updated_state.execution_log = state.execution_log + ["Task planning completed", f"Planned {len(actions)} initial actions"]
            
            return updated_state
        else:
            # Return failed state
            updated_state = state.copy()
            updated_state.status = TaskStatus.FAILED
            updated_state.error = "Failed to analyze initial page"
            updated_state.execution_log = state.execution_log + ["Page analysis failed"]
            
            return updated_state
    
    except Exception as e:
        app_logger.error(f"Task planning failed: {e}")
        updated_state = state.copy()
        updated_state.status = TaskStatus.FAILED
        updated_state.error = f"Planning error: {str(e)}"
        updated_state.execution_log = state.execution_log + [f"Planning failed: {str(e)}"]
        
        return updated_state


async def analyze_page_node(state: AgentState) -> AgentState:
    """
    Node that analyzes the current page state
    """
    app_logger.info("Analyzing current page")
    
    try:
        # Take screenshot
        screenshot_path = await browser_tool.take_screenshot(state.task_id)
        
        # Analyze page
        page_analysis = await browser_tool.analyze_page()
        
        if page_analysis:
            # Check if task is complete
            completion_analysis = await llm_tool.analyze_task_completion(
                state.description, 
                page_analysis, 
                state.execution_log
            )
            
            if completion_analysis.get("completed", False):
                updated_state = state.copy()
                updated_state.status = TaskStatus.COMPLETED
                updated_state.page_analysis = page_analysis
                updated_state.last_screenshot = screenshot_path
                updated_state.result = {
                    "success": True,
                    "completion_analysis": completion_analysis,
                    "final_url": page_analysis.url
                }
                updated_state.execution_log = state.execution_log + ["Task completed successfully"]
                
                return updated_state
            else:
                # Plan next actions
                actions = await llm_tool.plan_actions(state.description, page_analysis)
                
                updated_state = state.copy()
                updated_state.page_analysis = page_analysis
                updated_state.pending_actions = actions
                updated_state.last_screenshot = screenshot_path
                updated_state.execution_log = state.execution_log + [f"Page analyzed, planned {len(actions)} next actions"]
                
                return updated_state
        else:
            updated_state = state.copy()
            updated_state.status = TaskStatus.FAILED
            updated_state.error = "Failed to analyze page"
            updated_state.execution_log = state.execution_log + ["Page analysis failed"]
            
            return updated_state
    
    except Exception as e:
        app_logger.error(f"Page analysis failed: {e}")
        updated_state = state.copy()
        updated_state.status = TaskStatus.FAILED
        updated_state.error = f"Analysis error: {str(e)}"
        updated_state.execution_log = state.execution_log + [f"Analysis failed: {str(e)}"]
        
        return updated_state
