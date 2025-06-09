#!/usr/bin/env python3
"""
Test script for the Web Operator Agent API
"""
import asyncio
import aiohttp
import json

async def test_simple_task():
    """Test a simple navigation task"""
    
    task_data = {
        "description": "Navigate to Google and take a screenshot",
        "url": "https://www.google.com",
        "max_steps": 3,
        "require_confirmation": False
    }
    
    async with aiohttp.ClientSession() as session:
        # Submit the task
        print("🚀 Submitting task...")
        async with session.post("http://localhost:8001/api/tasks", 
                               json=task_data) as resp:
            if resp.status == 200:
                result = await resp.json()
                task_id = result["task_id"]
                print(f"✅ Task submitted with ID: {task_id}")
            else:
                print(f"❌ Failed to submit task: {resp.status}")
                return
        
        # Monitor task status
        print("\n📊 Monitoring task progress...")
        for i in range(30):  # Wait up to 30 seconds
            async with session.get(f"http://localhost:8001/tasks/{task_id}") as resp:
                if resp.status == 200:
                    status = await resp.json()
                    print(f"Status: {status['status']}")
                    
                    if status["status"] == "waiting_user_input":
                        print("🔄 Task is waiting for user confirmation, auto-confirming...")
                        # Auto-confirm the action
                        confirmation_data = {"confirm": True}
                        async with session.post(f"http://localhost:8001/tasks/{task_id}/confirm", 
                                              json=confirmation_data) as conf_resp:
                            if conf_resp.status == 200:
                                print("✅ Action confirmed, continuing...")
                            else:
                                print(f"❌ Failed to confirm: {conf_resp.status}")
                                break
                    elif status["status"] in ["completed", "failed"]:
                        print(f"✅ Task {status['status']}")
                        print(f"Result: {status.get('result', 'No result')}")
                        break
                else:
                    print(f"❌ Failed to get status: {resp.status}")
                    
            await asyncio.sleep(1)
        
        # Get final result
        async with session.get(f"http://localhost:8001/tasks/{task_id}") as resp:
            if resp.status == 200:
                final_result = await resp.json()
                print("\n📋 Final Result:")
                print(json.dumps(final_result, indent=2))
            else:
                print(f"❌ Failed to get final result: {resp.status}")

if __name__ == "__main__":
    asyncio.run(test_simple_task())
