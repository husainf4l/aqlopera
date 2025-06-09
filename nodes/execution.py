"""
Action execution nodes for different types of web interactions
"""
import asyncio
from core.models import AgentState, TaskStatus, ActionType
from tools.browser import browser_tool
from tools.llm import llm_tool
from core.logging import app_logger


async def safety_check_node(state: AgentState) -> AgentState:
    """
    Perform safety checks before executing sensitive actions
    """
    if not state.pending_actions:
        updated_state = state.copy()
        updated_state.status = TaskStatus.COMPLETED
        updated_state.execution_log = state.execution_log + ["No pending actions - marking as completed"]
        return updated_state
    
    next_action = state.pending_actions[0]
    
    # Define sensitive actions that need confirmation
    sensitive_actions = [
        ActionType.CLICK,  # Clicking buttons might trigger purchases, submissions, etc.
        ActionType.FILL_FORM,  # Form filling might submit personal data
    ]
    
    # Check if the action is on a sensitive domain
    sensitive_domains = [
        "bank", "payment", "checkout", "billing", "financial",
        "paypal", "stripe", "amazon", "shop", "store"
    ]
    
    current_url = state.current_url or ""
    is_sensitive_domain = any(domain in current_url.lower() for domain in sensitive_domains)
    
    # Check if action needs confirmation
    needs_confirmation = (
        next_action.action_type in sensitive_actions or
        is_sensitive_domain or
        "submit" in (next_action.target or "").lower() or
        "buy" in (next_action.target or "").lower() or
        "purchase" in (next_action.target or "").lower()
    )
    
    if needs_confirmation and not state.requires_confirmation:
        app_logger.info("Safety check triggered - requiring user confirmation")
        
        confirmation_message = await llm_tool.generate_user_confirmation_message(
            next_action, state.page_analysis
        )
        
        updated_state = state.copy()
        updated_state.status = TaskStatus.WAITING_USER_INPUT
        updated_state.requires_confirmation = True
        updated_state.confirmation_message = confirmation_message
        updated_state.execution_log = state.execution_log + ["Safety check: User confirmation required"]
        
        return updated_state
    
    # Safety check passed
    updated_state = state.copy()
    updated_state.execution_log = state.execution_log + ["Safety check passed"]
    
    return updated_state


async def execute_action_node(state: AgentState) -> AgentState:
    """
    Execute the next pending action
    """
    if not state.pending_actions:
        app_logger.warning("No pending actions to execute")
        updated_state = state.copy()
        updated_state.status = TaskStatus.COMPLETED
        return updated_state
    
    next_action = state.pending_actions[0]
    app_logger.info(f"Executing action: {next_action.action_type.value}")
    
    try:
        # Execute the action using browser tool
        if next_action.action_type == ActionType.NAVIGATE:
            success = await browser_tool.navigate_to(next_action.target)
            result = {"success": success, "current_url": next_action.target if success else None}
        elif next_action.action_type == ActionType.CLICK:
            success = await browser_tool.click_element(selector=next_action.target)
            result = {"success": success, "message": f"Clicked {next_action.target}" if success else "Click failed"}
        elif next_action.action_type == ActionType.TYPE:
            success = await browser_tool.type_text(next_action.target, next_action.value)
            result = {"success": success, "message": f"Typed text into {next_action.target}" if success else "Type failed"}
        elif next_action.action_type == ActionType.FILL_FORM:
            # For now, treat as TYPE action since fill_form might not be implemented
            success = await browser_tool.type_text(next_action.target, next_action.value)
            result = {"success": success, "message": f"Filled form field {next_action.target}" if success else "Form fill failed"}
        elif next_action.action_type == ActionType.SCROLL:
            success = await browser_tool.scroll_page(next_action.target or "down")
            result = {"success": success, "message": f"Scrolled {next_action.target or 'down'}" if success else "Scroll failed"}
        elif next_action.action_type == ActionType.WAIT:
            await asyncio.sleep(float(next_action.value or "1"))
            result = {"success": True, "message": f"Waited {next_action.value} seconds"}
        elif next_action.action_type == ActionType.SCREENSHOT:
            screenshot_path = await browser_tool.take_screenshot(state.task_id)
            result = {"success": bool(screenshot_path), "message": f"Screenshot saved: {screenshot_path}" if screenshot_path else "Screenshot failed"}
        else:
            app_logger.error(f"Unknown action type: {next_action.action_type}")
            updated_state = state.copy()
            updated_state.status = TaskStatus.FAILED
            updated_state.error = f"Unknown action type: {next_action.action_type}"
            return updated_state
        
        # Update state
        remaining_actions = state.pending_actions[1:]
        execution_log = state.execution_log + [f"Executed: {next_action.action_type.value}"]
        
        updated_state = state.copy()
        
        if result.get("success"):
            app_logger.info(f"Action executed successfully: {result.get('message', '')}")
            updated_state.pending_actions = remaining_actions
            updated_state.execution_log = execution_log
            updated_state.current_url = result.get("current_url", state.current_url)
            updated_state.completed_actions = state.completed_actions + [next_action]
            updated_state.steps_completed = state.steps_completed + 1
            
            return updated_state
        else:
            app_logger.error(f"Action failed: {result.get('error', 'Unknown error')}")
            updated_state.status = TaskStatus.FAILED
            updated_state.error = result.get("error", "Action execution failed")
            updated_state.execution_log = execution_log + [f"Failed: {result.get('error', 'Unknown error')}"]
            
            return updated_state
    
    except Exception as e:
        app_logger.error(f"Exception during action execution: {str(e)}")
        updated_state = state.copy()
        updated_state.status = TaskStatus.FAILED
        updated_state.error = f"Exception during execution: {str(e)}"
        updated_state.execution_log = state.execution_log + [f"Exception: {str(e)}"]
        
        return updated_state
