import chromadb
import openai
import structlog
import asyncio
from typing import Dict, Any, List, Optional
import json
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
    Memory Agent: Stores and retrieves semantic embeddings using ChromaDB with optimizations
    """

    def __init__(self):
        self.client = openai.OpenAI(api_key=Config.openai()["api_key"])
        self.logger = structlog.get_logger(__name__)

        # Initialize ChromaDB
        self.chroma_client = chromadb.Client()

        # Create collections for different types of memory
        self.interaction_collection = self.chroma_client.create_collection(
            name="user_interactions",
            metadata={"description": "User interaction history and embeddings"}
        )
        self.context_collection = self.chroma_client.create_collection(
            name="conversation_context",
            metadata={"description": "Conversation context and session data"}
        )
        self.knowledge_collection = self.chroma_client.create_collection(
            name="domain_knowledge",
            metadata={"description": "Domain-specific knowledge base"}
        )

    @track_metrics("store_interaction")
    async def store_interaction(
        self,
        user_id: str,
        session_id: str,
        input_type: str,
        content: str,
        intent: Optional[str] = None,
        response: Optional[Dict] = None
    ) -> str:
        try:
            self.logger.info("Storing interaction", user_id=user_id)

            embedding = await self._generate_embedding(content)
            interaction_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()

            metadata = {
                "user_id": user_id,
                "session_id": session_id,
                "input_type": input_type,
                "intent": intent,
                "timestamp": timestamp,
                "response": json.dumps(response) if response else None
            }

            self.interaction_collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata],
                ids=[interaction_id]
            )

            self.logger.info("Interaction stored", interaction_id=interaction_id)
            return interaction_id

        except Exception as e:
            self.logger.error("Error storing interaction", error=str(e))
            raise Exception(f"Failed to store interaction: {str(e)}")

    @cache_result(ttl=1800, key_prefix="memory")
    async def get_user_memory(self, user_id: str, limit: int = 10) -> List[Dict]:
        try:
            self.logger.info("Retrieving memory", user_id=user_id, limit=limit)

            results = self.interaction_collection.query(
                query_embeddings=[],
                n_results=limit,
                where={"user_id": user_id}
            )

            interactions = []
            for i in range(len(results['ids'][0])):
                interactions.append({
                    "id": results['ids'][0][i],
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i]
                })

            interactions.sort(key=lambda x: x['metadata']['timestamp'], reverse=True)

            self.logger.info("Memory retrieved", user_id=user_id, count=len(interactions))
            return interactions

        except Exception as e:
            self.logger.error("Error retrieving memory", error=str(e))
            return []

    @cache_result(ttl=600, key_prefix="similar_interactions")
    async def search_similar_interactions(
        self,
        query: str,
        user_id: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict]:
        try:
            self.logger.info("Searching similar interactions", query=query[:50], user_id=user_id)

            query_embedding = await self._generate_embedding(query)

            where_clause = {"user_id": user_id} if user_id else None

            results = self.interaction_collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause
            )

            similar_interactions = []
            for i in range(len(results['ids'][0])):
                similar_interactions.append({
                    "id": results['ids'][0][i],
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i]
                })

            self.logger.info("Similar interactions found", count=len(similar_interactions))
            return similar_interactions

        except Exception as e:
            self.logger.error("Error searching similar interactions", error=str(e))
            return []

    @track_metrics("store_context")
    async def store_context(self, session_id: str, context: Dict) -> str:
        try:
            context_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()

            context_summary = json.dumps(context, sort_keys=True)
            embedding = await self._generate_embedding(context_summary)

            metadata = {
                "session_id": session_id,
                "timestamp": timestamp,
                "context_type": "conversation"
            }

            self.context_collection.add(
                embeddings=[embedding],
                documents=[context_summary],
                metadatas=[metadata],
                ids=[context_id]
            )

            self.logger.info("Context stored", context_id=context_id)
            return context_id

        except Exception as e:
            self.logger.error("Error storing context", error=str(e))
            raise Exception(f"Failed to store context: {str(e)}")

    @cache_result(ttl=600, key_prefix="session_context")
    async def get_session_context(self, session_id: str) -> Optional[Dict]:
        try:
            results = self.context_collection.query(
                query_embeddings=[],
                n_results=1,
                where={"session_id": session_id}
            )

            if results['ids'][0]:
                context_data = json.loads(results['documents'][0][0])
                self.logger.info("Session context retrieved", session_id=session_id)
                return context_data

            return None

        except Exception as e:
            self.logger.error("Error retrieving session context", error=str(e))
            return None

    @track_metrics("store_knowledge")
    async def store_knowledge(self, domain: str, content: str, metadata: Dict = None) -> str:
        try:
            knowledge_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()

            embedding = await self._generate_embedding(content)

            knowledge_metadata = {
                "domain": domain,
                "timestamp": timestamp,
                **(metadata or {})
            }

            self.knowledge_collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[knowledge_metadata],
                ids=[knowledge_id]
            )

            self.logger.info("Knowledge stored", knowledge_id=knowledge_id)
            return knowledge_id

        except Exception as e:
            self.logger.error("Error storing knowledge", error=str(e))
            raise Exception(f"Failed to store knowledge: {str(e)}")

    @cache_result(ttl=900, key_prefix="knowledge_search")
    async def search_knowledge(
        self,
        query: str,
        domain: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict]:
        try:
            query_embedding = await self._generate_embedding(query)

            where_clause = {"domain": domain} if domain else None

            results = self.knowledge_collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause
            )

            knowledge_items = []
            for i in range(len(results['ids'][0])):
                knowledge_items.append({
                    "id": results['ids'][0][i],
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i]
                })

            self.logger.info("Knowledge search complete", count=len(knowledge_items))
            return knowledge_items

        except Exception as e:
            self.logger.error("Error searching knowledge", error=str(e))
            return []

    @circuit_breaker
    @track_metrics("embedding_generation")
    async def _generate_embedding(self, text: str) -> List[float]:
        try:
            def sync_call():
                response = self.client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text
                )
                return response.data[0].embedding
            embedding = await asyncio.to_thread(sync_call)
            return embedding
        except Exception as e:
            self.logger.error("Error generating embedding", error=str(e))
            raise Exception(f"Failed to generate embedding: {str(e)}")

    async def clear_user_memory(self, user_id: str) -> bool:
        try:
            self.logger.info("Clearing user memory", user_id=user_id)
            # Note: No direct delete API in ChromaDB
            return True
        except Exception as e:
            self.logger.error("Error clearing user memory", error=str(e))
            return False 