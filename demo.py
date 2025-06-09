#!/usr/bin/env python3
"""
Demo script for the Web Operator Agent
Shows various capabilities and example usage scenarios
"""
import asyncio
import json
import httpx
from datetime import datetime

# Demo configuration
API_BASE_URL = "http://localhost:8001"

async def demo_health_check():
    """Test basic health check"""
    print("🔍 Testing health check...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ System healthy: {data['status']}")
            print(f"📊 Active tasks: {data['active_tasks']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")

async def demo_simple_navigation():
    """Demo simple website navigation"""
    print("\n🌐 Testing simple navigation...")
    
    task_data = {
        "description": "Navigate to https://httpbin.org and take a screenshot",
        "url": "https://httpbin.org",
        "priority": "medium"
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Create task
            response = await client.post(f"{API_BASE_URL}/tasks", json=task_data)
            if response.status_code == 200:
                task = response.json()
                task_id = task["task_id"]
                print(f"✅ Task created: {task_id}")
                
                # Monitor task status
                for i in range(30):  # Wait up to 30 seconds
                    await asyncio.sleep(1)
                    status_response = await client.get(f"{API_BASE_URL}/tasks/{task_id}")
                    if status_response.status_code == 200:
                        task_status = status_response.json()
                        print(f"📊 Status: {task_status['status']}")
                        
                        if task_status['status'] in ['completed', 'failed']:
                            print(f"🎯 Final result: {task_status.get('result', 'No result')}")
                            break
                    else:
                        print(f"❌ Status check failed: {status_response.status_code}")
                        break
            else:
                print(f"❌ Task creation failed: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"❌ Demo failed: {str(e)}")

async def demo_form_interaction():
    """Demo form filling and interaction"""
    print("\n📝 Testing form interaction...")
    
    task_data = {
        "description": "Go to httpbin.org/forms/post, fill out the form with test data, and submit it",
        "url": "https://httpbin.org/forms/post",
        "priority": "high"
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(f"{API_BASE_URL}/tasks", json=task_data)
            if response.status_code == 200:
                task = response.json()
                task_id = task["task_id"]
                print(f"✅ Form task created: {task_id}")
                
                # Monitor progress
                for i in range(45):  # Longer timeout for complex task
                    await asyncio.sleep(1)
                    status_response = await client.get(f"{API_BASE_URL}/tasks/{task_id}")
                    if status_response.status_code == 200:
                        task_status = status_response.json()
                        print(f"📊 Status: {task_status['status']}")
                        
                        # Check if confirmation is needed
                        if task_status.get('requires_confirmation'):
                            print(f"⚠️  Confirmation required: {task_status.get('confirmation_message')}")
                            # Auto-approve for demo
                            confirm_response = await client.post(
                                f"{API_BASE_URL}/tasks/{task_id}/confirm",
                                json={"approved": True, "message": "Auto-approved for demo"}
                            )
                            if confirm_response.status_code == 200:
                                print("✅ Confirmation sent")
                        
                        if task_status['status'] in ['completed', 'failed']:
                            print(f"🎯 Final result: {task_status.get('result', 'No result')}")
                            break
            else:
                print(f"❌ Form task creation failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Form demo failed: {str(e)}")

async def demo_search_task():
    """Demo search functionality"""
    print("\n🔍 Testing search task...")
    
    task_data = {
        "description": "Go to DuckDuckGo, search for 'LangGraph tutorial', and capture the search results",
        "url": "https://duckduckgo.com",
        "priority": "medium"
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(f"{API_BASE_URL}/tasks", json=task_data)
            if response.status_code == 200:
                task = response.json()
                task_id = task["task_id"]
                print(f"✅ Search task created: {task_id}")
                
                # Monitor progress
                for i in range(30):
                    await asyncio.sleep(1)
                    status_response = await client.get(f"{API_BASE_URL}/tasks/{task_id}")
                    if status_response.status_code == 200:
                        task_status = status_response.json()
                        print(f"📊 Status: {task_status['status']}")
                        
                        if task_status['status'] in ['completed', 'failed']:
                            print(f"🎯 Final result: {task_status.get('result', 'No result')}")
                            break
            else:
                print(f"❌ Search task creation failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Search demo failed: {str(e)}")

async def demo_list_tasks():
    """Demo task listing"""
    print("\n📋 Listing all tasks...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE_URL}/tasks")
            if response.status_code == 200:
                data = response.json()
                tasks_list = data.get("tasks", [])
                print(f"📊 Found {data.get('total', 0)} tasks:")
                for task in tasks_list:
                    task_id = task.get('response', {}).get('task_id', 'Unknown')
                    status = task.get('result', {}).get('status', 'Unknown')
                    description = task.get('request', {}).get('description', 'No description')
                    print(f"  - {task_id}: {status} - {description[:50]}...")
            else:
                print(f"❌ Task listing failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Task listing failed: {str(e)}")

async def show_system_info():
    """Show system information"""
    print("🤖 Web Operator Agent Demo")
    print("=" * 50)
    print(f"⏰ Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 API URL: {API_BASE_URL}")
    print(f"📚 Documentation: {API_BASE_URL}/docs")
    print(f"🏥 Health check: {API_BASE_URL}/health")
    print()

async def main():
    """Run all demos"""
    await show_system_info()
    
    # Run basic demos
    await demo_health_check()
    await demo_simple_navigation()
    
    # More complex demos (commented out by default)
    # await demo_form_interaction()
    # await demo_search_task()
    
    await demo_list_tasks()
    
    print("\n🎉 Demo completed!")
    print("💡 Tips:")
    print(f"  - Visit {API_BASE_URL}/docs for interactive API documentation")
    print(f"  - Check logs in ./logs/operator.log for detailed execution info")
    print(f"  - Screenshots are saved in ./screenshots/ directory")
    print("  - Use the API endpoints to create custom automation tasks")

if __name__ == "__main__":
    print("Starting Web Operator Agent Demo...")
    print("Make sure the server is running with: python main.py")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"❌ Demo failed: {str(e)}")
