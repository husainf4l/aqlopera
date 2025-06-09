#!/usr/bin/env python3
import asyncio
import os
import json
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

async def test_detailed_llm():
    try:
        llm = ChatOpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            model='gpt-4o',
            temperature=0.1
        )
        
        # Use the exact prompt from the LLM tool
        system_prompt = """You are an expert web automation agent. Your job is to analyze a webpage and plan the next actions to complete a given task.

You can perform these actions:
- NAVIGATE: Go to a URL
- CLICK: Click on an element
- TYPE: Enter text into a field
- SCROLL: Scroll the page
- SCREENSHOT: Take a screenshot
- EXTRACT_TEXT: Extract text from elements
- WAIT: Wait for an element or time
- CONFIRM: Ask for user confirmation
- FILL_FORM: Fill out a form

Given the current page analysis and task description, return a JSON list of actions to take.
Each action should have: action_type, target (CSS selector or description), value (if needed), and reason.

Be specific and practical. If you need to click something, identify the exact element.
If you need to type, specify what text to enter.
Always include a clear reason for each action.

Current page analysis:
- URL: https://example.com
- Title: Test Page
- Available elements: [
  {
    "index": 1,
    "tag": "button",
    "text": "Submit",
    "coordinates": [100, 200],
    "clickable": true
  }
]

Task: Click the submit button

Return only a JSON array of actions."""
        
        response = await llm.ainvoke([HumanMessage(content=system_prompt)])
        
        print(f'Response content: {repr(response.content)}')
        print('---')
        
        # Test JSON parsing
        content = response.content.strip()
        print(f'Content after strip: {repr(content)}')
        
        # Check for markdown
        if content.startswith('```json'):
            content = content[7:]
            print(f'After removing ```json: {repr(content)}')
        if content.endswith('```'):
            content = content[:-3]
            print(f'After removing ```: {repr(content)}')
            
        print(f'Final content to parse: {repr(content)}')
        
        try:
            parsed = json.loads(content.strip())
            print(f'Successfully parsed JSON: {parsed}')
        except Exception as e:
            print(f'JSON parse error: {e}')
        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_detailed_llm())
