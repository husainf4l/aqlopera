#!/usr/bin/env python3
"""
Simple client for interacting with the Web Operator Agent
"""
import asyncio
import httpx
import json
import sys
from typing import Optional

class WebOperatorClient:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
    
    async def health_check(self) -> dict:
        """Check system health"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health")
            return response.json()
    
    async def create_task(self, description: str, url: Optional[str] = None, priority: str = "medium") -> dict:
        """Create a new automation task"""
        task_data = {
            "description": description,
            "priority": priority
        }
        if url:
            task_data["url"] = url
        
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/tasks/", json=task_data)
            if response.status_code != 200:
                raise Exception(f"Task creation failed: {response.status_code} - {response.text}")
            return response.json()
    
    async def get_task_status(self, task_id: str) -> dict:
        """Get task status"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/tasks/{task_id}")
            if response.status_code != 200:
                raise Exception(f"Status check failed: {response.status_code}")
            return response.json()
    
    async def confirm_task(self, task_id: str, approved: bool = True, message: str = "") -> dict:
        """Confirm or reject a task that requires user approval"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/tasks/{task_id}/confirm",
                json={"approved": approved, "message": message}
            )
            if response.status_code != 200:
                raise Exception(f"Confirmation failed: {response.status_code}")
            return response.json()
    
    async def list_tasks(self) -> list:
        """List all tasks"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/tasks/")
            if response.status_code != 200:
                raise Exception(f"Task listing failed: {response.status_code}")
            return response.json()
    
    async def wait_for_completion(self, task_id: str, timeout: int = 60) -> dict:
        """Wait for task completion with polling"""
        for _ in range(timeout):
            status = await self.get_task_status(task_id)
            
            if status['status'] in ['completed', 'failed']:
                return status
            
            if status.get('requires_confirmation'):
                print(f"⚠️  Task requires confirmation: {status.get('confirmation_message')}")
                confirm = input("Approve this action? (y/n): ").lower().strip()
                if confirm in ['y', 'yes']:
                    await self.confirm_task(task_id, True, "User approved")
                    print("✅ Confirmation sent")
                else:
                    await self.confirm_task(task_id, False, "User rejected")
                    print("❌ Task rejected")
                    return await self.get_task_status(task_id)
            
            await asyncio.sleep(1)
        
        raise Exception(f"Task {task_id} did not complete within {timeout} seconds")

# Example usage functions
async def example_simple_navigation():
    """Example: Simple navigation"""
    client = WebOperatorClient()
    
    print("🌐 Creating navigation task...")
    task = await client.create_task(
        description="Navigate to https://httpbin.org and take a screenshot",
        url="https://httpbin.org"
    )
    
    task_id = task["task_id"]
    print(f"✅ Task created: {task_id}")
    
    print("⏳ Waiting for completion...")
    result = await client.wait_for_completion(task_id, timeout=30)
    
    print(f"🎯 Result: {result['status']}")
    if result.get('result'):
        print(f"📝 Details: {result['result']}")

async def example_search_task():
    """Example: Search task"""
    client = WebOperatorClient()
    
    print("🔍 Creating search task...")
    task = await client.create_task(
        description="Go to Google, search for 'Web automation with Python', and capture the first 3 results",
        url="https://google.com"
    )
    
    task_id = task["task_id"]
    print(f"✅ Task created: {task_id}")
    
    print("⏳ Waiting for completion...")
    result = await client.wait_for_completion(task_id, timeout=45)
    
    print(f"🎯 Result: {result['status']}")
    if result.get('result'):
        print(f"📝 Details: {result['result']}")

async def interactive_mode():
    """Interactive mode for custom tasks"""
    client = WebOperatorClient()
    
    print("🤖 Web Operator Agent - Interactive Mode")
    print("Type 'quit' to exit, 'help' for commands")
    
    while True:
        try:
            command = input("\n> ").strip()
            
            if command.lower() in ['quit', 'exit']:
                break
            elif command.lower() == 'help':
                print("Commands:")
                print("  health - Check system health")
                print("  list - List all tasks")
                print("  create - Create a new task interactively")
                print("  status <task_id> - Check task status")
                print("  quit - Exit")
            elif command.lower() == 'health':
                health = await client.health_check()
                print(f"Health: {health['status']}, Active tasks: {health['active_tasks']}")
            elif command.lower() == 'list':
                tasks = await client.list_tasks()
                print(f"Found {len(tasks)} tasks:")
                for task in tasks[-5:]:  # Show last 5
                    print(f"  {task['task_id']}: {task['status']} - {task['description'][:50]}...")
            elif command.lower() == 'create':
                description = input("Enter task description: ").strip()
                url = input("Enter starting URL (optional): ").strip()
                priority = input("Enter priority (low/medium/high, default=medium): ").strip() or "medium"
                
                task = await client.create_task(
                    description=description,
                    url=url if url else None,
                    priority=priority
                )
                
                task_id = task["task_id"]
                print(f"✅ Task created: {task_id}")
                
                monitor = input("Monitor task progress? (y/n): ").lower().strip()
                if monitor in ['y', 'yes']:
                    try:
                        result = await client.wait_for_completion(task_id, timeout=60)
                        print(f"🎯 Final status: {result['status']}")
                        if result.get('result'):
                            print(f"📝 Result: {result['result']}")
                    except Exception as e:
                        print(f"❌ Error monitoring task: {str(e)}")
            elif command.startswith('status '):
                task_id = command.split(' ', 1)[1].strip()
                try:
                    status = await client.get_task_status(task_id)
                    print(f"Status: {status['status']}")
                    if status.get('result'):
                        print(f"Result: {status['result']}")
                except Exception as e:
                    print(f"❌ Error: {str(e)}")
            else:
                print("Unknown command. Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("👋 Goodbye!")

async def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == 'interactive':
            await interactive_mode()
        elif sys.argv[1] == 'example1':
            await example_simple_navigation()
        elif sys.argv[1] == 'example2':
            await example_search_task()
        else:
            print("Usage: python client.py [interactive|example1|example2]")
    else:
        # Default: run simple example
        print("Running simple navigation example...")
        await example_simple_navigation()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
