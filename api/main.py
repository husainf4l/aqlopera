"""
FastAPI main application for the Web Operator Agent
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
import os
from pathlib import Path

from core.config import settings
from core.models import TaskRequest, TaskResponse, UserConfirmation, TaskStatus
from core.logging import app_logger
from workflow import web_operator_workflow

# Create FastAPI app
app = FastAPI(
    title="Web Operator Agent",
    description="A sophisticated web automation agent inspired by OpenAI's Operator",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for screenshots
if os.path.exists(settings.screenshot_path):
    app.mount("/screenshots", StaticFiles(directory=settings.screenshot_path), name="screenshots")

# In-memory task storage (use Redis in production)
active_tasks: Dict[str, Dict[str, Any]] = {}


@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    app_logger.info("Starting Web Operator Agent API")
    app_logger.info(f"Environment: {settings.environment}")
    app_logger.info(f"Browser type: {settings.browser_type}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    app_logger.info("Shutting down Web Operator Agent API")
    
    # Close browser instances
    from tools.browser import browser_tool
    await browser_tool.close()


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Web Operator Agent API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "create_task": "POST /tasks",
            "get_task": "GET /tasks/{task_id}",
            "confirm_action": "POST /tasks/{task_id}/confirm",
            "list_tasks": "GET /tasks",
            "health": "GET /health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_tasks": len(active_tasks)
    }


@app.post("/tasks", response_model=TaskResponse)
async def create_task(task_request: TaskRequest, background_tasks: BackgroundTasks):
    """Create a new web automation task"""
    
    try:
        # Create task ID
        task_id = await web_operator_workflow.create_task(task_request)
        
        # Create task response
        task_response = TaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            description=task_request.description,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Store task
        active_tasks[task_id] = {
            "request": task_request.dict(),
            "response": task_response.dict(),
            "created_at": datetime.now()
        }
        
        # Execute task in background
        background_tasks.add_task(execute_task_background, task_id, task_request)
        
        app_logger.info(f"Task created: {task_id}")
        return task_response
        
    except Exception as e:
        app_logger.error(f"Task creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Task creation failed: {str(e)}")


async def execute_task_background(task_id: str, task_request: TaskRequest):
    """Execute task in background"""
    try:
        app_logger.info(f"Starting background execution for task: {task_id}")
        
        # Execute the workflow
        result = await web_operator_workflow.execute_task(task_id, task_request)
        
        # Update task storage
        if task_id in active_tasks:
            active_tasks[task_id]["result"] = result
            active_tasks[task_id]["updated_at"] = datetime.now()
        
        app_logger.info(f"Task execution completed: {task_id}")
        
    except Exception as e:
        app_logger.error(f"Background task execution failed: {e}")
        if task_id in active_tasks:
            active_tasks[task_id]["result"] = {
                "task_id": task_id,
                "status": TaskStatus.FAILED,
                "error": str(e)
            }


@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    """Get task status and details"""
    
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        # Get latest status from workflow
        workflow_status = await web_operator_workflow.get_task_status(task_id)
        
        # Combine with stored data
        task_data = active_tasks[task_id]
        task_data.update(workflow_status)
        
        return task_data
        
    except Exception as e:
        app_logger.error(f"Task retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Task retrieval failed: {str(e)}")


@app.post("/tasks/{task_id}/confirm")
async def confirm_action(task_id: str, confirmation: UserConfirmation, background_tasks: BackgroundTasks):
    """Confirm or decline a pending action"""
    
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        app_logger.info(f"User confirmation for task {task_id}: {confirmation.confirm}")
        
        # Continue task execution with user decision
        result = await web_operator_workflow.continue_task(task_id, confirmation.confirm)
        
        # Update task storage
        active_tasks[task_id]["result"] = result
        active_tasks[task_id]["updated_at"] = datetime.now()
        
        return result
        
    except Exception as e:
        app_logger.error(f"Action confirmation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Confirmation failed: {str(e)}")


@app.get("/tasks")
async def list_tasks(limit: int = 10, offset: int = 0):
    """List all tasks"""
    
    tasks = list(active_tasks.values())
    total = len(tasks)
    
    # Apply pagination
    paginated_tasks = tasks[offset:offset + limit]
    
    return {
        "tasks": paginated_tasks,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@app.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a running task"""
    
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        # Mark task as cancelled
        if "result" in active_tasks[task_id]:
            active_tasks[task_id]["result"]["status"] = TaskStatus.CANCELLED
        else:
            active_tasks[task_id]["result"] = {
                "task_id": task_id,
                "status": TaskStatus.CANCELLED,
                "message": "Task cancelled by user"
            }
        
        active_tasks[task_id]["updated_at"] = datetime.now()
        
        return {"message": "Task cancelled", "task_id": task_id}
        
    except Exception as e:
        app_logger.error(f"Task cancellation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cancellation failed: {str(e)}")


@app.get("/screenshots/{filename}")
async def get_screenshot(filename: str):
    """Get a screenshot file"""
    
    screenshot_path = Path(settings.screenshot_path) / filename
    
    if not screenshot_path.exists():
        raise HTTPException(status_code=404, detail="Screenshot not found")
    
    return FileResponse(
        path=screenshot_path,
        media_type="image/png",
        filename=filename
    )


@app.get("/tasks/{task_id}/screenshots")
async def get_task_screenshots(task_id: str):
    """Get all screenshots for a task"""
    
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    screenshot_dir = Path(settings.screenshot_path)
    screenshots = []
    
    if screenshot_dir.exists():
        for screenshot_file in screenshot_dir.glob(f"{task_id}_*.png"):
            screenshots.append({
                "filename": screenshot_file.name,
                "url": f"/screenshots/{screenshot_file.name}",
                "created_at": datetime.fromtimestamp(screenshot_file.stat().st_ctime).isoformat()
            })
    
    return {"task_id": task_id, "screenshots": screenshots}


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    app_logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )
