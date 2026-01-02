"""
Worker engine for ContentFlow multi-processing content processing.

This module implements the main WorkerEngine that manages:
- Content processing workers
- Input source loading workers
- Worker lifecycle and graceful shutdown
"""
import logging
import multiprocessing as mp
import signal
import sys
import time
from typing import List

from app.worker.processing_worker import ContentProcessingWorker
from app.worker.source_worker import InputSourceWorker
from app.settings import WorkerSettings, get_settings

logger = logging.getLogger("contentflow.worker.engine")


class WorkerEngine:
    """
    Main engine for managing worker processes.
    
    The engine creates and manages two types of workers:
    1. Content Processing Workers: Execute pipelines on content
    2. Input Source Workers: Discover content and create processing tasks
    
    Features:
    - Multi-processing based parallelism
    - Graceful shutdown handling
    - Worker health monitoring
    - Automatic worker restart on failure
    """
    
    def __init__(self, settings: WorkerSettings = None):
        """
        Initialize the worker engine.
        
        Args:
            settings: Worker configuration (uses default if not provided)
        """
        self.settings = settings or get_settings()
        self.processing_workers: List[mp.Process] = []
        self.source_workers: List[mp.Process] = []
        self.stop_event = mp.Event()
        self.running = False
        
        logger.info(f"Initialized WorkerEngine: {self.settings.WORKER_NAME}")
        logger.info(f"  Processing Workers: {self.settings.NUM_PROCESSING_WORKERS}")
        logger.info(f"  Source Workers: {self.settings.NUM_SOURCE_WORKERS}")
    
    def start(self):
        """Start all worker processes"""
        if self.running:
            logger.warning("WorkerEngine is already running")
            return
        
        logger.info("Starting WorkerEngine...")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Start processing workers
        logger.info(f"Starting {self.settings.NUM_PROCESSING_WORKERS} processing workers...")
        for i in range(self.settings.NUM_PROCESSING_WORKERS):
            worker = self._create_processing_worker(i)
            worker.start()
            self.processing_workers.append(worker)
            logger.info(f"Started processing worker {i} (PID: {worker.pid})")
        
        # Start source workers
        logger.info(f"Starting {self.settings.NUM_SOURCE_WORKERS} source workers...")
        for i in range(self.settings.NUM_SOURCE_WORKERS):
            worker = self._create_source_worker(i)
            worker.start()
            self.source_workers.append(worker)
            logger.info(f"Started source worker {i} (PID: {worker.pid})")
        
        self.running = True
        logger.info("WorkerEngine started successfully")
    
    def _create_processing_worker(self, worker_id: int) -> mp.Process:
        """Create a content processing worker process"""
        worker = ContentProcessingWorker(
            worker_id=worker_id,
            settings=self.settings,
            stop_event=self.stop_event
        )
        
        process = mp.Process(
            target=worker.run,
            name=f"ProcessingWorker-{worker_id}"
        )
        process.daemon = False  # Allow graceful shutdown
        
        return process
    
    def _create_source_worker(self, worker_id: int) -> mp.Process:
        """Create an input source worker process"""
        worker = InputSourceWorker(
            worker_id=worker_id,
            settings=self.settings,
            stop_event=self.stop_event
        )
        
        process = mp.Process(
            target=worker.run,
            name=f"SourceWorker-{worker_id}"
        )
        process.daemon = False  # Allow graceful shutdown
        
        return process
    
    def stop(self):
        """Stop all worker processes gracefully"""
        if not self.running:
            logger.warning("WorkerEngine is not running")
            return
        
        logger.info("Stopping WorkerEngine...")
        
        # Signal all workers to stop
        self.stop_event.set()
        
        # Wait for processing workers to finish
        logger.info("Waiting for processing workers to stop...")
        for worker in self.processing_workers:
            worker.join(timeout=30)
            if worker.is_alive():
                logger.warning(f"Worker {worker.name} did not stop gracefully, terminating...")
                worker.terminate()
                worker.join(timeout=5)
                if worker.is_alive():
                    logger.error(f"Worker {worker.name} could not be terminated")
        
        # Wait for source workers to finish
        logger.info("Waiting for source workers to stop...")
        for worker in self.source_workers:
            worker.join(timeout=30)
            if worker.is_alive():
                logger.warning(f"Worker {worker.name} did not stop gracefully, terminating...")
                worker.terminate()
                worker.join(timeout=5)
                if worker.is_alive():
                    logger.error(f"Worker {worker.name} could not be terminated")
        
        self.running = False
        logger.info("WorkerEngine stopped")
    
    def run(self):
        """
        Run the engine (blocking).
        
        This method starts all workers and monitors their health
        until a shutdown signal is received.
        """
        self.start()
        
        try:
            # Main monitoring loop
            logger.info("Monitoring workers... (Press Ctrl+C to stop)")
            
            while not self.stop_event.is_set():
                # Check worker health
                self._check_worker_health()
                
                # Sleep between health checks
                time.sleep(30)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.stop()
    
    def _check_worker_health(self):
        """Check health of all workers and restart if needed"""
        # Check processing workers
        for i, worker in enumerate(self.processing_workers):
            if not worker.is_alive() and not self.stop_event.is_set():
                logger.warning(f"Processing worker {i} died, restarting...")
                new_worker = self._create_processing_worker(i)
                new_worker.start()
                self.processing_workers[i] = new_worker
                logger.info(f"Restarted processing worker {i} (PID: {new_worker.pid})")
        
        # Check source workers
        for i, worker in enumerate(self.source_workers):
            if not worker.is_alive() and not self.stop_event.is_set():
                logger.warning(f"Source worker {i} died, restarting...")
                new_worker = self._create_source_worker(i)
                new_worker.start()
                self.source_workers[i] = new_worker
                logger.info(f"Restarted source worker {i} (PID: {new_worker.pid})")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"WorkerEngine received signal {signum}")
        self.stop_event.set()
    
    def get_status(self) -> dict:
        """
        Get current engine status.
        
        Returns:
            Dictionary with engine status information
        """
        return {
            "running": self.running,
            "processing_workers": {
                "configured": self.settings.NUM_PROCESSING_WORKERS,
                "active": sum(1 for w in self.processing_workers if w.is_alive()),
                "workers": [
                    {
                        "id": i,
                        "pid": w.pid,
                        "alive": w.is_alive()
                    }
                    for i, w in enumerate(self.processing_workers)
                ]
            },
            "source_workers": {
                "configured": self.settings.NUM_SOURCE_WORKERS,
                "active": sum(1 for w in self.source_workers if w.is_alive()),
                "workers": [
                    {
                        "id": i,
                        "pid": w.pid,
                        "alive": w.is_alive()
                    }
                    for i, w in enumerate(self.source_workers)
                ]
            }
        }
