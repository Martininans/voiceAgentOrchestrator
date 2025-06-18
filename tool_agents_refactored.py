import openai
import os
from typing import Dict, Any, List, Optional
import logging
import json
from datetime import datetime, timedelta
import importlib
from abc import ABC, abstractmethod

class BaseTool(ABC):
    """Base class for all tool agents"""
    
    @abstractmethod
    async def execute(self, text: str, context: Dict = None) -> Dict[str, Any]:
        """Execute the tool with given input and context"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get tool description"""
        pass

class ToolAgents:
    """
    Generic Tool Agents: Handle any sector-specific services through configurable tools
    """
    
    def __init__(self, sector_config: Dict = None):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.logger = logging.getLogger(__name__)
        
        # Load sector configuration
        self.sector_config = sector_config or self._load_default_config()
        
        # Initialize tools registry
        self.tools_registry = {}
        self._load_tools()
    
    def _load_default_config(self) -> Dict:
        """Load default sector configuration"""
        return {
            "sector": "generic",
            "available_tools": [
                "booking", "information", "reminder", "support", 
                "notification", "search", "help", "greeting", "goodbye"
            ],
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
        """Load available tools based on configuration"""
        for tool_name in self.sector_config.get("available_tools", []):
            try:
                # Try to load sector-specific tool first
                tool_class = self._get_tool_class(tool_name)
                if tool_class:
                    self.tools_registry[tool_name] = tool_class()
                    self.logger.info(f"Loaded tool: {tool_name}")
                else:
                    # Fall back to generic tool
                    self.tools_registry[tool_name] = GenericTool(tool_name)
                    self.logger.info(f"Loaded generic tool: {tool_name}")
            except Exception as e:
                self.logger.error(f"Failed to load tool {tool_name}: {str(e)}")
                # Create a fallback tool
                self.tools_registry[tool_name] = GenericTool(tool_name)
    
    def _get_tool_class(self, tool_name: str):
        """Get tool class for specific sector"""
        sector = self.sector_config.get("sector", "generic")
        
        # Try to import sector-specific tool
        try:
            module_name = f"tools.{sector}.{tool_name}_tool"
            module = importlib.import_module(module_name)
            class_name = f"{tool_name.capitalize()}Tool"
            return getattr(module, class_name, None)
        except ImportError:
            return None
    
    async def route_to_tool(self, intent: str, text: str, context: Dict = None) -> Dict[str, Any]:
        """
        Route request to appropriate tool agent based on intent
        
        Args:
            intent: Determined intent
            text: User input text
            context: Additional context
            
        Returns:
            Tool response
        """
        try:
            self.logger.info(f"Routing to tool for intent: {intent}")
            
            # Map intent to tool
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
        """Map intent to tool name"""
        intent_mapping = self.sector_config.get("intent_mapping", {})
        
        for tool_name, intent_keywords in intent_mapping.items():
            if intent in intent_keywords or any(keyword in intent.lower() for keyword in intent_keywords):
                return tool_name
        
        # Default mapping
        default_mapping = {
            "booking": "booking",
            "information": "information", 
            "reminder": "reminder",
            "support": "support",
            "notification": "notification",
            "search": "search",
            "help": "help",
            "greeting": "greeting",
            "goodbye": "goodbye"
        }
        
        return default_mapping.get(intent, "help")
    
    async def _handle_unknown_intent(self, intent: str, text: str, context: Dict) -> Dict[str, Any]:
        """Handle unknown or unrecognized intents"""
        return {
            "response": f"I'm not sure how to help with '{intent}'. Could you please rephrase your request or ask for help?",
            "success": False,
            "intent": intent
        }
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        return list(self.tools_registry.keys())
    
    def get_tool_description(self, tool_name: str) -> str:
        """Get description for a specific tool"""
        if tool_name in self.tools_registry:
            return self.tools_registry[tool_name].get_description()
        return f"Tool '{tool_name}' not found"
    
    async def add_tool(self, tool_name: str, tool_instance: BaseTool):
        """Add a new tool to the registry"""
        self.tools_registry[tool_name] = tool_instance
        self.logger.info(f"Added new tool: {tool_name}")
    
    async def remove_tool(self, tool_name: str):
        """Remove a tool from the registry"""
        if tool_name in self.tools_registry:
            del self.tools_registry[tool_name]
            self.logger.info(f"Removed tool: {tool_name}")

class GenericTool(BaseTool):
    """Generic tool implementation for any sector"""
    
    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.logger = logging.getLogger(__name__)
    
    async def execute(self, text: str, context: Dict = None) -> Dict[str, Any]:
        """Execute generic tool logic"""
        try:
            # Use GPT-4 to generate appropriate response based on tool type
            response = await self._generate_response(text, context)
            return {
                "response": response,
                "success": True,
                "tool": self.tool_name
            }
        except Exception as e:
            self.logger.error(f"Error executing {self.tool_name}: {str(e)}")
            return {
                "response": f"I encountered an error with {self.tool_name}.",
                "success": False,
                "error": str(e)
            }
    
    def get_description(self) -> str:
        """Get tool description"""
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
    
    async def _generate_response(self, text: str, context: Dict = None) -> str:
        """Generate response using GPT-4"""
        try:
            prompt = f"""
            You are a helpful AI assistant handling {self.tool_name} requests.
            
            User request: "{text}"
            Context: {json.dumps(context) if context else 'None'}
            
            Generate a helpful, professional response for this {self.tool_name} request.
            Keep the response concise and actionable.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"You are a helpful assistant specializing in {self.tool_name}."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return f"I'm here to help with {self.tool_name}. How can I assist you?"

# Example sector-specific tool implementations
class BookingTool(BaseTool):
    """Generic booking tool that can be extended for specific sectors"""
    
    def __init__(self, sector_config: Dict = None):
        self.sector_config = sector_config or {}
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    async def execute(self, text: str, context: Dict = None) -> Dict[str, Any]:
        """Handle booking requests"""
        try:
            # Extract booking details
            booking_details = await self._extract_booking_details(text)
            
            # Generate response based on sector
            response = await self._generate_booking_response(booking_details, context)
            
            return {
                "response": response,
                "success": True,
                "booking_details": booking_details
            }
        except Exception as e:
            return {
                "response": "I encountered an error processing your booking request.",
                "success": False,
                "error": str(e)
            }
    
    def get_description(self) -> str:
        return "Handle booking and reservation requests"
    
    async def _extract_booking_details(self, text: str) -> Dict[str, Any]:
        """Extract booking details from text"""
        try:
            prompt = f"""
            Extract booking details from this text: "{text}"
            
            Return a JSON object with:
            - item_type: what is being booked
            - date: booking date
            - time: booking time
            - quantity: number of items/people
            - special_requests: any special requests
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts booking details."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"item_type": "service", "date": "today", "time": "now"}
    
    async def _generate_booking_response(self, booking_details: Dict, context: Dict) -> str:
        """Generate booking response"""
        sector = self.sector_config.get("sector", "generic")
        
        if sector == "hotel":
            return f"I can help you book a {booking_details.get('item_type', 'room')} for {booking_details.get('date', 'your preferred date')}. What type of room would you prefer?"
        elif sector == "hospital":
            return f"I can help you schedule an appointment for {booking_details.get('item_type', 'medical service')} on {booking_details.get('date', 'your preferred date')}. What department do you need?"
        else:
            return f"I can help you book {booking_details.get('item_type', 'your service')} for {booking_details.get('date', 'your preferred date')}. Please provide more details about your requirements."

class InformationTool(BaseTool):
    """Generic information tool"""
    
    def __init__(self, sector_config: Dict = None):
        self.sector_config = sector_config or {}
    
    async def execute(self, text: str, context: Dict = None) -> Dict[str, Any]:
        """Handle information requests"""
        try:
            # Extract information request
            info_request = await self._extract_info_request(text)
            
            # Generate response
            response = await self._generate_info_response(info_request, context)
            
            return {
                "response": response,
                "success": True,
                "info_request": info_request
            }
        except Exception as e:
            return {
                "response": "I encountered an error processing your information request.",
                "success": False,
                "error": str(e)
            }
    
    def get_description(self) -> str:
        return "Provide information and details"
    
    async def _extract_info_request(self, text: str) -> Dict[str, Any]:
        """Extract information request details"""
        return {"topic": "general", "query": text}
    
    async def _generate_info_response(self, info_request: Dict, context: Dict) -> str:
        """Generate information response"""
        sector = self.sector_config.get("sector", "generic")
        
        if sector == "hotel":
            return "I can provide information about our rooms, amenities, dining options, and services. What would you like to know?"
        elif sector == "hospital":
            return "I can provide information about our departments, visiting hours, emergency services, and appointment scheduling. What would you like to know?"
        else:
            return "I can provide information about our services and offerings. What would you like to know?" 