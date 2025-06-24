import openai
import json
import structlog
import asyncio
from typing import Dict, Any, List
from app.config import Config
from app.optimization_implementations import (
    CircuitBreaker,
    retry_on_exception,
    track_metrics,
    cache_result
)

class OrchestratorAgent:
    """
    Orchestrator Agent: Determines intent using GPT-4 and routes to appropriate agents with optimizations
    """

    def __init__(self):
        self.client = openai.OpenAI(api_key=Config.openai()["api_key"])
        self.logger = structlog.get_logger(__name__)
        self.openai_circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60
        )
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

    @property
    def all_intents(self) -> List[str]:
        """Flattened list of all intents"""
        return [intent for category in self.intents.values() for intent in category]

    @track_metrics("determine_intent")
    @retry_on_exception(max_attempts=3, delay=2)
    async def determine_intent(self, text: str, context: Dict = None) -> Dict[str, Any]:
        """
        Determine user intent using GPT-4
        """
        try:
            self.logger.info("Determining intent", text_preview=text[:100])

            def sync_call():
                user_message = f"User input: {text}"
                if context:
                    user_message += f"\nContext: {json.dumps(context)}"
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.1,
                    max_tokens=200
                )
                return response

            response = await self.openai_circuit_breaker.call(lambda: asyncio.to_thread(sync_call))
            response = await response  # openai_circuit_breaker.call returns coroutine
            response_text = response.choices[0].message.content
            intent_result = json.loads(response_text)

            self.logger.info("Intent determined", intent=intent_result.get("intent"), confidence=intent_result.get("confidence"))
            return intent_result

        except json.JSONDecodeError as e:
            self.logger.error("Failed to parse intent response", error=str(e))
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "entities": {},
                "context": "Failed to parse intent"
            }
        except Exception as e:
            self.logger.error("Error determining intent", error=str(e))
            return {
                "intent": "fallback",
                "confidence": 0.0,
                "entities": {},
                "context": f"Error: {str(e)}"
            }

    @retry_on_exception(max_attempts=3, delay=2)
    async def get_intent_suggestions(self, text: str) -> List[str]:
        """
        Suggest likely intents for ambiguous input
        """
        try:
            prompt = f"""
            Given the user input: "{text}"

            Suggest the top 3 most likely intents from the list:
            {json.dumps(self.intents, indent=2)}

            Respond with a JSON array of intent names.
            """

            def sync_call():
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that suggests intents."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=100
                )
                return response

            response = await asyncio.to_thread(sync_call)
            suggestions = json.loads(response.choices[0].message.content)
            self.logger.info("Intent suggestions", suggestions=suggestions)
            return suggestions

        except Exception as e:
            self.logger.error("Error getting intent suggestions", error=str(e))
            return ["unknown"]

    async def validate_intent(self, intent: str) -> bool:
        """
        Validate if an intent is recognized
        """
        is_valid = intent in self.all_intents
        self.logger.info("Intent validation", intent=intent, is_valid=is_valid)
        return is_valid

    @cache_result(ttl=3600, key_prefix="intent_description")  # Cache 1 hour
    async def get_intent_description(self, intent: str) -> str:
        """
        Get description for a specific intent
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

        description = intent_descriptions.get(intent, "Unknown intent")
        self.logger.info("Intent description lookup", intent=intent, description=description)
        return description 