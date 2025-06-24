import openai
import os
from typing import Dict, Any, List
import logging
import json
import importlib
from abc import ABC, abstractmethod
import asyncio
from app.config import Config
from app.optimization_implementations import CircuitBreaker, retry_on_exception, track_metrics, cache_result

# BaseTool abstract class
class BaseTool(ABC):
    """Base class for all tool agents"""
    @abstractmethod
    async def execute(self, text: str, context: Dict = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_description(self) -> str:
        pass

# Main ToolAgents
class ToolAgents:
    def __init__(self, sector_config: Dict = None):
        self.client = openai.OpenAI(api_key=Config.openai()["api_key"])
        self.logger = logging.getLogger(__name__)
        self.sector_config = sector_config or self._load_default_config()
        self.tools_registry = {}
        self._load_tools()

    def _load_default_config(self) -> Dict:
        return {
            "sector": "generic",
            "available_tools": ["booking", "information", "reminder", "support", "notification", "search", "help", "greeting", "goodbye"],
            "intent_mapping": {
                "booking": ["book", "reserve", "schedule", "appointment"],
                "information": ["info", "details", "hours", "location", "contact"],
                "reminder": ["remind", "reminder", "alert", "notify"],
                "support": ["help", "support", "assist", "issue"],
                "notification": ["notify", "alert", "message", "sms"],
                "search": ["find", "search", "lookup", "locate"],
                "help": ["help", "assist", "guide", "support"],
                "greeting": ["hello", "hi", "good morning", "good afternoon"],
                "goodbye": ["bye", "goodbye", "see you", "thank you"]
            }
        }

    def _load_tools(self):
        for tool_name in self.sector_config.get("available_tools", []):
            try:
                tool_class = self._get_tool_class(tool_name)
                if tool_class:
                    self.tools_registry[tool_name] = tool_class()
                    self.logger.info(f"Loaded tool: {tool_name}")
                else:
                    self.tools_registry[tool_name] = GenericTool(tool_name, self.client)
                    self.logger.info(f"Loaded generic tool: {tool_name}")
            except Exception as e:
                self.logger.error(f"Failed to load tool {tool_name}: {str(e)}")
                self.tools_registry[tool_name] = GenericTool(tool_name, self.client)

    def _get_tool_class(self, tool_name: str):
        sector = self.sector_config.get("sector", "generic")
        try:
            module_name = f"app.tools.{sector}.{tool_name}_tool"
            module = importlib.import_module(module_name)
            class_name = f"{tool_name.capitalize()}Tool"
            return getattr(module, class_name, None)
        except ImportError:
            return None

    async def route_to_tool(self, intent: str, text: str, context: Dict = None) -> Dict[str, Any]:
        try:
            self.logger.info(f"Routing to tool for intent: {intent}")
            tool_name = self._map_intent_to_tool(intent)
            if tool_name in self.tools_registry:
                tool = self.tools_registry[tool_name]
                return await tool.execute(text, context)
            else:
                return await self._handle_unknown_intent(intent, text, context)
        except Exception as e:
            self.logger.error(f"Error routing to tool: {str(e)}")
            return {
                "response": "I'm sorry, I encountered an error processing your request. Please try again.",
                "success": False,
                "error": str(e)
            }

    def _map_intent_to_tool(self, intent: str) -> str:
        intent_mapping = self.sector_config.get("intent_mapping", {})
        for tool_name, intent_keywords in intent_mapping.items():
            if intent in intent_keywords or any(keyword in intent.lower() for keyword in intent_keywords):
                return tool_name
        default_mapping = {
            "booking": "booking", "information": "information", "reminder": "reminder", "support": "support",
            "notification": "notification", "search": "search", "help": "help", "greeting": "greeting", "goodbye": "goodbye"
        }
        return default_mapping.get(intent, "help")

    async def _handle_unknown_intent(self, intent: str, text: str, context: Dict) -> Dict[str, Any]:
        return {
            "response": f"I'm not sure how to help with '{intent}'. Could you please rephrase your request or ask for help?",
            "success": False,
            "intent": intent
        }

    def get_available_tools(self) -> List[str]:
        return list(self.tools_registry.keys())

    def get_tool_description(self, tool_name: str) -> str:
        if tool_name in self.tools_registry:
            return self.tools_registry[tool_name].get_description()
        return f"Tool '{tool_name}' not found"

    async def add_tool(self, tool_name: str, tool_instance: BaseTool):
        self.tools_registry[tool_name] = tool_instance
        self.logger.info(f"Added new tool: {tool_name}")

    async def remove_tool(self, tool_name: str):
        if tool_name in self.tools_registry:
            del self.tools_registry[tool_name]
            self.logger.info(f"Removed tool: {tool_name}")

# Optimized GenericTool
class GenericTool(BaseTool):
    def __init__(self, tool_name: str, client):
        self.tool_name = tool_name
        self.client = client
        self.logger = logging.getLogger(__name__)
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)

    @track_metrics("generic_tool_execute")
    @retry_on_exception(max_attempts=3, delay=1)
    async def execute(self, text: str, context: Dict = None) -> Dict[str, Any]:
        try:
            response_text = await self._call_openai(text, context)
            return {
                "response": response_text,
                "success": True,
                "tool": self.tool_name
            }
        except Exception as e:
            self.logger.error(f"GenericTool execution error: {str(e)}")
            return {
                "response": f"I encountered an error with {self.tool_name}.",
                "success": False,
                "error": str(e)
            }

    @cache_result(ttl=1800, key_prefix="tool_description")
    def get_description(self) -> str:
        descriptions = {
            "booking": "Handle booking and reservation requests",
            "information": "Provide information and details",
            "reminder": "Set up reminders and notifications",
            "support": "Provide customer support and assistance",
            "notification": "Send notifications and alerts",
            "search": "Search for information and resources",
            "help": "Provide help and guidance",
            "greeting": "Handle greetings and welcome messages",
            "goodbye": "Handle farewell and goodbye messages"
        }
        return descriptions.get(self.tool_name, f"Generic {self.tool_name} tool")

    async def _call_openai(self, text: str, context: Dict = None) -> str:
        prompt = f"""
        You are a helpful AI assistant handling {self.tool_name} requests.

        User request: "{text}"
        Context: {json.dumps(context) if context else 'None'}

        Generate a helpful, professional response for this {self.tool_name} request.
        Keep the response concise and actionable.
        """

        def _api_call():
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"You are a helpful assistant specializing in {self.tool_name}."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200,
                timeout=15
            )
            return response.choices[0].message.content.strip()

        return await asyncio.to_thread(_api_call) 