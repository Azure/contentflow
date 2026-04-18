"""
ContentFlow Worker - Multi-processing content processing engine.

This is the main entry point for the ContentFlow worker service.
It starts the worker engine which manages processing and source workers.
It also starts a FastAPI health/status monitoring API.
"""
import logging
import sys
import threading
from pathlib import Path
import uvicorn

from contentflow.utils import setup_logging

from app.engine import WorkerEngine
from app.settings import get_settings, WorkerSettings
from app.startup import run_startup_checks
from app.api import create_app

def print_worker_banner():
    """Print worker banner"""
    banner = """
    ╔════════════════════════════════════════════════════════╗
    ║                                                        ║
    ║       ◆                                                ║
    ║      / ╲                                               ║
    ║     /   ╲              ContentFlow                     ║
    ║    ◆     ◆                                             ║
    ║     ╲   /              Worker Service                  ║
    ║      ╲ /                                               ║
    ║       ◆                                                ║
    ║                                                        ║
    ╚════════════════════════════════════════════════════════╝
    """
    print(banner)
    

def main(settings: WorkerSettings):
    """Main entry point"""
    
    print_worker_banner()
    print("=" * 60)
    print("ContentFlow Worker Service")
    print("=" * 60)
    print(f"Worker Name: {settings.WORKER_NAME}")
    print(f"Processing Workers: {settings.NUM_PROCESSING_WORKERS}")
    print(f"Source Workers: {settings.NUM_SOURCE_WORKERS}")
    print(f"Queue: {settings.STORAGE_WORKER_QUEUE_NAME}")
    if settings.API_ENABLED:
        print(f"API Enabled: http://{settings.API_HOST}:{settings.API_PORT}")
    print("=" * 60)
    
    # Run startup checks with retries (Azure services may need time for DNS/RBAC propagation)
    import time
    max_startup_retries = 5
    print("Running startup validation checks...")
    for _attempt in range(max_startup_retries):
        if run_startup_checks(settings):
            print("✅ Startup validation passed.")
            break
        wait = min(30, 5 * (_attempt + 1))
        print(f"⏳ Startup check failed (attempt {_attempt + 1}/{max_startup_retries}), retrying in {wait}s...")
        time.sleep(wait)
    else:
        print("\033[93m⚠️ Startup validation did not pass after retries, continuing with available config...\033[0m")
    
    # Create worker engine
    print("Creating worker engine...")
    engine = WorkerEngine(settings)
    
    # Start API server in a separate thread if enabled
    api_thread = None
    if settings.API_ENABLED:
        print(f"Starting API server on {settings.API_HOST}:{settings.API_PORT}...")
        app = create_app(settings, engine)
        
        # Run uvicorn in a separate thread
        api_thread = threading.Thread(
            target=uvicorn.run,
            kwargs={
                "app": app,
                "reload": False,
                "host": settings.API_HOST,
                "port": settings.API_PORT,
                "log_level": settings.LOG_LEVEL.lower(),
                "log_config": None  # Disable uvicorn's default logging config
            },
            daemon=True,
            name="APIServerThread"
        )
        api_thread.start()
        print("✅ API server started.")
    
    print("Starting worker engine...")
    
    try:
        # Run the worker engine (blocking)
        engine.run()
        
    except Exception as e:
        print(f"\033[91m🚨 Fatal error: {e}\033[0m")
        sys.exit(1)
    finally:
        # Cleanup
        if api_thread and api_thread.is_alive():
            print("API server will stop with the main process...")
    
    print("Worker service stopped")

settings = get_settings()
setup_logging(settings.LOG_LEVEL)


if __name__ == "__main__":
    main(settings)