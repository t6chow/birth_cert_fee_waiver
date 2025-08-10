import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

webhook_url = os.getenv('N8N_WEBHOOK_URL', 'https://dignifi.app.n8n.cloud/webhook/fill_spreadsheet')

print(f"Testing webhook URL: {webhook_url}")

test_data = {
    "name_of_requestor": "Test User",
    "homeless": "n",
    "request_on_behalf": "n",
    "name_of_child": None
}

print(f"Sending data: {json.dumps(test_data, indent=2)}")

try:
    # Test 1: With User-Agent (like the agent)
    print("\n--- Test 1: With User-Agent ---")
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'WebhookAgent/1.0'
    }
    
    response = requests.post(
        webhook_url,
        json=test_data,
        headers=headers,
        timeout=30
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
except Exception as e:
    print(f"Error with User-Agent: {type(e).__name__}: {e}")

try:
    # Test 2: Without User-Agent (like curl)
    print("\n--- Test 2: Without User-Agent ---")
    headers = {
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        webhook_url,
        json=test_data,
        headers=headers,
        timeout=30
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
except Exception as e:
    print(f"Error without User-Agent: {type(e).__name__}: {e}")
