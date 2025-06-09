"""
LangGraph workflow definition for the Web Operator Agent
"""
import uuid
from typing import Dict, Any
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from core.models import AgentState, TaskStatus, TaskRequest
from nodes.planning import plan_task_node, analyze_page_node
from nodes.execution import execute_action_node, safety_check_node
from nodes.control import (
    should_continue_execution, 
    route_next_action, 
    completion_node, 
    confirmation_node, 
    error_handling_node
)
from core.logging import app_logger


class WebOperatorWorkflow:
    """
    LangGraph workflow for web automation tasks
    """
    
    def __init__(self):
        self.workflow = None
        self.app = None
        self._build_workflow()
    
    def _build_workflow(self):
        """Build the LangGraph workflow"""
        
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("plan_task", plan_task_node)
        workflow.add_node("analyze_page", analyze_page_node)
        workflow.add_node("safety_check", safety_check_node)
        workflow.add_node("execute_action", execute_action_node)
        workflow.add_node("completion", completion_node)
        workflow.add_node("confirmation", confirmation_node)
        workflow.add_node("error_handling", error_handling_node)
        
        # Set entry point
        workflow.set_entry_point("plan_task")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "plan_task",
            should_continue_execution,
            {
                "continue": "safety_check",
                "complete": "completion",
                "confirm": "confirmation",
                "fail": "error_handling"
            }
        )
        
        workflow.add_conditional_edges(
            "analyze_page",
            should_continue_execution,
            {
                "continue": "safety_check",
                "complete": "completion", 
                "confirm": "confirmation",
                "fail": "error_handling"
            }
        )
        
        workflow.add_conditional_edges(
            "safety_check",
            should_continue_execution,
            {
                "continue": "execute_action",
                "complete": "completion",
                "confirm": "confirmation", 
                "fail": "error_handling"
            }
        )
        
        workflow.add_conditional_edges(
            "execute_action",
            route_next_action,
            {
                "execute": "safety_check",
                "analyze": "analyze_page",
                "plan": "analyze_page"
            }
        )
        
        workflow.add_conditional_edges(
            "error_handling",
            should_continue_execution,
            {
                "continue": "safety_check",
                "complete": "completion",
                "confirm": "confirmation",
                "fail": "completion"
            }
        )
        
        # Terminal nodes
        workflow.add_edge("completion", END)
        workflow.add_edge("confirmation", END)
        
        # Compile the workflow with memory
        self.workflow = workflow
        self.app = workflow.compile(checkpointer=MemorySaver())
        
        app_logger.info("Web Operator workflow built successfully")
    
    async def create_task(self, task_request: TaskRequest) -> str:
        """Create a new task and return task ID"""
        task_id = str(uuid.uuid4())
        
        app_logger.info(f"Creating new task: {task_id}")
        app_logger.info(f"Task description: {task_request.description}")
        
        return task_id
    
    async def execute_task(self, task_id: str, task_request: TaskRequest) -> Dict[str, Any]:
        """Execute a task using the LangGraph workflow"""
        
        # Create initial state
        initial_state = AgentState(
            task_id=task_id,
            description=task_request.description,
            current_url=task_request.url,
            max_steps=task_request.max_steps,
            status=TaskStatus.PENDING,
            steps_completed=0,
            execution_log=[f"Task created: {task_request.description}"],
            requires_confirmation=task_request.require_confirmation
        )
        
        try:
            # Execute the workflow
            config = {"configurable": {"thread_id": task_id}}
            
            final_state = None
            async for state in self.app.astream(initial_state, config=config):
                final_state = state
                app_logger.debug(f"Workflow step completed: {state}")
            
            if final_state:
                # Get the final state from the last node (it's a dictionary)
                final_agent_state = list(final_state.values())[0]
                return {
                    "task_id": task_id,
                    "status": final_agent_state.get("status"),
                    "result": final_agent_state.get("result"),
                    "steps_completed": final_agent_state.get("steps_completed", 0),
                    "execution_log": final_agent_state.get("execution_log", []),
                    "final_screenshot": final_agent_state.get("last_screenshot"),
                    "error": final_agent_state.get("error")
                }
            else:
                return {
                    "task_id": task_id,
                    "status": TaskStatus.FAILED,
                    "error": "Workflow execution failed - no final state",
                    "steps_completed": 0,
                    "execution_log": ["Workflow execution failed"]
                }
        
        except Exception as e:
            app_logger.error(f"Task execution failed: {e}")
            return {
                "task_id": task_id,
                "status": TaskStatus.FAILED,
                "error": f"Execution error: {str(e)}",
                "steps_completed": 0,
                "execution_log": [f"Task failed: {str(e)}"]
            }
    
    async def continue_task(self, task_id: str, user_confirmed: bool = True) -> Dict[str, Any]:
        """Continue a task that's waiting for user confirmation"""
        
        try:
            config = {"configurable": {"thread_id": task_id}}
            
            # Get current state
            state_snapshot = await self.app.aget_state(config)
            if not state_snapshot or not state_snapshot.values:
                return {
                    "error": "Task not found",
                    "status": TaskStatus.FAILED
                }
            
            agent_state = state_snapshot.values
            
            if user_confirmed:
                # User confirmed, continue execution
                # Create a new AgentState from the dictionary
                from core.models import AgentState
                updated_state = AgentState(**agent_state)
                updated_state.requires_confirmation = False
                updated_state.status = TaskStatus.RUNNING
                updated_state.execution_log.append("User confirmed action")
                
                # Resume workflow
                final_state = None
                async for state in self.app.astream(updated_state, config=config):
                    final_state = state
                
                if final_state:
                    final_agent_state = list(final_state.values())[0]
                    return {
                        "task_id": task_id,
                        "status": final_agent_state.get("status"),
                        "result": final_agent_state.get("result"),
                        "steps_completed": final_agent_state.get("steps_completed", 0),
                        "execution_log": final_agent_state.get("execution_log", [])
                    }
            else:
                # User declined, cancel task
                return {
                    "task_id": task_id,
                    "status": TaskStatus.CANCELLED,
                    "result": {"success": False, "message": "Task cancelled by user"},
                    "execution_log": agent_state.get("execution_log", []) + ["Task cancelled by user"]
                }
        
        except Exception as e:
            app_logger.error(f"Task continuation failed: {e}")
            return {
                "task_id": task_id,
                "status": TaskStatus.FAILED,
                "error": f"Continuation error: {str(e)}"
            }
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get the current status of a task"""
        
        try:
            config = {"configurable": {"thread_id": task_id}}
            state_snapshot = await self.app.aget_state(config)
            
            if not state_snapshot or not state_snapshot.values:
                return {
                    "error": "Task not found",
                    "status": TaskStatus.FAILED
                }
            
            # In LangGraph, state_snapshot.values contains the current state as a dict
            agent_state = state_snapshot.values
            
            return {
                "task_id": task_id,
                "status": agent_state.get("status"),
                "description": agent_state.get("description"),
                "steps_completed": agent_state.get("steps_completed", 0),
                "max_steps": agent_state.get("max_steps", 10),
                "current_url": agent_state.get("current_url"),
                "requires_confirmation": agent_state.get("requires_confirmation", False),
                "confirmation_message": agent_state.get("confirmation_message"),
                "last_screenshot": agent_state.get("last_screenshot"),
                "execution_log": agent_state.get("execution_log", [])[-5:] if agent_state.get("execution_log") else [],
                "error": agent_state.get("error")
            }
        
        except Exception as e:
            app_logger.error(f"Status retrieval failed: {e}")
            return {
                "error": f"Status error: {str(e)}",
                "status": TaskStatus.FAILED
            }


# Global workflow instance
web_operator_workflow = WebOperatorWorkflow()
