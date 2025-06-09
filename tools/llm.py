"""
LLM integration tools for decision making and task planning
"""
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
import json

from core.config import settings
from core.models import ActionRequest, PageAnalysis, ActionType
from core.logging import app_logger


class LLMTool:
    """LLM integration for intelligent decision making"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=0.1
        )
        
    async def plan_actions(self, task_description: str, page_analysis: PageAnalysis) -> List[ActionRequest]:
        """Plan the next actions based on task and current page state"""
        try:
            system_prompt = """You are an expert web automation agent. Your job is to analyze a webpage and plan the next actions to complete a given task.

You can perform these actions (use lowercase):
- navigate: Go to a URL
- click: Click on an element
- type: Enter text into a field
- scroll: Scroll the page
- screenshot: Take a screenshot
- extract_text: Extract text from elements
- wait: Wait for an element or time
- confirm: Ask for user confirmation
- fill_form: Fill out a form

Given the current page analysis and task description, return a JSON list of actions to take.
Each action should have: action_type (lowercase), target (CSS selector or description), value (if needed), and reason.

Be specific and practical. If you need to click something, identify the exact element.
If you need to type, specify what text to enter.
Always include a clear reason for each action.

Current page analysis:
- URL: {url}
- Title: {title}
- Available elements: {elements}

Task: {task}

Return only a JSON array of actions."""

            elements_summary = []
            for i, element in enumerate(page_analysis.elements[:10]):  # Limit to first 10
                elements_summary.append({
                    "index": i + 1,
                    "tag": element.tag,
                    "text": element.text[:100] if element.text else None,
                    "coordinates": element.coordinates,
                    "clickable": element.is_clickable
                })

            prompt = system_prompt.format(
                url=page_analysis.url,
                title=page_analysis.title,
                elements=json.dumps(elements_summary, indent=2),
                task=task_description
            )
            
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            
            app_logger.debug(f"LLM response content: {response.content}")
            app_logger.debug(f"LLM response type: {type(response.content)}")
            
            # Parse the response
            try:
                if not response.content or response.content.strip() == "":
                    app_logger.error("LLM returned empty response")
                    return []
                
                # Clean up response content (remove markdown if present)
                content = response.content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                app_logger.debug(f"Cleaned content for parsing: {content}")
                
                actions_data = json.loads(content)
                actions = []
                
                for action_data in actions_data:
                    action = ActionRequest(
                        action_type=ActionType(action_data["action_type"].lower()),
                        target=action_data.get("target"),
                        value=action_data.get("value"),
                        reason=action_data["reason"]
                    )
                    actions.append(action)
                
                app_logger.info(f"Planned {len(actions)} actions for task")
                return actions
                
            except json.JSONDecodeError as e:
                app_logger.error(f"Failed to parse LLM response: {e}")
                app_logger.debug(f"Raw response: {response.content}")
                app_logger.debug(f"Cleaned content: {content}")
                return []
                
        except Exception as e:
            app_logger.error(f"Action planning failed: {e}")
            return []
    
    async def analyze_task_completion(self, task_description: str, 
                                   page_analysis: PageAnalysis,
                                   execution_log: List[str]) -> Dict[str, Any]:
        """Analyze if the task has been completed successfully"""
        try:
            system_prompt = """You are an expert web automation analyst. Analyze whether a given task has been completed successfully based on the current page state and execution log.

Task: {task}
Current page URL: {url}
Current page title: {title}
Execution log: {log}

Analyze the situation and return a JSON response with:
{{
    "completed": true/false,
    "confidence": 0.0-1.0,
    "reason": "explanation of why task is/isn't complete",
    "next_action_needed": "what should be done next (if not complete)",
    "success_indicators": ["list of indicators that show success"],
    "failure_indicators": ["list of indicators that show failure"]
}}"""

            prompt = system_prompt.format(
                task=task_description,
                url=page_analysis.url,
                title=page_analysis.title,
                log=json.dumps(execution_log[-10:])  # Last 10 log entries
            )
            
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            
            try:
                analysis = json.loads(response.content)
                app_logger.info(f"Task completion analysis: {analysis.get('completed', False)}")
                return analysis
                
            except json.JSONDecodeError:
                return {
                    "completed": False,
                    "confidence": 0.0,
                    "reason": "Failed to analyze completion status",
                    "next_action_needed": "Manual review required",
                    "success_indicators": [],
                    "failure_indicators": ["Analysis error"]
                }
                
        except Exception as e:
            app_logger.error(f"Task completion analysis failed: {e}")
            return {
                "completed": False,
                "confidence": 0.0,
                "reason": f"Analysis error: {str(e)}",
                "next_action_needed": "Manual review required",
                "success_indicators": [],
                "failure_indicators": ["System error"]
            }
    
    async def generate_user_confirmation_message(self, action: ActionRequest, 
                                               page_analysis: PageAnalysis) -> str:
        """Generate a user-friendly confirmation message"""
        try:
            system_prompt = """Generate a clear, concise confirmation message for the user about the next action to be taken.

Action: {action_type} on {target}
Value: {value}
Reason: {reason}
Current page: {url}

Create a user-friendly message asking for confirmation. Be specific about what will happen.
Example: "I'm about to click the 'Submit Order' button to complete your purchase. Is this okay?"

Return only the confirmation message text."""

            prompt = system_prompt.format(
                action_type=action.action_type.value,
                target=action.target or "the page",
                value=action.value or "N/A",
                reason=action.reason,
                url=page_analysis.url
            )
            
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return response.content.strip()
            
        except Exception as e:
            app_logger.error(f"Confirmation message generation failed: {e}")
            return f"I'm about to perform: {action.action_type.value}. Do you want me to proceed?"
    
    async def extract_form_data(self, page_analysis: PageAnalysis, 
                              task_description: str) -> Dict[str, str]:
        """Extract and suggest form data based on the task"""
        try:
            # Find form elements
            form_elements = [el for el in page_analysis.elements 
                           if el.tag in ['input', 'textarea', 'select']]
            
            if not form_elements:
                return {}
            
            system_prompt = """Analyze the form elements and suggest what data should be filled based on the task.

Task: {task}
Form elements found: {elements}

Return a JSON object mapping element attributes (like name, id, or placeholder) to suggested values.
Only suggest realistic, task-appropriate values. Don't include sensitive data like passwords or credit cards.

Example:
{{
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "search_query": "laptops"
}}"""

            elements_data = []
            for el in form_elements[:10]:  # Limit to first 10
                elements_data.append({
                    "tag": el.tag,
                    "attributes": el.attributes,
                    "text": el.text
                })
            
            prompt = system_prompt.format(
                task=task_description,
                elements=json.dumps(elements_data, indent=2)
            )
            
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            
            try:
                form_data = json.loads(response.content)
                app_logger.info(f"Generated form data for {len(form_data)} fields")
                return form_data
                
            except json.JSONDecodeError:
                app_logger.error("Failed to parse form data response")
                return {}
                
        except Exception as e:
            app_logger.error(f"Form data extraction failed: {e}")
            return {}


# Global LLM tool instance
llm_tool = LLMTool()
