#!/usr/bin/env python3
"""
Simple test to manually confirm a task
"""
import asyncio
import aiohttp
import json

async def test_manual_confirm():
    """Test manual confirmation"""
    task_id = "b98adeda-f778-4972-8219-64b7b1e0fee3"  # Use the current task ID
    
    confirmation_data = {
        "task_id": task_id,
        "action_description": "Start task execution",
        "confirm": True
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"http://localhost:8001/tasks/{task_id}/confirm", 
                              json=confirmation_data) as resp:
            print(f"Confirmation status: {resp.status}")
            if resp.status == 200:
                result = await resp.json()
                print("✅ Successfully confirmed!")
                print(json.dumps(result, indent=2))
            else:
                error_text = await resp.text()
                print(f"❌ Confirmation failed: {error_text}")

if __name__ == "__main__":
    asyncio.run(test_manual_confirm())
