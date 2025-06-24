"""
Optimization Implementations for Voice Agent Orchestrator
Critical performance and scalability improvements
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Any, Optional, Callable
from functools import wraps
from contextlib import asynccontextmanager
import psutil
import gc
import structlog

# Import required libraries (add to requirements.txt)
try:
    import redis.asyncio as aioredis
    import slowapi
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    from tenacity import retry, stop_after_attempt, wait_exponential
except ImportError as e:
    print(f"Missing optimization dependencies: {e}")
    print("Install with: pip install redis slowapi tenacity psutil")

logger = logging.getLogger(__name__)

# ============================================================================
# 1. DATABASE CONNECTION POOLING
# ============================================================================

class DatabaseManager:
    """Centralized database connection management with pooling"""
    
    def __init__(self):
        self.redis_pool = None
        self.chroma_client = None
        self._initialized = False
    
    async def initialize(self, redis_url: str = "redis://localhost:6379"):
        """Initialize all database connections with proper pooling"""
        try:
            # Redis connection pool
            self.redis_pool = aioredis.ConnectionPool.from_url(
                redis_url,
                max_connections=20,
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            
            # ChromaDB client with optimized settings
            import chromadb
            self.chroma_client = chromadb.PersistentClient(
                path="./chroma_db",
                settings=chromadb.Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                    is_persistent=True
                )
            )
            
            self._initialized = True
            logger.info("Database connections initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connections: {e}")
            raise
    
    @asynccontextmanager
    async def get_redis_connection(self):
        """Get Redis connection from pool"""
        if not self._initialized:
            raise RuntimeError("DatabaseManager not initialized")
        
        redis = aioredis.Redis(connection_pool=self.redis_pool)
        try:
            yield redis
        finally:
            await redis.close()
    
    def get_chroma_client(self):
        """Get ChromaDB client"""
        if not self._initialized:
            raise RuntimeError("DatabaseManager not initialized")
        return self.chroma_client

# Global database manager instance
db_manager = DatabaseManager()

# ============================================================================
# 2. CACHING STRATEGY
# ============================================================================

class CacheManager:
    """Advanced caching with Redis backend"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            self.redis = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis.ping()
            self._initialized = True
            logger.info("Cache manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize cache manager: {e}")
            raise
    
    async def cache_result(self, key: str, data: dict, ttl: int = 3600):
        """Cache data with TTL"""
        if not self._initialized:
            return
        
        try:
            await self.redis.setex(key, ttl, json.dumps(data))
            logger.debug(f"Cached data for key: {key}")
        except Exception as e:
            logger.warning(f"Failed to cache data: {e}")
    
    async def get_cached(self, key: str) -> Optional[dict]:
        """Retrieve cached data"""
        if not self._initialized:
            return None
        
        try:
            data = await self.redis.get(key)
            if data:
                logger.debug(f"Cache hit for key: {key}")
                return json.loads(data)
            return None
        except Exception as e:
            logger.warning(f"Failed to retrieve cached data: {e}")
            return None
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        if not self._initialized:
            return
        
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries")
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")

# Global cache manager instance
cache_manager = CacheManager()

