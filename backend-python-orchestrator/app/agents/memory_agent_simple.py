import structlog
import asyncio
import json
import redis
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from app.config import Config
from app.optimization_implementations import (
    cache_result,
    circuit_breaker,
    track_metrics
)

class MemoryAgent:
    """
    Memory Agent: Stores and retrieves conversation memory using Redis (simplified version)
    """

    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self.redis_client = redis.from_url(Config.redis()["url"])
        
    @track_metrics("store_interaction")
    @cache_result(ttl=3600)  # Cache for 1 hour
    async def store_interaction(self, user_id: str, interaction: Dict[str, Any]) -> str:
        """
        Store user interaction in memory
        
        Args:
            user_id: User identifier
            interaction: Interaction data to store
            
        Returns:
            Interaction ID
        """
        try:
            interaction_id = str(uuid.uuid4())
            interaction["id"] = interaction_id
            interaction["timestamp"] = datetime.utcnow().isoformat()
            interaction["user_id"] = user_id
            
            # Store in Redis with TTL of 30 days
            key = f"interaction:{user_id}:{interaction_id}"
            self.redis_client.setex(key, 30 * 24 * 3600, json.dumps(interaction))
            
            # Add to user's interaction list
            list_key = f"user_interactions:{user_id}"
            self.redis_client.lpush(list_key, interaction_id)
            self.redis_client.expire(list_key, 30 * 24 * 3600)  # 30 days TTL
            
            self.logger.info("Interaction stored", user_id=user_id, interaction_id=interaction_id)
            return interaction_id
            
        except Exception as e:
            self.logger.error("Error storing interaction", error=str(e))
            return str(uuid.uuid4())  # Return a fallback ID
    
    @track_metrics("retrieve_interactions")
    @cache_result(ttl=300)  # Cache for 5 minutes
    async def retrieve_interactions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve recent interactions for a user
        
        Args:
            user_id: User identifier
            limit: Maximum number of interactions to retrieve
            
        Returns:
            List of interactions
        """
        try:
            list_key = f"user_interactions:{user_id}"
            interaction_ids = self.redis_client.lrange(list_key, 0, limit - 1)
            
            interactions = []
            for interaction_id in interaction_ids:
                key = f"interaction:{user_id}:{interaction_id.decode()}"
                interaction_data = self.redis_client.get(key)
                if interaction_data:
                    interactions.append(json.loads(interaction_data))
            
            self.logger.info("Interactions retrieved", user_id=user_id, count=len(interactions))
            return interactions
            
        except Exception as e:
            self.logger.error("Error retrieving interactions", error=str(e))
            return []
    
    @track_metrics("store_context")
    async def store_context(self, user_id: str, context: Dict[str, Any]) -> bool:
        """
        Store conversation context
        
        Args:
            user_id: User identifier
            context: Context data to store
            
        Returns:
            Success status
        """
        try:
            key = f"context:{user_id}"
            self.redis_client.setex(key, 24 * 3600, json.dumps(context))  # 24 hours TTL
            
            self.logger.info("Context stored", user_id=user_id)
            return True
            
        except Exception as e:
            self.logger.error("Error storing context", error=str(e))
            return False
    
    @track_metrics("retrieve_context")
    @cache_result(ttl=300)  # Cache for 5 minutes
    async def retrieve_context(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieve conversation context
        
        Args:
            user_id: User identifier
            
        Returns:
            Context data
        """
        try:
            key = f"context:{user_id}"
            context_data = self.redis_client.get(key)
            
            if context_data:
                context = json.loads(context_data)
                self.logger.info("Context retrieved", user_id=user_id)
                return context
            else:
                return {}
                
        except Exception as e:
            self.logger.error("Error retrieving context", error=str(e))
            return {}
    
    @track_metrics("clear_user_memory")
    async def clear_user_memory(self, user_id: str) -> bool:
        """
        Clear all memory for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            Success status
        """
        try:
            # Get all interaction IDs
            list_key = f"user_interactions:{user_id}"
            interaction_ids = self.redis_client.lrange(list_key, 0, -1)
            
            # Delete all interactions
            for interaction_id in interaction_ids:
                key = f"interaction:{user_id}:{interaction_id.decode()}"
                self.redis_client.delete(key)
            
            # Delete the list and context
            self.redis_client.delete(list_key)
            self.redis_client.delete(f"context:{user_id}")
            
            self.logger.info("User memory cleared", user_id=user_id)
            return True
            
        except Exception as e:
            self.logger.error("Error clearing user memory", error=str(e))
            return False



