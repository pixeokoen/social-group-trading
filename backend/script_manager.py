#!/usr/bin/env python3
"""
Centralized Script Manager

This service manages all automated scripts and processes to prevent conflicts,
monitor resource usage, and provide comprehensive logging.

Features:
- Centralized process monitoring
- API call rate limiting and tracking
- Conflict detection and prevention
- Unified logging and reporting
- Resource usage monitoring
"""

import os
import sys
import asyncio
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from collections import defaultdict
import psutil

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import get_db_connection
from alpaca_client import AlpacaClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('script_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProcessType(Enum):
    TRADE_SYNC = "trade_sync"
    PRICE_UPDATE = "price_update"
    LEVEL_MONITOR = "level_monitor"
    NOTIFICATION_CHECK = "notification_check"
    POSITION_SYNC = "position_sync"
    DASHBOARD_SYNC = "dashboard_sync"

@dataclass
class ProcessConfig:
    name: str
    type: ProcessType
    interval_seconds: float
    enabled: bool = True
    max_api_calls_per_minute: int = 50
    priority: int = 1  # 1=highest, 5=lowest
    timeout_seconds: int = 30
    retry_count: int = 3

@dataclass
class ProcessMetrics:
    last_run: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_error: Optional[datetime] = None
    total_runs: int = 0
    success_count: int = 0
    error_count: int = 0
    avg_duration: float = 0.0
    api_calls_last_minute: int = 0
    last_error_message: Optional[str] = None

@dataclass
class ScriptStatus:
    process_name: str
    status: str  # running, stopped, error, disabled
    last_update: datetime
    next_run: Optional[datetime] = None
    metrics: ProcessMetrics = None
    resource_usage: Dict[str, float] = None

class ScriptManager:
    def __init__(self):
        self.processes: Dict[str, ProcessConfig] = {}
        self.metrics: Dict[str, ProcessMetrics] = defaultdict(ProcessMetrics)
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.api_call_tracker: Dict[str, List[datetime]] = defaultdict(list)
        self.lock = threading.Lock()
        self.shutdown_event = asyncio.Event()
        
        # Initialize default processes
        self._initialize_default_processes()
        
        # Start monitoring
        logger.info("[SCRIPT_MANAGER] Script Manager initialized")

    def _initialize_default_processes(self):
        """Initialize default process configurations"""
        self.processes = {
            "trade_sync": ProcessConfig(
                name="Trade Sync",
                type=ProcessType.TRADE_SYNC,
                interval_seconds=30.0,  # Consolidate to 30 seconds
                max_api_calls_per_minute=60,
                priority=1
            ),
            "level_monitor": ProcessConfig(
                name="Level Monitor",
                type=ProcessType.LEVEL_MONITOR,
                interval_seconds=1.0,  # 1 second for critical execution - 60 calls/min max
                max_api_calls_per_minute=60,  # 1 API call per cycle × 60 cycles = 60 calls/min
                priority=1
            ),
            "price_update": ProcessConfig(
                name="Price Update",
                type=ProcessType.PRICE_UPDATE,
                interval_seconds=10.0,  # Batch price updates
                max_api_calls_per_minute=30,
                priority=2
            ),
            "notification_check": ProcessConfig(
                name="Notification Check",
                type=ProcessType.NOTIFICATION_CHECK,
                interval_seconds=5.0,
                max_api_calls_per_minute=20,
                priority=3
            ),
            "position_sync": ProcessConfig(
                name="Position Sync",
                type=ProcessType.POSITION_SYNC,
                interval_seconds=60.0,  # Less frequent
                max_api_calls_per_minute=20,
                priority=4
            ),
            "dashboard_sync": ProcessConfig(
                name="Dashboard Sync",
                type=ProcessType.DASHBOARD_SYNC,
                interval_seconds=30.0,
                max_api_calls_per_minute=15,
                priority=5
            )
        }

    def track_api_call(self, process_name: str, count: int = 1):
        """Track API calls for rate limiting"""
        now = datetime.now()
        with self.lock:
            # Clean old entries (older than 1 minute)
            cutoff = now - timedelta(minutes=1)
            self.api_call_tracker[process_name] = [
                timestamp for timestamp in self.api_call_tracker[process_name]
                if timestamp > cutoff
            ]
            
            # Add new calls
            for _ in range(count):
                self.api_call_tracker[process_name].append(now)
            
            # Update metrics
            self.metrics[process_name].api_calls_last_minute = len(self.api_call_tracker[process_name])

    def can_make_api_calls(self, process_name: str, count: int = 1) -> bool:
        """Check if process can make API calls within rate limits"""
        if process_name not in self.processes:
            return False
            
        config = self.processes[process_name]
        current_calls = self.metrics[process_name].api_calls_last_minute
        
        return (current_calls + count) <= config.max_api_calls_per_minute

    async def run_process(self, process_name: str, func, *args, **kwargs):
        """Run a process with tracking and error handling"""
        if process_name not in self.processes:
            logger.error(f"Unknown process: {process_name}")
            return
            
        config = self.processes[process_name]
        metrics = self.metrics[process_name]
        
        if not config.enabled:
            return
            
        start_time = time.time()
        
        try:
            # Check rate limits
            if hasattr(func, '_api_calls') and not self.can_make_api_calls(process_name, func._api_calls):
                logger.warning(f"[RATE_LIMIT] Rate limit reached for {process_name}, skipping cycle")
                return
            
            logger.debug(f"[RUN] Running {config.name}")
            
            # Run the function with timeout
            result = await asyncio.wait_for(func(*args, **kwargs), timeout=config.timeout_seconds)
            
            # Update success metrics
            end_time = time.time()
            duration = end_time - start_time
            
            metrics.last_run = datetime.now()
            metrics.last_success = datetime.now()
            metrics.total_runs += 1
            metrics.success_count += 1
            
            # Update average duration
            if metrics.avg_duration == 0:
                metrics.avg_duration = duration
            else:
                metrics.avg_duration = (metrics.avg_duration + duration) / 2
            
            # Track API calls - use actual count if returned, otherwise use estimate
            if hasattr(func, '_api_calls'):
                actual_api_calls = func._api_calls  # Default to estimate
                if result is not None and isinstance(result, int) and result >= 0:
                    actual_api_calls = result  # Use actual count if function returned it
                
                self.track_api_call(process_name, actual_api_calls)
            
            logger.debug(f"[SUCCESS] {config.name} completed in {duration:.2f}s")
            return result
            
        except asyncio.TimeoutError:
            error_msg = f"Timeout after {config.timeout_seconds}s"
            self._handle_process_error(process_name, error_msg)
            
        except Exception as e:
            self._handle_process_error(process_name, str(e))

    def _handle_process_error(self, process_name: str, error_msg: str):
        """Handle process errors and update metrics"""
        metrics = self.metrics[process_name]
        
        metrics.last_run = datetime.now()
        metrics.last_error = datetime.now()
        metrics.last_error_message = error_msg
        metrics.total_runs += 1
        metrics.error_count += 1
        
        logger.error(f"[ERROR] {self.processes[process_name].name} failed: {error_msg}")

    async def start_process_loop(self, process_name: str, func, *args, **kwargs):
        """Start a continuous process loop"""
        if process_name not in self.processes:
            logger.error(f"Unknown process: {process_name}")
            return
            
        config = self.processes[process_name]
        logger.info(f"[START] Starting {config.name} (every {config.interval_seconds}s)")
        
        while not self.shutdown_event.is_set():
            cycle_start = time.time()
            
            await self.run_process(process_name, func, *args, **kwargs)
            
            # Calculate sleep time to maintain consistent interval
            cycle_duration = time.time() - cycle_start
            sleep_time = max(0, config.interval_seconds - cycle_duration)
            
            if cycle_duration > config.interval_seconds:
                logger.warning(f"[TIMING] {config.name} cycle took {cycle_duration:.2f}s (longer than {config.interval_seconds}s interval)")
            
            try:
                await asyncio.wait_for(self.shutdown_event.wait(), timeout=sleep_time)
                break  # Shutdown requested
            except asyncio.TimeoutError:
                continue  # Normal timeout, continue loop

    def get_status(self) -> Dict[str, ScriptStatus]:
        """Get current status of all processes"""
        status = {}
        
        for process_name, config in self.processes.items():
            metrics = self.metrics[process_name]
            
            # Determine status
            if not config.enabled:
                process_status = "disabled"
            elif process_name in self.running_tasks:
                if self.running_tasks[process_name].done():
                    process_status = "error" if self.running_tasks[process_name].exception() else "stopped"
                else:
                    process_status = "running"
            else:
                process_status = "stopped"
            
            # Calculate next run time
            next_run = None
            if process_status == "running" and metrics.last_run:
                next_run = metrics.last_run + timedelta(seconds=config.interval_seconds)
            
            # Get resource usage
            resource_usage = self._get_resource_usage()
            
            status[process_name] = ScriptStatus(
                process_name=config.name,
                status=process_status,
                last_update=datetime.now(),
                next_run=next_run,
                metrics=metrics,
                resource_usage=resource_usage
            )
        
        return status

    def _get_resource_usage(self) -> Dict[str, float]:
        """Get current resource usage"""
        try:
            process = psutil.Process()
            return {
                "cpu_percent": process.cpu_percent(),
                "memory_mb": process.memory_info().rss / 1024 / 1024,
                "memory_percent": process.memory_percent()
            }
        except:
            return {"cpu_percent": 0, "memory_mb": 0, "memory_percent": 0}

    def get_api_usage_summary(self) -> Dict[str, Any]:
        """Get API usage summary across all processes"""
        total_calls = sum(len(calls) for calls in self.api_call_tracker.values())
        
        usage_by_process = {}
        for process_name, calls in self.api_call_tracker.items():
            if process_name in self.processes:
                config = self.processes[process_name]
                usage_by_process[process_name] = {
                    "calls_last_minute": len(calls),
                    "limit_per_minute": config.max_api_calls_per_minute,
                    "usage_percent": (len(calls) / config.max_api_calls_per_minute) * 100,
                    "process_name": config.name
                }
        
        return {
            "total_calls_last_minute": total_calls,
            "estimated_calls_per_hour": total_calls * 60,
            "usage_by_process": usage_by_process,
            "timestamp": datetime.now().isoformat()
        }

    def log_status_report(self):
        """Log comprehensive status report"""
        logger.info("=" * 80)
        logger.info("[STATUS] SCRIPT MANAGER STATUS REPORT")
        logger.info("=" * 80)
        
        status = self.get_status()
        api_usage = self.get_api_usage_summary()
        
        # Process status
        for process_name, process_status in status.items():
            metrics = process_status.metrics
            logger.info(f"[PROCESS] {process_status.process_name}:")
            logger.info(f"   Status: {process_status.status}")
            logger.info(f"   Runs: {metrics.total_runs} (SUCCESS: {metrics.success_count}, ERRORS: {metrics.error_count})")
            logger.info(f"   Last: {metrics.last_run.strftime('%H:%M:%S') if metrics.last_run else 'Never'}")
            logger.info(f"   Avg Duration: {metrics.avg_duration:.2f}s")
            logger.info(f"   API Calls/min: {metrics.api_calls_last_minute}")
            if metrics.last_error_message:
                logger.info(f"   Last Error: {metrics.last_error_message}")
        
        # API usage summary
        logger.info(f"[API] Usage: {api_usage['total_calls_last_minute']} calls/minute")
        logger.info(f"[API] Projected: ~{api_usage['estimated_calls_per_hour']} calls/hour")
        
        # Resource usage
        resource = self._get_resource_usage()
        logger.info(f"[SYSTEM] CPU: {resource['cpu_percent']:.1f}%, Memory: {resource['memory_mb']:.1f}MB")
        
        logger.info("=" * 80)

    async def start_all_processes(self):
        """Start all enabled processes"""
        logger.info("[STARTUP] Starting all processes...")
        
        # Import process functions
        from process_modules.trade_sync import sync_trades_process
        from process_modules.level_monitor import monitor_levels_process  
        from process_modules.price_updater import update_prices_process
        from process_modules.notification_checker import check_notifications_process
        from process_modules.position_sync import sync_positions_process
        from process_modules.dashboard_sync import sync_dashboard_process
        
        # Start process loops
        process_functions = {
            "trade_sync": sync_trades_process,
            "level_monitor": monitor_levels_process,
            "price_update": update_prices_process,
            "notification_check": check_notifications_process,
            "position_sync": sync_positions_process,
            "dashboard_sync": sync_dashboard_process
        }
        
        for process_name, func in process_functions.items():
            if process_name in self.processes and self.processes[process_name].enabled:
                task = asyncio.create_task(
                    self.start_process_loop(process_name, func)
                )
                self.running_tasks[process_name] = task
        
        # Start status reporting
        asyncio.create_task(self._status_reporter())
        
        logger.info(f"[STARTUP] Started {len(self.running_tasks)} processes")

    async def _status_reporter(self):
        """Periodic status reporting"""
        while not self.shutdown_event.is_set():
            try:
                await asyncio.sleep(300)  # Report every 5 minutes
                self.log_status_report()
            except asyncio.CancelledError:
                break

    async def shutdown(self):
        """Gracefully shutdown all processes"""
        logger.info("[SHUTDOWN] Shutting down Script Manager...")
        
        self.shutdown_event.set()
        
        # Cancel all running tasks
        for process_name, task in self.running_tasks.items():
            logger.info(f"Stopping {process_name}...")
            task.cancel()
            
        # Wait for tasks to complete
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
        
        logger.info("[SHUTDOWN] Script Manager shutdown complete")

# Global manager instance
script_manager = ScriptManager()

async def main():
    """Main entry point"""
    try:
        await script_manager.start_all_processes()
        
        # Keep running until interrupted
        while not script_manager.shutdown_event.is_set():
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("[SHUTDOWN] Shutdown requested by user")
    except Exception as e:
        logger.error(f"[FATAL] Fatal error: {e}")
        raise
    finally:
        await script_manager.shutdown()

if __name__ == "__main__":
    asyncio.run(main()) 