def cache_result(ttl: int = 3600, key_prefix: str = ""):
    """Decorator for caching function results"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached = await cache_manager.get_cached(cache_key)
            if cached:
                return cached
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.cache_result(cache_key, result, ttl)
            return result
        return wrapper
    return decorator

# ============================================================================
# 3. RATE LIMITING
# ============================================================================

class RateLimiter:
    """Custom rate limiter with Redis backend"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis = None
    
    async def initialize(self):
        """Initialize Redis connection for rate limiting"""
        try:
            self.redis = aioredis.from_url(self.redis_url)
            await self.redis.ping()
            logger.info("Rate limiter initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize rate limiter: {e}")
            raise
    
    async def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed within rate limit"""
        try:
            current = await self.redis.get(key)
            if current is None:
                await self.redis.setex(key, window, 1)
                return True
            
            count = int(current)
            if count < limit:
                await self.redis.incr(key)
                return True
            
            return False
        except Exception as e:
            logger.warning(f"Rate limiting check failed: {e}")
            return True  # Allow request if rate limiting fails
    
    async def get_remaining(self, key: str, limit: int) -> int:
        """Get remaining requests allowed"""
        try:
            current = await self.redis.get(key)
            if current is None:
                return limit
            return max(0, limit - int(current))
        except Exception as e:
            logger.warning(f"Failed to get remaining requests: {e}")
            return limit

# Global rate limiter instance
rate_limiter = RateLimiter()

# ============================================================================
# 4. ASYNC CONCURRENCY OPTIMIZATION
# ============================================================================

class ConcurrentProcessor:
    """Optimized concurrent processing with semaphores and batching"""
    
    def __init__(self, max_concurrent: int = 50, max_workers: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.executor = asyncio.get_event_loop().run_in_executor
        self.max_workers = max_workers
        self._executor_pool = None
    
    async def process_batch(self, items: List[Dict], processor_func: Callable) -> List[Dict]:
        """Process items in batches with controlled concurrency"""
        if not items:
            return []
        
        async def process_item(item):
            async with self.semaphore:
                return await processor_func(item)
        
        # Process items concurrently
        tasks = [process_item(item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch processing error: {result}")
            else:
                valid_results.append(result)
        
        return valid_results
    
    async def process_with_timeout(self, items: List[Dict], processor_func: Callable, 
                                 timeout: float = 30.0) -> List[Dict]:
        """Process items with timeout protection"""
        try:
            return await asyncio.wait_for(
                self.process_batch(items, processor_func),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Batch processing timed out after {timeout}s")
            return []

# Global concurrent processor
concurrent_processor = ConcurrentProcessor()

# ============================================================================
# 5. MEMORY MANAGEMENT
# ============================================================================

class MemoryMonitor:
    """Memory usage monitoring and garbage collection"""
    
    def __init__(self, warning_threshold: float = 80.0, critical_threshold: float = 90.0):
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.logger = logging.getLogger(__name__)
    
    def check_memory_usage(self) -> Dict[str, float]:
        """Check current memory usage and trigger GC if needed"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            result = {
                "memory_percent": memory_percent,
                "memory_mb": memory_info.rss / 1024 / 1024,
                "cpu_percent": process.cpu_percent(interval=0.1)
            }
            
            # Trigger garbage collection if memory usage is high
            if memory_percent > self.critical_threshold:
                self.logger.critical(f"Critical memory usage: {memory_percent}%")
                gc.collect()
            elif memory_percent > self.warning_threshold:
                self.logger.warning(f"High memory usage: {memory_percent}%")
                gc.collect()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Memory monitoring error: {e}")
            return {"memory_percent": 0, "memory_mb": 0, "cpu_percent": 0}
    
    def get_system_memory(self) -> Dict[str, float]:
        """Get system-wide memory information"""
        try:
            memory = psutil.virtual_memory()
            return {
                "total_gb": memory.total / 1024 / 1024 / 1024,
                "available_gb": memory.available / 1024 / 1024 / 1024,
                "used_percent": memory.percent,
                "free_percent": 100 - memory.percent
            }
        except Exception as e:
            self.logger.error(f"System memory check error: {e}")
            return {}

# Global memory monitor
memory_monitor = MemoryMonitor()

# ============================================================================
# 6. CIRCUIT BREAKER PATTERN
# ============================================================================

class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.logger = logging.getLogger(__name__)
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                self.logger.info("Circuit breaker transitioning to HALF_OPEN")
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful execution"""
        self.failure_count = 0
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.logger.info("Circuit breaker reset to CLOSED")
    
    def _on_failure(self):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status"""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout
        }

# ============================================================================
# 7. API CALL OPTIMIZATION
# ============================================================================

