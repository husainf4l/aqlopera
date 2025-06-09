#!/usr/bin/env python3
"""
Final comprehensive test of the Web Operator Agent with multiple task types
"""
import requests
import time
import json

API_BASE = "http://localhost:8001"

def test_task(description, url=None, require_confirmation=False):
    """Test a single task"""
    print(f"\n🚀 Testing: {description}")
    
    task_request = {
        "description": description,
        "url": url,
        "max_steps": 8,
        "require_confirmation": require_confirmation,
        "custom_instructions": None
    }
    
    # Create task
    response = requests.post(f"{API_BASE}/tasks", json=task_request)
    if response.status_code != 200:
        print(f"❌ Task creation failed: {response.status_code}")
        return False
    
    task_data = response.json()
    task_id = task_data["task_id"]
    print(f"✅ Task created: {task_id}")
    
    # Monitor execution
    max_wait = 90  # 90 seconds max
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        response = requests.get(f"{API_BASE}/tasks/{task_id}")
        if response.status_code == 200:
            status_data = response.json()
            current_status = status_data.get("status", "unknown")
            steps = status_data.get("steps_completed", 0)
            
            if current_status in ["completed", "failed", "cancelled"]:
                print(f"🎯 Final status: {current_status} (Steps: {steps})")
                
                if current_status == "completed":
                    print("✅ Task completed successfully!")
                else:
                    error = status_data.get("error", "Unknown error")
                    print(f"❌ Task failed: {error}")
                
                # Show last few log entries
                execution_log = status_data.get("execution_log", [])
                if execution_log:
                    print("📝 Last actions:")
                    for log_entry in execution_log[-3:]:
                        print(f"   • {log_entry}")
                
                return current_status == "completed"
            elif current_status == "waiting_user_input":
                print("⚠️  Auto-confirming user input...")
                requests.post(f"{API_BASE}/tasks/{task_id}/confirm", json={"confirm": True})
            
            time.sleep(3)
        else:
            print(f"❌ Status check failed: {response.status_code}")
            return False
    
    print(f"⏰ Task timed out after {max_wait} seconds")
    return False

def main():
    print("🧪 COMPREHENSIVE WEB OPERATOR AGENT TEST")
    print("=" * 60)
    
    # Test 1: Simple navigation
    success1 = test_task(
        "Navigate to httpbin.org and take a screenshot",
        url="https://httpbin.org",
        require_confirmation=False
    )
    
    # Test 2: Different site navigation
    success2 = test_task(
        "Navigate to example.com and take a screenshot", 
        url="https://example.com",
        require_confirmation=False
    )
    
    # Test 3: Site analysis without initial URL
    success3 = test_task(
        "Go to httpbin.org/json and take a screenshot of the JSON response",
        require_confirmation=False
    )
    
    # Summary
    total_tests = 3
    passed_tests = sum([success1, success2, success3])
    
    print(f"\n🎯 FINAL RESULTS")
    print("=" * 60)
    print(f"✅ Tests passed: {passed_tests}/{total_tests}")
    print(f"📊 Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Web Operator Agent is fully functional!")
    else:
        print("⚠️  Some tests failed. Check logs for details.")
    
    # Show final system status
    response = requests.get(f"{API_BASE}/health")
    if response.status_code == 200:
        health_data = response.json()
        active_tasks = health_data.get("active_tasks", 0)
        print(f"🏥 System health: {health_data.get('status')} (Active tasks: {active_tasks})")
    
    print("\n💡 Next steps:")
    print("  • Check screenshots/ for captured images")
    print("  • Visit http://localhost:8001/docs for API documentation")
    print("  • Use the API to create custom automation tasks")

if __name__ == "__main__":
    main()
