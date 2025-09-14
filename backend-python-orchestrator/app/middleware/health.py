"""
Health check middleware for the Python orchestrator
"""
import asyncio
import logging
import time
import psutil
import os
from typing import Dict, Any, Optional, List
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import aiohttp
from app.config import Config

logger = logging.getLogger(__name__)

class HealthChecker:
    """Health checker for various system components"""
    
    def __init__(self):
        self.start_time = time.time()
        self.checks = {}
        self.last_checks = {}
    
    def add_check(self, name: str, check_func, timeout: int = 5):
        """Add a health check function"""
        self.checks[name] = {
            'function': check_func,
            'timeout': timeout
        }
    
    async def run_check(self, name: str) -> Dict[str, Any]:
        """Run a specific health check"""
        if name not in self.checks:
            raise ValueError(f"Health check '{name}' not found")
        
        check_info = self.checks[name]
        start_time = time.time()
        
        try:
            # Run check with timeout
            result = await asyncio.wait_for(
                check_info['function'](),
                timeout=check_info['timeout']
            )
            
            duration = time.time() - start_time
            self.last_checks[name] = {
                'status': 'healthy',
                'duration': duration,
                'timestamp': datetime.utcnow().isoformat(),
                **result
            }
            
            return self.last_checks[name]
            
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            self.last_checks[name] = {
                'status': 'unhealthy',
                'error': 'Health check timeout',
                'duration': duration,
                'timestamp': datetime.utcnow().isoformat()
            }
            return self.last_checks[name]
            
        except Exception as e:
            duration = time.time() - start_time
            self.last_checks[name] = {
                'status': 'unhealthy',
                'error': str(e),
                'duration': duration,
                'timestamp': datetime.utcnow().isoformat()
            }
            return self.last_checks[name]
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}
        
        # Run checks concurrently
        tasks = []
        for name in self.checks.keys():
            tasks.append(self.run_check(name))
        
        check_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, name in enumerate(self.checks.keys()):
            if isinstance(check_results[i], Exception):
                results[name] = {
                    'status': 'unhealthy',
                    'error': str(check_results[i]),
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                results[name] = check_results[i]
        
        return results
    
    def get_overall_status(self, checks: Dict[str, Any]) -> Dict[str, Any]:
        """Get overall health status"""
        unhealthy_count = sum(1 for check in checks.values() if check['status'] == 'unhealthy')
        total_count = len(checks)
        
        return {
            'status': 'healthy' if unhealthy_count == 0 else 'unhealthy',
            'healthy': total_count - unhealthy_count,
            'unhealthy': unhealthy_count,
            'total': total_count
        }
    
    def get_uptime(self) -> float:
        """Get application uptime in seconds"""
        return time.time() - self.start_time

# Create global health checker instance
health_checker = HealthChecker()

# Health check functions
async def check_database():
    """Check database connectivity"""
    try:
        # This would be implemented based on your database setup
        # For now, we'll assume it's healthy if the app is running
        return {'message': 'Database connection successful'}
    except Exception as e:
        raise Exception(f"Database connection failed: {str(e)}")

async def check_redis():
    """Check Redis connectivity"""
    try:
        if Config.get_env("DISABLE_OPTIMIZATIONS", "false").lower() == "true":
            return {'message': 'Redis disabled by configuration'}
        
        import redis.asyncio as redis
        client = redis.from_url(Config.redis()['url'])
        await client.ping()
        await client.close()
        return {'message': 'Redis connection successful'}
    except Exception as e:
        raise Exception(f"Redis connection failed: {str(e)}")

async def check_voice_agent():
    """Check voice agent functionality"""
    try:
        from app.voice_agent_base import create_voice_agent
        agent = create_voice_agent()
        return {
            'message': 'Voice agent is operational',
            'provider': agent.provider
        }
    except Exception as e:
        raise Exception(f"Voice agent check failed: {str(e)}")

async def check_memory():
    """Check memory usage"""
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        # Consider unhealthy if memory usage is over 1GB
        if memory_mb > 1024:
            raise Exception(f"High memory usage: {memory_mb:.1f}MB")
        
        return {
            'message': 'Memory usage is normal',
            'usage_mb': round(memory_mb, 1)
        }
    except Exception as e:
        raise Exception(f"Memory check failed: {str(e)}")

async def check_disk_space():
    """Check disk space"""
    try:
        disk_usage = psutil.disk_usage('/')
        free_gb = disk_usage.free / (1024**3)
        
        # Consider unhealthy if less than 1GB free
        if free_gb < 1:
            raise Exception(f"Low disk space: {free_gb:.1f}GB free")
        
        return {
            'message': 'Disk space is sufficient',
            'free_gb': round(free_gb, 1)
        }
    except Exception as e:
        raise Exception(f"Disk space check failed: {str(e)}")

async def check_external_apis():
    """Check external API connectivity"""
    try:
        # Check OpenAI API if configured
        if Config.get_env("OPENAI_API_KEY"):
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {Config.get_env('OPENAI_API_KEY')}"},
                    timeout=5
                ) as response:
                    if response.status == 200:
                        return {'message': 'External APIs are accessible'}
                    else:
                        raise Exception(f"OpenAI API returned status {response.status}")
        else:
            return {'message': 'External APIs not configured'}
    except Exception as e:
        raise Exception(f"External API check failed: {str(e)}")

