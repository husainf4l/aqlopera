"""
Main entry point for the Web Operator Agent
"""
import asyncio
import uvicorn
from api.main import app
from core.config import settings
from core.logging import app_logger


def main():
    """Run the Web Operator Agent server"""
    
    app_logger.info("Starting Web Operator Agent")
    app_logger.info(f"Host: {settings.host}:{settings.port}")
    app_logger.info(f"Debug mode: {settings.debug}")
    
    # Run the server
    uvicorn.run(
        "api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        workers=1  # Single worker to maintain state
    )


if __name__ == "__main__":
    main()
