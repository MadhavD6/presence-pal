import time
import functools
import inspect
from typing import Any, Callable, TypeVar, ParamSpec
from backend.core.logger import logger

P = ParamSpec("P")
R = TypeVar("R")

def log_execution_time(func: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator to log the execution time of a function.
    Logs start and end events with duration.
    """
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        func_name = func.__qualname__
        logger.info(f"Function started: {func_name}")
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            # Log success with duration
            logger.info(
                f"Function completed: {func_name}",
                duration_ms=f"{duration_ms:.2f}",
                status="success"
            )
            return result
        except Exception as e:
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            # Log failure with duration and error
            logger.error(
                f"Function failed: {func_name}",
                duration_ms=f"{duration_ms:.2f}",
                error=str(e),
                status="failed"
            )
            raise e
            
    return wrapper

def log_execution_time_async(func: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator to log the execution time of an async function.
    """
    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        func_name = func.__qualname__
        logger.info(f"Async Function started: {func_name}")
        
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            logger.info(
                f"Async Function completed: {func_name}",
                duration_ms=f"{duration_ms:.2f}",
                status="success"
            )
            return result
        except Exception as e:
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            logger.error(
                f"Async Function failed: {func_name}",
                duration_ms=f"{duration_ms:.2f}",
                error=str(e),
                status="failed"
            )
            raise e
            
    return wrapper