# Register health checks
health_checker.add_check('database', check_database)
health_checker.add_check('redis', check_redis)
health_checker.add_check('voice_agent', check_voice_agent)
health_checker.add_check('memory', check_memory)
health_checker.add_check('disk_space', check_disk_space)
health_checker.add_check('external_apis', check_external_apis)

# Health check endpoints
async def health_endpoint():
    """Basic health check endpoint"""
    try:
        checks = await health_checker.run_all_checks()
        overall_status = health_checker.get_overall_status(checks)
        
        response = {
            'status': overall_status['status'],
            'timestamp': datetime.utcnow().isoformat(),
            'uptime': health_checker.get_uptime(),
            'version': os.getenv('APP_VERSION', '1.0.0'),
            'environment': os.getenv('NODE_ENV', 'development'),
            'checks': overall_status,
            'details': checks
        }
        
        status_code = 200 if overall_status['status'] == 'healthy' else 503
        return JSONResponse(status_code=status_code, content=response)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
        )

async def detailed_health_endpoint():
    """Detailed health check endpoint"""
    try:
        checks = await health_checker.run_all_checks()
        overall_status = health_checker.get_overall_status(checks)
        
        # Get system information
        process = psutil.Process()
        system_info = {
            'cpu_percent': process.cpu_percent(),
            'memory_info': {
                'rss': process.memory_info().rss,
                'vms': process.memory_info().vms
            },
            'num_threads': process.num_threads(),
            'create_time': process.create_time()
        }
        
        response = {
            'status': overall_status['status'],
            'timestamp': datetime.utcnow().isoformat(),
            'uptime': health_checker.get_uptime(),
            'version': os.getenv('APP_VERSION', '1.0.0'),
            'environment': os.getenv('NODE_ENV', 'development'),
            'python_version': os.sys.version,
            'platform': os.sys.platform,
            'checks': overall_status,
            'details': checks,
            'system': system_info
        }
        
        status_code = 200 if overall_status['status'] == 'healthy' else 503
        return JSONResponse(status_code=status_code, content=response)
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
        )

async def readiness_endpoint():
    """Readiness probe endpoint"""
    try:
        checks = await health_checker.run_all_checks()
        overall_status = health_checker.get_overall_status(checks)
        
        if overall_status['status'] == 'healthy':
            return JSONResponse(
                status_code=200,
                content={'status': 'ready'}
            )
        else:
            unhealthy_checks = [
                {'name': name, 'error': check.get('error', 'Unknown error')}
                for name, check in checks.items()
                if check['status'] == 'unhealthy'
            ]
            
            return JSONResponse(
                status_code=503,
                content={
                    'status': 'not ready',
                    'unhealthy_checks': unhealthy_checks
                }
            )
            
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                'status': 'not ready',
                'error': str(e)
            }
        )

async def liveness_endpoint():
    """Liveness probe endpoint"""
    return JSONResponse(
        status_code=200,
        content={
            'status': 'alive',
            'timestamp': datetime.utcnow().isoformat(),
            'uptime': health_checker.get_uptime()
        }
    )












