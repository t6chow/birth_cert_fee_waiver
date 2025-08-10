import os
import json
import requests
from typing import Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
import time
# Load environment variables
load_dotenv()

class WebhookAgent:
    def __init__(self):
        """Initialize the webhook agent with OpenAI client and webhook URL."""
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.webhook_url = os.getenv('N8N_WEBHOOK_URL', 'https://dignifi.app.n8n.cloud/webhook-test/fill_forms')
        
        # Define the form schema
        self.form_schema = {
            "adult_name": "string (name of the adult making the request)",
            "email_address": "string (email address, required)",
            "signup_type": "self/child (self if signing up themselves, child if signing up for their child)", 
            "child_name": "string (only if signup_type is 'child', otherwise null)"
        }
    
    def collect_form_data(self, user_input: str) -> Dict[str, Any]:
        """
        Use OpenAI GPT-5 to extract form data from user input.
        
        Args:
            user_input: The user's response containing form information
            
        Returns:
            Dictionary containing the extracted form data
        """
        system_prompt = f"""
        You are a helpful assistant that extracts form data from user responses.

        You need to collect the following information:
        - adult_name: The name of the adult making the request (required)
        - email_address: The email address of the adult (required)
        - signup_type: Whether they are signing up for themselves or their child (self/child)
        - child_name: The name of the child (only if signup_type is 'child', otherwise null)

        IMPORTANT INFERENCE RULES:
        1. If signup_type is not explicitly mentioned, infer based on context:
        - If the person mentions "for myself", "for me", "I'm signing up", "I need" → signup_type = 'self'
        - If the person mentions "for my child", "my kid", "my son/daughter" → signup_type = 'child'
        - If no context about who they're signing up is given, assume signup_type = 'self'


        3. If child_name is mentioned but signup_type is not explicitly 'child', set signup_type = 'child'

        4. All fields except child_name are required. Use inference to fill missing fields when possible.

        5. email_address is now required - if not provided, ask for it or set to null if truly not available.

        6. Return the data as a valid JSON object with all fields present.

        Current form schema: {json.dumps(self.form_schema, indent=2)}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-5",  # Using GPT-5
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                max_completion_tokens=500
            )
            
            # Extract the response content
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON from the response
            try:
                # Look for JSON in the response
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = content[start_idx:end_idx]
                    form_data = json.loads(json_str)
                else:
                    # If no JSON found, create a structured response
                    form_data = self._parse_structured_response(content)
                
                # Validate the form data
                validated_data = self._validate_form_data(form_data)
                return validated_data
                
            except json.JSONDecodeError:
                # Fallback to structured parsing
                form_data = self._parse_structured_response(content)
                validated_data = self._validate_form_data(form_data)
                return validated_data
                
        except Exception as e:
            print(f"Error collecting form data: {e}")
            return {}
    
    def _parse_structured_response(self, content: str) -> Dict[str, Any]:
        """Parse structured response when JSON parsing fails."""
        form_data = {}
        
        # Extract name_of_requestor
        if "name" in content.lower() or "requestor" in content.lower():
            lines = content.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in ["name", "requestor", "person"]):
                    parts = line.split(':')
                    if len(parts) > 1:
                        form_data["name_of_requestor"] = parts[1].strip()
                        break
        
        
        # Extract request_on_behalf status
        if "behalf" in content.lower():
            if "yes" in content.lower() or "y" in content.lower():
                form_data["request_on_behalf"] = "y"
            elif "no" in content.lower() or "n" in content.lower():
                form_data["request_on_behalf"] = "n"
        
        # Extract name_of_child
        if "child" in content.lower() and form_data.get("request_on_behalf") == "y":
            lines = content.split('\n')
            for line in lines:
                if "child" in line.lower():
                    parts = line.split(':')
                    if len(parts) > 1:
                        form_data["name_of_child"] = parts[1].strip()
                        break
        
        return form_data
    
    def _validate_form_data(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean the form data."""
        result = {"valid": True, "error": None}
        validated = {}
        
        # Handle both old and new field names for backwards compatibility
        # Validate adult_name (or name_of_requestor for backwards compatibility)
        adult_name = form_data.get("adult_name") or form_data.get("name_of_requestor")
        if adult_name:
            validated["adult_name"] = str(adult_name).strip()
        else:
            result["valid"] = False
            result["error"] = "Adult name is required"
            return result
        
        # Validate email_address (now required)
        if "email_address" in form_data and form_data["email_address"]:
            validated["email_address"] = str(form_data["email_address"]).strip()
        else:
            result["valid"] = False
            result["error"] = "Email address is required"
            return result
        
        
        # Validate signup_type (or infer from request_on_behalf for backwards compatibility)
        signup_type = form_data.get("signup_type")
        if not signup_type and "request_on_behalf" in form_data:
            # Convert old format to new format
            signup_type = "child" if form_data["request_on_behalf"] == "y" else "self"
        
        if signup_type in ["self", "child"]:
            validated["signup_type"] = signup_type
        else:
            result["valid"] = False
            result["error"] = "Signup type must be 'self' or 'child'"
            return result
        
        # Validate child_name (or name_of_child for backwards compatibility)
        child_name = form_data.get("child_name") or form_data.get("name_of_child")
        if validated["signup_type"] == "child":
            if child_name:
                validated["child_name"] = str(child_name).strip()
            else:
                result["valid"] = False
                result["error"] = "Child name is required when signup type is 'child'"
                return result
        else:
            validated["child_name"] = None
        
        result.update(validated)
        return result
    
    def send_webhook(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send form data to the n8n webhook.
        
        Args:
            form_data: The validated form data to send
            
        Returns:
            Dictionary containing the webhook response
        """
        try:

            time.sleep(1)
            headers = {
                'Content-Type': 'application/json'#,
                # 'User-Agent': 'WebhookAgent/1.0'
            }
            
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
    
    def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input, extract form data, and send webhook.
        
        Args:
            user_input: The user's input containing form information
            
        Returns:
            Dictionary containing the processing results
        """
        # Extract form data
        form_data = self.collect_form_data(user_input)
        
        if not form_data:
            return {
                "success": False,
                "error": "Failed to extract form data from user input"
            }
        
        # Validate the extracted data
        validation_result = self._validate_form_data(form_data)
        if not validation_result.get("valid", False):
            return {
                "success": False,
                "error": validation_result.get("error", "Invalid form data"),
                "extracted_data": form_data
            }
        
        # Use the validated data
        validated_form_data = {k: v for k, v in validation_result.items() if k not in ["valid", "error"]}
        
        # Send webhook
        webhook_result = self.send_webhook(validated_form_data)
        
        return {
            "success": webhook_result["success"],
            "form_data": validated_form_data,
            "webhook_result": webhook_result
        }
