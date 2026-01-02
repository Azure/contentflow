from functools import lru_cache, update_wrapper
import time
import asyncio
import inspect

def ttl_cache(maxsize: int = 128, typed: bool = False, ttl: int = -1):
    if ttl <= 0:
        ttl = float('inf')  # No expiration if ttl is non-positive

    def wrapper(func):
        cache_data = {}
        func_name = func.__name__
        is_async = asyncio.iscoroutinefunction(func)
        
        def get_cache_key(*args, **kwargs):
            # Create a hashable key for the cache
            # Handle the case where kwargs might contain unhashable values
            def make_hashable(obj):
                """Convert an object to a hashable representation."""
                try:
                    hash(obj)
                    return obj
                except TypeError:
                    if isinstance(obj, dict):
                        return tuple(sorted((k, make_hashable(v)) for k, v in obj.items()))
                    elif isinstance(obj, list):
                        return tuple(make_hashable(item) for item in obj)
                    elif isinstance(obj, set):
                        return tuple(sorted(make_hashable(item) for item in obj))
                    else:
                        return str(obj)
            
            try:
                hashable_args = tuple(make_hashable(arg) for arg in args)
                if kwargs:
                    hashable_kwargs = tuple(sorted((k, make_hashable(v)) for k, v in kwargs.items()))
                    cache_key_tuple = (func_name, hashable_args, hashable_kwargs)
                else:
                    cache_key_tuple = (func_name, hashable_args) if hashable_args else (func_name,)
                return str(cache_key_tuple)
            except (TypeError, RecursionError):
                # Fallback to string representation if all else fails
                return f"({func_name}, {str(args)}, {str(sorted(kwargs.items())) if kwargs else ''})"
        
        async def async_inner(*args, **kwargs):
            cache_key = get_cache_key(*args, **kwargs)
            current_time = time.time()
            
            # Check if we have cached data and if it's still valid
            if cache_key in cache_data:
                result, timestamp = cache_data[cache_key]
                if current_time - timestamp <= ttl:
                    return result
                else:
                    # Cache expired, remove the entry
                    del cache_data[cache_key]
            
            # Execute function and cache the result
            result = await func(*args, **kwargs)
            cache_data[cache_key] = (result, current_time)
            
            # Maintain maxsize limit by removing oldest entries if needed
            if len(cache_data) > maxsize:
                # Remove the oldest entry (simple FIFO strategy)
                oldest_key = next(iter(cache_data))
                del cache_data[oldest_key]
            
            return result
        
        def inner(*args, **kwargs):
            
            cache_key = get_cache_key(*args, **kwargs)
            
            current_time = time.time()
            
            # Check if we have cached data and if it's still valid
            if cache_key in cache_data:
                result, timestamp = cache_data[cache_key]
                if current_time - timestamp <= ttl:
                    return result
                else:
                    # Cache expired, remove the entry
                    del cache_data[cache_key]
            
            # Execute function and cache the result
            result = func(*args, **kwargs)
            cache_data[cache_key] = (result, current_time)
            
            # Maintain maxsize limit by removing oldest entries if needed
            if len(cache_data) > maxsize:
                # Remove the oldest entry (simple FIFO strategy)
                oldest_key = next(iter(cache_data))
                del cache_data[oldest_key]
            
            return result
        
        # Add cache management methods
        def cache_clear():
            cache_data.clear()
        
        def cache_info():
            return {
                'hits': len(cache_data),
                'misses': 0,  # We don't track misses in this implementation
                'maxsize': maxsize,
                'currsize': len(cache_data)
            }
        
        # Choose the appropriate wrapper based on whether func is async
        if is_async:
            async_inner.cache_clear = cache_clear
            async_inner.cache_info = cache_info
            return update_wrapper(async_inner, func)
        else:
            inner.cache_clear = cache_clear
            inner.cache_info = cache_info
            return update_wrapper(inner, func)
    
    return wrapper