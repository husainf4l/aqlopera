#!/usr/bin/env python3
"""
Complete end-to-end test of the Web Operator Agent
"""
import asyncio
import requests
import time
import json

API_BASE = "http://localhost:8001"

async def test_complete_workflow():
    """Test a complete workflow without confirmation requirements"""
    
    print("🧪 Testing Complete Web Operator Workflow")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health: {health_data.get('status')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return
    
    # Test 2: Create a simple task without confirmation requirement
    print("\n2. Creating simple task...")
    task_request = {
        "description": "Navigate to httpbin.org and take a screenshot",
        "url": "https://httpbin.org",
        "max_steps": 5,
        "require_confirmation": False,  # No confirmation needed
        "custom_instructions": "Just navigate and take a screenshot"
    }
    
    try:
        response = requests.post(f"{API_BASE}/tasks", json=task_request)
        if response.status_code == 200:
            task_data = response.json()
            task_id = task_data["task_id"]
            print(f"✅ Task created: {task_id}")
        else:
            print(f"❌ Task creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return
    except Exception as e:
        print(f"❌ Task creation error: {e}")
        return
    
    # Test 3: Monitor task execution
    print("\n3. Monitoring task execution...")
    max_wait_time = 60  # Wait up to 60 seconds
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get(f"{API_BASE}/tasks/{task_id}")
            if response.status_code == 200:
                status_data = response.json()
                current_status = status_data.get("status", "unknown")
                steps_completed = status_data.get("steps_completed", 0)
                
                print(f"📊 Status: {current_status}, Steps: {steps_completed}")
                
                if current_status in ["completed", "failed", "cancelled"]:
                    print(f"\n🎯 Final status: {current_status}")
                    
                    # Show execution log
                    execution_log = status_data.get("execution_log", [])
                    if execution_log:
                        print("\n📝 Execution log:")
                        for i, log_entry in enumerate(execution_log[-5:], 1):
                            print(f"   {i}. {log_entry}")
                    
                    # Show error if any
                    error = status_data.get("error")
                    if error:
                        print(f"\n❌ Error: {error}")
                    
                    # Show screenshot path
                    screenshot = status_data.get("last_screenshot")
                    if screenshot:
                        print(f"\n📸 Screenshot: {screenshot}")
                    
                    break
                elif current_status == "waiting_user_input":
                    print("\n⚠️  Task is waiting for user input - auto-confirming...")
                    # Auto-confirm to continue
                    confirm_response = requests.post(f"{API_BASE}/tasks/{task_id}/confirm", json={"confirm": True})
                    if confirm_response.status_code == 200:
                        print("✅ Auto-confirmed action")
                    else:
                        print(f"❌ Auto-confirm failed: {confirm_response.status_code}")
                
                time.sleep(2)  # Wait 2 seconds before checking again
            else:
                print(f"❌ Status check failed: {response.status_code}")
                break
        except Exception as e:
            print(f"❌ Status check error: {e}")
            break
    else:
        print(f"\n⏰ Task monitoring timed out after {max_wait_time} seconds")
    
    # Test 4: List all tasks
    print("\n4. Listing all tasks...")
    try:
        response = requests.get(f"{API_BASE}/tasks")
        if response.status_code == 200:
            tasks_data = response.json()
            if "tasks" in tasks_data and tasks_data["tasks"]:
                tasks = tasks_data["tasks"]
                print(f"📋 Found {len(tasks)} task(s):")
                for task in tasks:
                    print(f"   - {task.get('task_id', 'unknown')}: {task.get('status', 'unknown')} - {task.get('description', 'No description')[:50]}...")
            else:
                print("📋 No tasks found")
        else:
            print(f"❌ Task listing failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Task listing error: {e}")
    
    print("\n🎉 Workflow test completed!")
    print("\n💡 Tips:")
    print("  - Check the screenshots/ directory for captured images")
    print("  - Check logs/operator.log for detailed execution logs") 
    print("  - Visit http://localhost:8001/docs for API documentation")

if __name__ == "__main__":
    asyncio.run(test_complete_workflow())
