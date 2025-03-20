from functools import wraps
import inspect
import traceback
from typing import Callable, TypeVar, Any, Optional, Awaitable

from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')
AsyncFunc = Callable[..., Awaitable[T]]
SyncFunc = Callable[..., T]
AnyFunc = TypeVar('AnyFunc', AsyncFunc, SyncFunc)

def catch_errors(
    fallback_value: Optional[Any] = None,
    log_error: bool = True,
    reraise: bool = False,
    error_message: str = "Error in function execution"
) -> Callable[[AnyFunc], AnyFunc]:
    """
    Decorator for catching errors in both synchronous and asynchronous functions.
    
    Args:
        fallback_value: Value to return if an error occurs
        log_error: Whether to log the error
        reraise: Whether to reraise the error after logging
        error_message: Custom error message prefix
        
    Returns:
        Decorated function that handles errors
    """
    def decorator(func: AnyFunc) -> AnyFunc:
        # Get function module for better logging
        module_name = func.__module__
        func_name = func.__qualname__
        func_logger = get_logger(f"{module_name}.{func_name}")
        
        # Check if function is async
        is_async = inspect.iscoroutinefunction(func)
        
        if is_async:
            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if log_error:
                        func_logger.error(
                            f"{error_message}: {str(e)}",
                            exc_info=True
                        )
                        # For extra debugging in development
                        func_logger.debug(f"Error traceback: {traceback.format_exc()}")
                    
                    if reraise:
                        raise
                    
                    return fallback_value
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if log_error:
                        func_logger.error(
                            f"{error_message}: {str(e)}",
                            exc_info=True
                        )
                        # For extra debugging in development
                        func_logger.debug(f"Error traceback: {traceback.format_exc()}")
                    
                    if reraise:
                        raise
                    
                    return fallback_value
            return sync_wrapper
    
    return decorator

async def safe_execute_async(
    func: AsyncFunc,
    *args: Any,
    fallback_value: Optional[Any] = None,
    log_error: bool = True,
    reraise: bool = False,
    error_message: str = "Error executing async function",
    **kwargs: Any
) -> Any:
    """
    Safely execute an async function with error handling
    
    Args:
        func: Async function to execute
        *args: Arguments for the function
        fallback_value: Value to return if an error occurs
        log_error: Whether to log the error
        reraise: Whether to reraise the error after logging
        error_message: Custom error message prefix
        **kwargs: Keyword arguments for the function
        
    Returns:
        Result of the function or fallback value
    """
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        if log_error:
            # Get function module for better logging
            module_name = func.__module__
            func_name = func.__qualname__
            func_logger = get_logger(f"{module_name}.{func_name}")
            
            func_logger.error(
                f"{error_message}: {str(e)}",
                exc_info=True
            )
            # For extra debugging in development
            func_logger.debug(f"Error traceback: {traceback.format_exc()}")
        
        if reraise:
            raise
        
        return fallback_value

def safe_execute(
    func: SyncFunc,
    *args: Any,
    fallback_value: Optional[Any] = None,
    log_error: bool = True,
    reraise: bool = False,
    error_message: str = "Error executing function",
    **kwargs: Any
) -> Any:
    """
    Safely execute a function with error handling
    
    Args:
        func: Function to execute
        *args: Arguments for the function
        fallback_value: Value to return if an error occurs
        log_error: Whether to log the error
        reraise: Whether to reraise the error after logging
        error_message: Custom error message prefix
        **kwargs: Keyword arguments for the function
        
    Returns:
        Result of the function or fallback value
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_error:
            # Get function module for better logging
            module_name = func.__module__
            func_name = func.__qualname__
            func_logger = get_logger(f"{module_name}.{func_name}")
            
            func_logger.error(
                f"{error_message}: {str(e)}",
                exc_info=True
            )
            # For extra debugging in development
            func_logger.debug(f"Error traceback: {traceback.format_exc()}")
        
        if reraise:
            raise
        
        return fallback_value 