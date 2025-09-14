import json
import structlog
import asyncio
import requests
from typing import Dict, Any, List
from app.config import Config
from app.optimization_implementations import (
    CircuitBreaker,
    retry_on_exception,
    track_metrics,
    cache_result
)

class IntentSchema:
    def __init__(self, intent: str, confidence: float, entities: Dict[str, Any] = None, context: str = ""):
        self.intent = intent
        self.confidence = confidence
        self.entities = entities or {}
        self.context = context

class OrchestratorAgent:
    """
    Orchestrator Agent: Determines intent and orchestrates conversation flow using Sarvam AI
    """
    
    def __init__(self):
        self.api_key = Config.sarvam()["api_key"]
        self.base_url = Config.sarvam()["base_url"]
        self.logger = structlog.get_logger(__name__)
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        
    @track_metrics("determine_intent")
    @retry_on_exception(max_attempts=3, delay=2)
    @cache_result(ttl=300)  # Cache for 5 minutes
    async def determine_intent(self, user_input: str, context: Dict[str, Any] = None) -> IntentSchema:
        """
        Determine user intent using Sarvam AI chat completion
        
        Args:
            user_input: User's text input
            context: Additional context about the conversation
            
        Returns:
            IntentSchema with determined intent and confidence
        """
        try:
            self.logger.info("Determining intent with Sarvam AI", input_preview=user_input[:100])
            
            # Build the prompt for intent determination
            prompt = self._build_intent_prompt(user_input, context)
            
            def sync_call():
                url = f"{self.base_url}/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "sarvam-llama-2-7b-chat",
                    "messages": [
                        {"role": "system", "content": "You are an intent classification assistant. Analyze the user input and determine their intent."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 200
                }
                
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    return self._parse_intent_response(content)
                else:
                    raise Exception(f"Sarvam AI API error: {response.status_code} - {response.text}")

            intent_result = await asyncio.to_thread(sync_call)
            
            self.logger.info("Intent determined", intent=intent_result.intent, confidence=intent_result.confidence)
            return intent_result
            
        except Exception as e:
            self.logger.error("Error in determine_intent", error=str(e))
            # Return a fallback intent
            return IntentSchema(
                intent="general_inquiry",
                confidence=0.5,
                entities={},
                context="fallback due to error"
            )
    
    def _build_intent_prompt(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """Build the prompt for intent determination"""
        context_str = ""
        if context:
            context_str = f"\nContext: {json.dumps(context, indent=2)}"
        
        return f"""
Analyze the following user input and determine their intent. Respond with a JSON object containing:
- intent: The primary intent (e.g., "book_appointment", "check_balance", "general_inquiry", "complaint")
- confidence: A number between 0 and 1 indicating confidence
- entities: Any relevant entities extracted (names, dates, amounts, etc.)
- context: Brief explanation of the intent

User Input: {user_input}{context_str}

Respond with valid JSON only:
"""
    
    def _parse_intent_response(self, response_content: str) -> IntentSchema:
        """Parse the response from Sarvam AI into IntentSchema"""
        try:
            # Try to extract JSON from the response
            if "```json" in response_content:
                json_start = response_content.find("```json") + 7
                json_end = response_content.find("```", json_start)
                json_str = response_content[json_start:json_end].strip()
            elif "{" in response_content and "}" in response_content:
                json_start = response_content.find("{")
                json_end = response_content.rfind("}") + 1
                json_str = response_content[json_start:json_end]
            else:
                # Fallback parsing
                return IntentSchema(
                    intent="general_inquiry",
                    confidence=0.7,
                    entities={},
                    context=response_content[:100]
                )
            
            data = json.loads(json_str)
            return IntentSchema(
                intent=data.get("intent", "general_inquiry"),
                confidence=float(data.get("confidence", 0.7)),
                entities=data.get("entities", {}),
                context=data.get("context", "")
            )
            
        except Exception as e:
            self.logger.warning("Failed to parse intent response", error=str(e), response=response_content[:200])
            return IntentSchema(
                intent="general_inquiry",
                confidence=0.5,
                entities={},
                context="parsing_error"
            )
    
    @track_metrics("generate_response")
    @retry_on_exception(max_attempts=3, delay=2)
    async def generate_response(self, intent: str, entities: Dict[str, Any], context: Dict[str, Any] = None) -> str:
        """
        Generate a response based on the determined intent
        
        Args:
            intent: The determined intent
            entities: Extracted entities
            context: Additional context
            
        Returns:
            Generated response text
        """
        try:
            self.logger.info("Generating response", intent=intent)
            
            prompt = self._build_response_prompt(intent, entities, context)
            
            def sync_call():
                url = f"{self.base_url}/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "sarvam-llama-2-7b-chat",
                    "messages": [
                        {"role": "system", "content": "You are a helpful voice assistant. Provide clear, concise responses."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 150
                }
                
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    raise Exception(f"Sarvam AI API error: {response.status_code} - {response.text}")

            response_text = await asyncio.to_thread(sync_call)
            
            self.logger.info("Response generated", preview=response_text[:100])
            return response_text
            
        except Exception as e:
            self.logger.error("Error in generate_response", error=str(e))
            return "I apologize, but I'm having trouble processing your request right now. Please try again."
    
    def _build_response_prompt(self, intent: str, entities: Dict[str, Any], context: Dict[str, Any] = None) -> str:
        """Build the prompt for response generation"""
        entities_str = json.dumps(entities, indent=2) if entities else "None"
        context_str = json.dumps(context, indent=2) if context else "None"
        
        return f"""
Based on the following information, generate an appropriate response:

Intent: {intent}
Entities: {entities_str}
Context: {context_str}

Provide a helpful, conversational response that addresses the user's intent. Keep it concise and natural.
"""



