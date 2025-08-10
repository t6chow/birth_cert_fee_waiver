import os
import json
import requests
from typing import Dict, Any, Optional, List
from openai import OpenAI
from dotenv import load_dotenv
import time
import uuid

# Load environment variables
load_dotenv()

class ConversationalAgent:
    def __init__(self):
        """Initialize the conversational agent with OpenAI client and webhook URL."""
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.webhook_url = os.getenv('N8N_WEBHOOK_URL', 'https://dignifi.app.n8n.cloud/webhook/fill_spreadsheet')
        
        # Define the required fields for the form
        self.required_fields = {
            "adult_name": {
                "description": "Name of the adult making the request",
                "type": "string",
                "question": "What is your full name?"
            },
            "email_address": {
                "description": "Email address of the adult",
                "type": "string",
                "question": "What is your email address?"
            },
            "signup_type": {
                "description": "Whether signing up for themselves or their child",
                "type": "choice",
                "options": ["self", "child"],
                "question": "Are you signing up for yourself or for your child?"
            },
            "child_name": {
                "description": "Name of the child (only if signup_type is 'child')",
                "type": "string",
                "conditional": {"field": "signup_type", "value": "child"},
                "question": "What is your child's full name?"
            }
        }
        
        # Conversation sessions storage (in production, use Redis or database)
        self.sessions = {}
    
    def create_session(self) -> str:
        """Create a new conversation session."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "collected_data": {},
            "conversation_history": [],
            "current_step": "greeting",
            "missing_fields": list(self.required_fields.keys())
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data."""
        return self.sessions.get(session_id)
    
    def update_session(self, session_id: str, updates: Dict):
        """Update session data."""
        if session_id in self.sessions:
            self.sessions[session_id].update(updates)
    
    def extract_information(self, user_input: str, session_data: Dict) -> Dict[str, Any]:
        """
        Extract information from user input using GPT and update session data.
        """
        collected_data = session_data.get("collected_data", {})
        missing_fields = session_data.get("missing_fields", [])
        
        system_prompt = f"""
        You are a helpful assistant extracting form information from user responses.
        
        Required fields and their current status:
        {json.dumps({field: {"description": self.required_fields[field]["description"], 
                            "collected": field in collected_data, 
                            "current_value": collected_data.get(field)} 
                    for field in self.required_fields}, indent=2)}
        
        Current missing fields: {missing_fields}
        
        Extract any available information from the user's input and return a JSON object with:
        - extracted_fields: dict of field_name -> value for any fields you can extract
        - confidence: dict of field_name -> confidence_score (0.0 to 1.0) for extracted fields
        
        Rules:
        1. Only extract information you're confident about
        2. For signup_type, look for clues like "for myself", "for my child", "my kid", etc.
           - If they say "myself", "me", "for myself", etc. -> extract "self"
           - If they say "child", "my child", "kid", etc. -> extract "child"
        3. If they mention a child's name, assume signup_type is "child"
        4. Be conservative - if unsure, don't extract
        5. Names should be proper names, not just "yes/no" responses
        6. IMPORTANT: For signup_type, only return "self" or "child", never "myself" or other variations
        
        Return valid JSON only.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                max_completion_tokens=300
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = content[start_idx:end_idx]
                    result = json.loads(json_str)
                    return result
            except json.JSONDecodeError:
                pass
            
            return {"extracted_fields": {}, "confidence": {}}
            
        except Exception as e:
            print(f"Error extracting information: {e}")
            return {"extracted_fields": {}, "confidence": {}}
    
    def generate_response(self, session_data: Dict, extracted_info: Dict) -> Dict[str, Any]:
        """
        Generate an appropriate response based on session state and extracted information.
        """
        collected_data = session_data.get("collected_data", {})
        missing_fields = session_data.get("missing_fields", [])
        current_step = session_data.get("current_step", "greeting")
        
        # Update collected data with high-confidence extractions
        extracted_fields = extracted_info.get("extracted_fields", {})
        confidence_scores = extracted_info.get("confidence", {})
        
        new_data = {}
        for field, value in extracted_fields.items():
            if field in self.required_fields and confidence_scores.get(field, 0) > 0.7:
                new_data[field] = value
                if field in missing_fields:
                    missing_fields.remove(field)
        
        collected_data.update(new_data)
        
        # Filter missing fields based on conditional requirements
        actual_missing = []
        for field in missing_fields:
            field_info = self.required_fields[field]
            
            # Check if field is conditionally required
            if "conditional" in field_info:
                condition = field_info["conditional"]
                if collected_data.get(condition["field"]) == condition["value"]:
                    actual_missing.append(field)
                # If condition not met, remove from missing fields
                elif condition["field"] in collected_data:
                    continue
                else:
                    # Condition field not collected yet, keep in missing
                    actual_missing.append(field)
            else:
                actual_missing.append(field)
        
        missing_fields = actual_missing
        
        # Check if we have all required information
        if not missing_fields:
            # All information collected, proceed to webhook
            webhook_result = self.send_webhook(collected_data)
            
            return {
                "type": "completion",
                "message": "Perfect! I have all the information needed. Let me submit your request now.",
                "data_collected": collected_data,
                "webhook_result": webhook_result,
                "session_complete": True
            }
        
        # Generate next question
        next_field = missing_fields[0]
        field_info = self.required_fields[next_field]
        
        # Acknowledge any new information we collected
        acknowledgment = ""
        if new_data:
            ack_parts = []
            for field, value in new_data.items():
                field_desc = self.required_fields[field]["description"]
                ack_parts.append(f"{field_desc}: {value}")
            acknowledgment = f"Great! I've noted: {', '.join(ack_parts)}. "
        
        # Generate question for next field
        question = field_info["question"]
        if field_info.get("type") == "choice":
            options_text = " or ".join(field_info["options"])
            question += f" (Please say {options_text})"
        
        return {
            "type": "question",
            "message": acknowledgment + question,
            "asking_for": next_field,
            "data_collected": collected_data,
            "missing_fields": missing_fields,
            "session_complete": False
        }
    
    def send_webhook(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send form data to the webhook."""
        try:
            time.sleep(1)
            headers = {'Content-Type': 'application/json'}
            
            response = requests.post(
                self.webhook_url,
                json=form_data,
                headers=headers,
                timeout=30
            )
            
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response_text": response.text,
                "sent_data": form_data
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "sent_data": form_data
            }
    
    def start_conversation(self) -> Dict[str, Any]:
        """Start a new conversation."""
        session_id = self.create_session()
        
        return {
            "session_id": session_id,
            "type": "greeting",
            "message": "Hi! I'm here to help you with your birth certificate fee waiver application. I'll need to collect some information from you. What's your full name?",
            "asking_for": "adult_name",
            "session_complete": False
        }
    
    def continue_conversation(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """Continue an existing conversation."""
        session_data = self.get_session(session_id)
        
        if not session_data:
            return {
                "type": "error",
                "message": "Session not found. Please start a new conversation.",
                "session_complete": True
            }
        
        # Add user input to conversation history
        session_data["conversation_history"].append({
            "type": "user",
            "message": user_input,
            "timestamp": time.time()
        })
        
        # Extract information from user input
        extracted_info = self.extract_information(user_input, session_data)
        
        # Generate response
        response = self.generate_response(session_data, extracted_info)
        
        # Update session
        session_data["collected_data"] = response.get("data_collected", {})
        session_data["missing_fields"] = response.get("missing_fields", [])
        
        # Add agent response to history
        session_data["conversation_history"].append({
            "type": "agent",
            "message": response["message"],
            "timestamp": time.time()
        })
        
        self.update_session(session_id, session_data)
        
        # Add session info to response
        response["session_id"] = session_id
        
        return response