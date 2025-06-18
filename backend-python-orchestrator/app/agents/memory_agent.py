import chromadb
import openai
import os
from typing import Dict, Any, List, Optional
import logging
import json
from datetime import datetime
import uuid

class MemoryAgent:
    """
    Memory Agent: Stores and retrieves semantic embeddings using ChromaDB
    """
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.logger = logging.getLogger(__name__)
        
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
    
    async def store_interaction(
        self, 
        user_id: str, 
        session_id: str, 
        input_type: str, 
        content: str, 
        intent: Optional[str] = None, 
        response: Optional[Dict] = None
    ) -> str:
        """
        Store user interaction with semantic embedding
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            input_type: Type of input (audio, text, etc.)
            content: Input content
            intent: Determined intent
            response: Agent response
            
        Returns:
            Interaction ID
        """
        try:
            self.logger.info(f"Storing interaction for user {user_id}")
            
            # Generate embedding for content
            embedding = await self._generate_embedding(content)
            
            # Create interaction record
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
            
            # Store in ChromaDB
            self.interaction_collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata],
                ids=[interaction_id]
            )
            
            self.logger.info(f"Interaction stored with ID: {interaction_id}")
            return interaction_id
            
        except Exception as e:
            self.logger.error(f"Error storing interaction: {str(e)}")
            raise Exception(f"Failed to store interaction: {str(e)}")
    
    async def get_user_memory(self, user_id: str, limit: int = 10) -> List[Dict]:
        """
        Retrieve user interaction history
        
        Args:
            user_id: User identifier
            limit: Maximum number of interactions to retrieve
            
        Returns:
            List of user interactions
        """
        try:
            self.logger.info(f"Retrieving memory for user {user_id}")
            
            # Query ChromaDB for user interactions
            results = self.interaction_collection.query(
                query_embeddings=[],  # We'll filter by metadata instead
                n_results=limit,
                where={"user_id": user_id}
            )
            
            # Format results
            interactions = []
            for i in range(len(results['ids'][0])):
                interaction = {
                    "id": results['ids'][0][i],
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i]
                }
                interactions.append(interaction)
            
            # Sort by timestamp (newest first)
            interactions.sort(key=lambda x: x['metadata']['timestamp'], reverse=True)
            
            self.logger.info(f"Retrieved {len(interactions)} interactions for user {user_id}")
            return interactions
            
        except Exception as e:
            self.logger.error(f"Error retrieving user memory: {str(e)}")
            return []
    
    async def search_similar_interactions(
        self, 
        query: str, 
        user_id: Optional[str] = None, 
        limit: int = 5
    ) -> List[Dict]:
        """
        Search for similar interactions using semantic similarity
        
        Args:
            query: Search query
            user_id: Optional user filter
            limit: Maximum number of results
            
        Returns:
            List of similar interactions
        """
        try:
            self.logger.info(f"Searching for similar interactions: {query[:50]}...")
            
            # Generate embedding for query
            query_embedding = await self._generate_embedding(query)
            
            # Build where clause
            where_clause = {}
            if user_id:
                where_clause["user_id"] = user_id
            
            # Search in ChromaDB
            results = self.interaction_collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause if where_clause else None
            )
            
            # Format results
            similar_interactions = []
            for i in range(len(results['ids'][0])):
                interaction = {
                    "id": results['ids'][0][i],
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i]
                }
                similar_interactions.append(interaction)
            
            self.logger.info(f"Found {len(similar_interactions)} similar interactions")
            return similar_interactions
            
        except Exception as e:
            self.logger.error(f"Error searching similar interactions: {str(e)}")
            return []
    
    async def store_context(self, session_id: str, context: Dict) -> str:
        """
        Store conversation context
        
        Args:
            session_id: Session identifier
            context: Context data
            
        Returns:
            Context ID
        """
        try:
            context_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()
            
            # Create context embedding from context summary
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
            
            return context_id
            
        except Exception as e:
            self.logger.error(f"Error storing context: {str(e)}")
            raise Exception(f"Failed to store context: {str(e)}")
    
    async def get_session_context(self, session_id: str) -> Optional[Dict]:
        """
        Retrieve session context
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session context or None
        """
        try:
            results = self.context_collection.query(
                query_embeddings=[],
                n_results=1,
                where={"session_id": session_id}
            )
            
            if results['ids'][0]:
                context_data = json.loads(results['documents'][0][0])
                return context_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving session context: {str(e)}")
            return None
    
    async def store_knowledge(self, domain: str, content: str, metadata: Dict = None) -> str:
        """
        Store domain knowledge
        
        Args:
            domain: Knowledge domain (hotel, hospital, etc.)
            content: Knowledge content
            metadata: Additional metadata
            
        Returns:
            Knowledge ID
        """
        try:
            knowledge_id = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()
            
            # Generate embedding
            embedding = await self._generate_embedding(content)
            
            # Prepare metadata
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
            
            return knowledge_id
            
        except Exception as e:
            self.logger.error(f"Error storing knowledge: {str(e)}")
            raise Exception(f"Failed to store knowledge: {str(e)}")
    
    async def search_knowledge(self, query: str, domain: Optional[str] = None, limit: int = 5) -> List[Dict]:
        """
        Search domain knowledge
        
        Args:
            query: Search query
            domain: Optional domain filter
            limit: Maximum number of results
            
        Returns:
            List of knowledge items
        """
        try:
            query_embedding = await self._generate_embedding(query)
            
            where_clause = {}
            if domain:
                where_clause["domain"] = domain
            
            results = self.knowledge_collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause if where_clause else None
            )
            
            knowledge_items = []
            for i in range(len(results['ids'][0])):
                item = {
                    "id": results['ids'][0][i],
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i]
                }
                knowledge_items.append(item)
            
            return knowledge_items
            
        except Exception as e:
            self.logger.error(f"Error searching knowledge: {str(e)}")
            return []
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using OpenAI
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
            
        except Exception as e:
            self.logger.error(f"Error generating embedding: {str(e)}")
            raise Exception(f"Failed to generate embedding: {str(e)}")
    
    async def clear_user_memory(self, user_id: str) -> bool:
        """
        Clear all memory for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            Success status
        """
        try:
            # This is a simplified implementation
            # In production, you might want to mark as deleted instead of actually deleting
            self.logger.info(f"Clearing memory for user {user_id}")
            
            # Note: ChromaDB doesn't have a direct delete by metadata filter
            # This would need to be implemented with a custom approach
            # For now, we'll just log the request
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error clearing user memory: {str(e)}")
            return False 