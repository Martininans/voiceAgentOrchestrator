import openai
import os
from typing import Dict, Any, List
import logging
import json

class OrchestratorAgent:
    """
    Orchestrator Agent: Determines intent using GPT-4 and routes to appropriate agents
    """
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.logger = logging.getLogger(__name__)
        
        # Define intents for hotel and hospital services
        self.intents = {
            "hotel": [
                "room_booking", "check_in", "check_out", "room_service", 
                "laundry_service", "wake_up_call", "wifi_info", "amenities_info",
                "dining_hours", "concierge_service", "housekeeping"
            ],
            "hospital": [
                "appointment_booking", "appointment_reminder", "directions", 
                "department_info", "triage_assistant", "patient_history",
                "emergency_info", "visiting_hours", "insurance_info"
            ],
            "general": [
                "greeting", "goodbye", "help", "unknown", "fallback"
            ]
        }
        
        # System prompt for intent classification
        self.system_prompt = """
        You are an AI assistant that determines user intent for hotel and hospital services.
        
        Available intents:
        Hotel Services:
        - room_booking: Booking rooms, checking availability
        - check_in: Hotel check-in process
        - check_out: Hotel check-out process
        - room_service: Food and beverage orders
        - laundry_service: Laundry and dry cleaning
        - wake_up_call: Setting wake-up calls
        - wifi_info: WiFi password and connection info
        - amenities_info: Hotel facilities and services
        - dining_hours: Restaurant and dining information
        - concierge_service: Concierge assistance
        - housekeeping: Room cleaning and maintenance
        
        Hospital Services:
        - appointment_booking: Scheduling medical appointments
        - appointment_reminder: Appointment reminders and confirmations
        - directions: Hospital navigation and directions
        - department_info: Information about hospital departments
        - triage_assistant: Basic health assessment and triage
        - patient_history: Patient medical history access
        - emergency_info: Emergency services information
        - visiting_hours: Hospital visiting hours
        - insurance_info: Insurance and billing information
        
        General:
        - greeting: Hello, hi, good morning, etc.
        - goodbye: Goodbye, bye, see you, etc.
        - help: Help requests, what can you do
        - unknown: Unclear or unrecognized intent
        - fallback: Default response when unsure
        
        Respond with a JSON object containing:
        {
            "intent": "the_determined_intent",
            "confidence": 0.95,
            "entities": {"key": "value"},
            "context": "additional_context"
        }
        """
    
    async def determine_intent(self, text: str, context: Dict = None) -> Dict[str, Any]:
        """
        Determine user intent using GPT-4
        
        Args:
            text: User input text
            context: Additional context (user_id, session_id, etc.)
            
        Returns:
            Intent classification result
        """
        try:
            self.logger.info(f"Determining intent for: {text[:100]}...")
            
            # Build the user message
            user_message = f"User input: {text}"
            if context:
                user_message += f"\nContext: {json.dumps(context)}"
            
            # Call GPT-4 for intent classification
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            # Parse the response
            response_text = response.choices[0].message.content
            intent_result = json.loads(response_text)
            
            self.logger.info(f"Intent determined: {intent_result['intent']} (confidence: {intent_result['confidence']})")
            
            return intent_result
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse intent response: {str(e)}")
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "entities": {},
                "context": "Failed to parse intent"
            }
        except Exception as e:
            self.logger.error(f"Error determining intent: {str(e)}")
            return {
                "intent": "fallback",
                "confidence": 0.0,
                "entities": {},
                "context": f"Error: {str(e)}"
            }
    
    async def get_intent_suggestions(self, text: str) -> List[str]:
        """
        Get suggested intents for ambiguous input
        
        Args:
            text: User input text
            
        Returns:
            List of suggested intents
        """
        try:
            prompt = f"""
            Given the user input: "{text}"
            
            Suggest the top 3 most likely intents from the available list:
            {json.dumps(self.intents, indent=2)}
            
            Respond with a JSON array of intent names.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that suggests intents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=100
            )
            
            suggestions = json.loads(response.choices[0].message.content)
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error getting intent suggestions: {str(e)}")
            return ["unknown"]
    
    async def validate_intent(self, intent: str) -> bool:
        """
        Validate if an intent is recognized
        
        Args:
            intent: Intent to validate
            
        Returns:
            True if valid, False otherwise
        """
        all_intents = []
        for category in self.intents.values():
            all_intents.extend(category)
        
        return intent in all_intents
    
    async def get_intent_description(self, intent: str) -> str:
        """
        Get description for a specific intent
        
        Args:
            intent: Intent name
            
        Returns:
            Intent description
        """
        intent_descriptions = {
            "room_booking": "Book hotel rooms and check availability",
            "check_in": "Hotel check-in process and procedures",
            "check_out": "Hotel check-out process and procedures",
            "room_service": "Order food and beverages to your room",
            "laundry_service": "Laundry and dry cleaning services",
            "wake_up_call": "Schedule wake-up calls",
            "wifi_info": "WiFi password and connection information",
            "amenities_info": "Hotel facilities and services information",
            "dining_hours": "Restaurant and dining hours",
            "concierge_service": "Concierge assistance and services",
            "housekeeping": "Room cleaning and maintenance requests",
            "appointment_booking": "Schedule medical appointments",
            "appointment_reminder": "Appointment reminders and confirmations",
            "directions": "Hospital navigation and directions",
            "department_info": "Information about hospital departments",
            "triage_assistant": "Basic health assessment and triage",
            "patient_history": "Access patient medical history",
            "emergency_info": "Emergency services information",
            "visiting_hours": "Hospital visiting hours",
            "insurance_info": "Insurance and billing information",
            "greeting": "Greeting and welcome messages",
            "goodbye": "Farewell and goodbye messages",
            "help": "Help and assistance requests",
            "unknown": "Unclear or unrecognized intent",
            "fallback": "Default response when unsure"
        }
        
        return intent_descriptions.get(intent, "Unknown intent") 