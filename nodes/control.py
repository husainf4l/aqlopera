"""
Control flow and decision nodes for the LangGraph workflow
"""
from typing import Dict, Any, Literal
from core.models import AgentState, TaskStatus
from core.logging import app_logger


def should_continue_execution(state: AgentState) -> Literal["continue", "complete", "confirm", "fail"]:
    """
    Decide whether to continue execution, complete, ask for confirmation, or fail
    """
    # Check if task failed
    if state.status == TaskStatus.FAILED:
        return "fail"
    
    # Check if task completed
    if state.status == TaskStatus.COMPLETED:
        return "complete"
    
    # Check if waiting for user input
    if state.status == TaskStatus.WAITING_USER_INPUT or state.requires_confirmation:
        return "confirm"
    
    # Check if max steps reached
    if state.steps_completed >= state.max_steps:
        app_logger.warning(f"Maximum steps ({state.max_steps}) reached")
        return "complete"
    
    # Check if no more actions
    if not state.pending_actions:
        return "complete"
    
    # Continue execution
    return "continue"


def route_next_action(state: AgentState) -> Literal["execute", "analyze", "plan"]:
    """
    Route to the appropriate next action based on current state
    """
    # If we have pending actions, execute them
    if state.pending_actions:
        return "execute"
    
    # If we don't have pending actions, analyze the page
    if not state.page_analysis or state.steps_completed > 0:
        return "analyze"
    
    # If we need to plan initial actions
    return "plan"


async def completion_node(state: AgentState) -> AgentState:
    """
    Handle task completion
    """
    app_logger.info(f"Task completion - Status: {state.status}")
    
    try:
        # Take final screenshot
        from tools.browser import browser_tool
        final_screenshot = await browser_tool.take_screenshot(f"{state.task_id}_final")
        
        # Determine completion status
        if state.status == TaskStatus.COMPLETED:
            result = {
                "success": True,
                "message": "Task completed successfully",
                "final_url": state.current_url,
                "steps_completed": state.steps_completed,
                "final_screenshot": final_screenshot
            }
        elif state.status == TaskStatus.FAILED:
            result = {
                "success": False,
                "message": f"Task failed: {state.error}",
                "final_url": state.current_url,
                "steps_completed": state.steps_completed,
                "final_screenshot": final_screenshot
            }
        else:
            # Max steps reached or other completion reason
            result = {
                "success": True,
                "message": "Task execution completed (max steps reached)",
                "final_url": state.current_url,
                "steps_completed": state.steps_completed,
                "final_screenshot": final_screenshot
            }
        
        updated_state = state.copy()
        updated_state.status = TaskStatus.COMPLETED
        updated_state.result = result
        updated_state.last_screenshot = final_screenshot
        updated_state.execution_log = state.execution_log + ["Task execution completed"]
        
        return updated_state
    
    except Exception as e:
        app_logger.error(f"Completion handling failed: {e}")
        updated_state = state.copy()
        updated_state.status = TaskStatus.FAILED
        updated_state.error = f"Completion error: {str(e)}"
        updated_state.execution_log = state.execution_log + [f"Completion failed: {str(e)}"]
        
        return updated_state


async def confirmation_node(state: AgentState) -> AgentState:
    """
    Handle user confirmation requests
    """
    app_logger.info("Waiting for user confirmation")
    
    # This node just maintains the waiting state
    # The actual confirmation handling is done in the API layer
    updated_state = state.copy()
    updated_state.status = TaskStatus.WAITING_USER_INPUT
    updated_state.execution_log = state.execution_log + ["Awaiting user confirmation"]
    
    return updated_state


async def error_handling_node(state: AgentState) -> AgentState:
    """
    Handle errors and attempt recovery
    """
    app_logger.error(f"Error handling - Error: {state.error}")
    
    try:
        # Take screenshot for debugging
        from tools.browser import browser_tool
        error_screenshot = await browser_tool.take_screenshot(f"{state.task_id}_error")
        
        # Check if we've exceeded retry attempts
        if state.retry_count >= state.max_retries:
            app_logger.error(f"Max retries ({state.max_retries}) exceeded, marking task as failed")
            updated_state = state.copy()
            updated_state.status = TaskStatus.FAILED
            updated_state.last_screenshot = error_screenshot
            updated_state.execution_log = state.execution_log + [
                f"Error occurred: {state.error}",
                f"Max retries ({state.max_retries}) exceeded - task failed"
            ]
            return updated_state
        
        # Try to analyze what went wrong and suggest recovery
        from tools.llm import llm_tool
        
        if state.page_analysis:
            recovery_actions = await llm_tool.plan_actions(
                f"Recover from error: {state.error}. Original task: {state.description}",
                state.page_analysis
            )
            
            if recovery_actions:
                app_logger.info(f"Planned {len(recovery_actions)} recovery actions (retry {state.retry_count + 1}/{state.max_retries})")
                updated_state = state.copy()
                updated_state.status = TaskStatus.RUNNING
                updated_state.pending_actions = recovery_actions
                updated_state.retry_count = state.retry_count + 1
                updated_state.last_screenshot = error_screenshot
                updated_state.execution_log = state.execution_log + [
                    f"Error occurred: {state.error}",
                    f"Attempting recovery with {len(recovery_actions)} actions (retry {state.retry_count + 1}/{state.max_retries})"
                ]
                
                return updated_state
        
        # If recovery planning fails, mark as failed
        updated_state = state.copy()
        updated_state.status = TaskStatus.FAILED
        updated_state.last_screenshot = error_screenshot
        updated_state.execution_log = state.execution_log + [
            f"Error occurred: {state.error}",
            "Recovery planning failed - task marked as failed"
        ]
        
        return updated_state
    
    except Exception as e:
        app_logger.error(f"Error handling failed: {e}")
        updated_state = state.copy()
        updated_state.status = TaskStatus.FAILED
        updated_state.error = f"Error handling failed: {str(e)}"
        updated_state.execution_log = state.execution_log + [f"Error handling failed: {str(e)}"]
        
        return updated_state
