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
            "name_of_requestor": "string",
            "homeless": "y/n",
            "request_on_behalf": "y/n", 
            "name_of_child": "string (only if request_on_behalf is 'y', otherwise null)"
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
        - name_of_requestor: The name of the person making the request
        - homeless: Whether the person is homeless (y/n)
        - request_on_behalf: Whether the request is being made on behalf of someone else (y/n)
        - name_of_child: The name of the child (only if request_on_behalf is 'y', otherwise null)

        IMPORTANT INFERENCE RULES:
        1. If request_on_behalf is not explicitly mentioned, infer based on context:
        - If the person mentions "for myself", "for me", "I'm requesting", or similar → request_on_behalf = 'n'
        - If the person mentions "for my child", "on behalf of", "for someone else" → request_on_behalf = 'y'
        - If no context about behalf is given, assume request_on_behalf = 'n' (self-request)

        2. If homeless status is not explicitly mentioned, infer based on context:
        - If they mention being "homeless", "living on the street", etc. → homeless = 'y'
        - If they mention having a home, address, or no mention of homelessness → homeless = 'n'

        3. If name_of_child is mentioned but request_on_behalf is not explicitly 'y', set request_on_behalf = 'y'

        4. All fields are required. Use inference to fill missing fields when possible.

        5. Return the data as a valid JSON object with all fields present.

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
        
        # Extract homeless status
        if "homeless" in content.lower():
            if "yes" in content.lower() or "y" in content.lower():
                form_data["homeless"] = "y"
            elif "no" in content.lower() or "n" in content.lower():
                form_data["homeless"] = "n"
        
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
        validated = {}
        
        # Validate name_of_requestor
        if "name_of_requestor" in form_data and form_data["name_of_requestor"]:
            validated["name_of_requestor"] = str(form_data["name_of_requestor"]).strip()
        
        # Validate homeless
        if "homeless" in form_data:
            homeless_val = str(form_data["homeless"]).lower().strip()
            if homeless_val in ["y", "yes", "n", "no"]:
                validated["homeless"] = "y" if homeless_val in ["y", "yes"] else "n"
        
        # Validate request_on_behalf
        if "request_on_behalf" in form_data:
            behalf_val = str(form_data["request_on_behalf"]).lower().strip()
            if behalf_val in ["y", "yes", "n", "no"]:
                validated["request_on_behalf"] = "y" if behalf_val in ["y", "yes"] else "n"
        
        # Validate name_of_child
        if "name_of_child" in form_data and form_data["name_of_child"]:
            if validated.get("request_on_behalf") == "y":
                validated["name_of_child"] = str(form_data["name_of_child"]).strip()
            else:
                validated["name_of_child"] = None
        elif validated.get("request_on_behalf") == "n":
            validated["name_of_child"] = None
        
        return validated
    
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
        
        # Check if all required fields are present
        required_fields = ["name_of_requestor", "homeless", "request_on_behalf"]
        missing_fields = [field for field in required_fields if field not in form_data]
        
        if missing_fields:
            return {
                "success": False,
                "error": f"Missing required fields: {', '.join(missing_fields)}",
                "extracted_data": form_data
            }
        
        # Send webhook
        webhook_result = self.send_webhook(form_data)
        
        return {
            "success": webhook_result["success"],
            "form_data": form_data,
            "webhook_result": webhook_result
        }