class APIOptimizer:
    """Optimize API calls with batching and caching"""
    
    def __init__(self, batch_size: int = 10, cache_ttl: int = 3600):
        self.batch_size = batch_size
        self.cache_ttl = cache_ttl
        self.pending_requests = []
        self.logger = logging.getLogger(__name__)
    
    @cache_result(ttl=3600, key_prefix="api")
    async def optimized_api_call(self, endpoint: str, data: Dict) -> Dict:
        """Make optimized API call with caching"""
        # Add retry logic with exponential backoff
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=4, max=10)
        )
        async def _make_call():
            # Simulate API call
            await asyncio.sleep(0.1)
            return {"success": True, "data": data, "endpoint": endpoint}
        
        return await _make_call()
    
    async def batch_api_calls(self, requests: List[Dict]) -> List[Dict]:
        """Batch multiple API calls to reduce overhead"""
        if len(requests) < self.batch_size:
            return await self._process_single_batch(requests)
        
        # Split into batches
        batches = [
            requests[i:i + self.batch_size] 
            for i in range(0, len(requests), self.batch_size)
        ]
        
        # Process batches concurrently
        batch_tasks = [self._process_single_batch(batch) for batch in batches]
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Flatten results
        results = []
        for batch_result in batch_results:
            if isinstance(batch_result, Exception):
                self.logger.error(f"Batch processing error: {batch_result}")
            else:
                results.extend(batch_result)
        
        return results
    
    async def _process_single_batch(self, batch: List[Dict]) -> List[Dict]:
        """Process a single batch of API calls"""
        tasks = [self.optimized_api_call(req["endpoint"], req["data"]) for req in batch]
        return await asyncio.gather(*tasks, return_exceptions=True)

# Global API optimizer
api_optimizer = APIOptimizer()

# ============================================================================
# 8. INITIALIZATION AND SETUP
# ============================================================================

async def initialize_optimizations():
    """Initialize all optimization components"""
    try:
        logger.info("Initializing optimization components...")
        
        # Initialize database connections
        await db_manager.initialize()
        
        # Initialize cache manager
        await cache_manager.initialize()
        
        # Initialize rate limiter
        await rate_limiter.initialize()
        
        logger.info("All optimization components initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize optimizations: {e}")
        raise

# ============================================================================
# 9. UTILITY FUNCTIONS
# ============================================================================

async def get_performance_metrics() -> Dict[str, Any]:
    """Get comprehensive performance metrics"""
    try:
        # Memory metrics
        memory_metrics = memory_monitor.check_memory_usage()
        system_memory = memory_monitor.get_system_memory()
        
        # Cache metrics (if Redis is available)
        cache_metrics = {}
        try:
            if cache_manager.redis:
                info = await cache_manager.redis.info()
                cache_metrics = {
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "0B"),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0)
                }
        except Exception as e:
            logger.warning(f"Failed to get cache metrics: {e}")
        
        return {
            "timestamp": time.time(),
            "memory": memory_metrics,
            "system_memory": system_memory,
            "cache": cache_metrics,
            "optimizations_enabled": {
                "database_pooling": db_manager._initialized,
                "caching": cache_manager._initialized,
                "rate_limiting": rate_limiter.redis is not None
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        return {"error": str(e)}

# ============================================================================
# 10. EXAMPLE USAGE
# ============================================================================

async def example_optimized_processing():
    """Example of how to use the optimization components"""
    
    # Initialize optimizations
    await initialize_optimizations()
    
    # Example: Rate-limited API call with caching
    async def process_user_request(user_id: str, data: Dict) -> Dict:
        # Check rate limit
        rate_key = f"user:{user_id}:requests"
        if not await rate_limiter.is_allowed(rate_key, limit=10, window=60):
            raise Exception("Rate limit exceeded")
        
        # Process with caching
        @cache_result(ttl=300, key_prefix=f"user:{user_id}")
        async def _process():
            # Simulate processing
            await asyncio.sleep(0.1)
            return {"user_id": user_id, "processed": True, "data": data}
        
        return await _process()
    
    # Example: Batch processing
    requests = [
        {"user_id": f"user_{i}", "data": {"message": f"test_{i}"}}
        for i in range(20)
    ]
    
    # Process in batches with concurrency control
    results = await concurrent_processor.process_batch(
        requests, 
        lambda req: process_user_request(req["user_id"], req["data"])
    )
    
    # Get performance metrics
    metrics = await get_performance_metrics()
    logger.info(f"Processing completed. Metrics: {metrics}")
    
    return results

def circuit_breaker(func):
    cb = CircuitBreaker()
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await cb.call(func, *args, **kwargs)
    return wrapper

def retry_on_exception(max_attempts=3, delay=1):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay)
            raise last_exc
        return wrapper
    return decorator

def track_metrics(metric_name):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logger = structlog.get_logger(func.__module__)
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info("metric", metric=metric_name, duration=duration, status="success")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error("metric", metric=metric_name, duration=duration, status="error", error=str(e))
                raise
        return wrapper
    return decorator

if __name__ == "__main__":
    # Run example
    asyncio.run(example_optimized_processing()) 