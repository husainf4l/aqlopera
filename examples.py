"""
Example usage scripts for the Web Operator Agent
"""
import asyncio
import aiohttp
import json
from typing import Dict, Any


class WebOperatorClient:
    """Client for interacting with the Web Operator Agent API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        
    async def create_task(self, description: str, url: str = None, max_steps: int = 10) -> Dict[str, Any]:
        """Create a new automation task"""
        
        task_data = {
            "description": description,
            "url": url,
            "max_steps": max_steps,
            "require_confirmation": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/tasks", json=task_data) as response:
                return await response.json()
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status"""
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/tasks/{task_id}") as response:
                return await response.json()
    
    async def confirm_action(self, task_id: str, confirm: bool = True) -> Dict[str, Any]:
        """Confirm or decline a pending action"""
        
        confirmation_data = {
            "task_id": task_id,
            "confirm": confirm
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/tasks/{task_id}/confirm", json=confirmation_data) as response:
                return await response.json()
    
    async def wait_for_completion_or_confirmation(self, task_id: str, max_wait: int = 300) -> Dict[str, Any]:
        """Wait for task completion or user confirmation needed"""
        
        for _ in range(max_wait):
            status = await self.get_task_status(task_id)
            
            if status.get("status") in ["completed", "failed", "cancelled"]:
                return status
            elif status.get("status") == "waiting_user_input":
                print(f"User confirmation needed: {status.get('confirmation_message')}")
                return status
            
            await asyncio.sleep(1)
        
        return {"error": "Timeout waiting for task completion"}


async def example_google_search():
    """Example: Perform a Google search"""
    
    client = WebOperatorClient()
    
    print("🔍 Creating Google search task...")
    task = await client.create_task(
        description="Go to Google and search for 'LangGraph tutorials'",
        url="https://www.google.com",
        max_steps=5
    )
    
    task_id = task["task_id"]
    print(f"Task created: {task_id}")
    
    # Wait for completion or confirmation
    result = await client.wait_for_completion_or_confirmation(task_id)
    
    if result.get("status") == "waiting_user_input":
        # Ask user for confirmation
        user_input = input("Do you want to proceed? (y/n): ")
        confirm = user_input.lower() == 'y'
        
        await client.confirm_action(task_id, confirm)
        
        # Wait for final result
        result = await client.wait_for_completion_or_confirmation(task_id)
    
    print(f"Task result: {json.dumps(result, indent=2)}")


async def example_form_filling():
    """Example: Fill out a contact form"""
    
    client = WebOperatorClient()
    
    print("📝 Creating form filling task...")
    task = await client.create_task(
        description="Fill out the contact form with name 'John Doe', email 'john@example.com', and message 'Hello, I'm interested in your services'",
        url="https://httpbin.org/forms/post",  # Example form
        max_steps=8
    )
    
    task_id = task["task_id"]
    print(f"Task created: {task_id}")
    
    # Monitor task progress
    while True:
        result = await client.get_task_status(task_id)
        status = result.get("status")
        
        print(f"Current status: {status}")
        
        if status == "waiting_user_input":
            print(f"Confirmation needed: {result.get('confirmation_message')}")
            user_input = input("Proceed? (y/n): ")
            await client.confirm_action(task_id, user_input.lower() == 'y')
        elif status in ["completed", "failed", "cancelled"]:
            print(f"Final result: {json.dumps(result, indent=2)}")
            break
        
        await asyncio.sleep(2)


async def example_ecommerce_browsing():
    """Example: Browse an e-commerce site"""
    
    client = WebOperatorClient()
    
    print("🛒 Creating e-commerce browsing task...")
    task = await client.create_task(
        description="Go to an e-commerce site, search for 'laptop', and find products under $1000",
        url="https://www.example-store.com",
        max_steps=15
    )
    
    task_id = task["task_id"]
    print(f"Task created: {task_id}")
    
    # Simple monitoring loop
    result = await client.wait_for_completion_or_confirmation(task_id, max_wait=600)
    print(f"Task result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    print("Web Operator Agent - Example Usage")
    print("=" * 50)
    
    # Choose example to run
    examples = {
        "1": ("Google Search", example_google_search),
        "2": ("Form Filling", example_form_filling),
        "3": ("E-commerce Browsing", example_ecommerce_browsing)
    }
    
    print("Available examples:")
    for key, (name, _) in examples.items():
        print(f"{key}. {name}")
    
    choice = input("\nChoose an example (1-3): ").strip()
    
    if choice in examples:
        name, func = examples[choice]
        print(f"\nRunning: {name}")
        asyncio.run(func())
    else:
        print("Invalid choice!")
