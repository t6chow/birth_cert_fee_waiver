#!/usr/bin/env python3
"""
Test script for the Dignifi Form Webhook Agent.
"""

import json
import os
from webhook_agent import WebhookAgent

def test_agent():
    """Test the webhook agent with various scenarios."""
    
    print("🧪 Testing Dignifi Form Webhook Agent")
    print("=" * 50)
    
    # Initialize agent
    try:
        agent = WebhookAgent()
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return
    
    # Test cases
    test_cases = [
        {
            "name": "Complete information with child",
            "input": "My name is John Smith. I am not homeless. I am making this request on behalf of my child, Sarah Smith.",
            "expected": {
                "name_of_requestor": "John Smith",
                "homeless": "n",
                "request_on_behalf": "y",
                "name_of_child": "Sarah Smith"
            }
        },
        {
            "name": "Self-request, not homeless",
            "input": "I'm Jane Doe, currently not homeless, and I'm requesting this for myself.",
            "expected": {
                "name_of_requestor": "Jane Doe",
                "homeless": "n",
                "request_on_behalf": "n",
                "name_of_child": None
            }
        },
        {
            "name": "Homeless person, self-request",
            "input": "My name is Mike Johnson. I am currently homeless. I am making this request for myself.",
            "expected": {
                "name_of_requestor": "Mike Johnson",
                "homeless": "y",
                "request_on_behalf": "n",
                "name_of_child": None
            }
        },
        {
            "name": "Structured format",
            "input": "Name: Emma Wilson, Homeless: No, Request on behalf: Yes, Child's name: Tommy Wilson",
            "expected": {
                "name_of_requestor": "Emma Wilson",
                "homeless": "n",
                "request_on_behalf": "y",
                "name_of_child": "Tommy Wilson"
            }
        },
        {
            "name": "Incomplete information",
            "input": "My name is Bob. I'm not homeless.",
            "expected": {
                "name_of_requestor": "Bob",
                "homeless": "n"
                # Missing request_on_behalf and name_of_child
            }
        }
    ]
    
    # Run tests
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        print(f"Input: {test_case['input']}")
        
        try:
            result = agent.process_user_input(test_case['input'])
            
            if result["success"]:
                print("✅ Processing successful")
                
                # Check if all expected fields are present
                form_data = result["form_data"]
                expected = test_case["expected"]
                
                all_fields_present = True
                for field, expected_value in expected.items():
                    if field in form_data:
                        actual_value = form_data[field]
                        if actual_value == expected_value:
                            print(f"  ✅ {field}: {actual_value}")
                        else:
                            print(f"  ❌ {field}: expected {expected_value}, got {actual_value}")
                            all_fields_present = False
                    else:
                        print(f"  ❌ {field}: missing")
                        all_fields_present = False
                
                if all_fields_present:
                    print("  🎉 All expected fields match!")
                    passed += 1
                else:
                    print("  ⚠️ Some fields don't match expected values")
                    failed += 1
                
                # Show webhook result
                webhook_result = result["webhook_result"]
                if webhook_result["success"]:
                    print(f"  ✅ Webhook sent successfully (Status: {webhook_result.get('status_code', 'N/A')})")
                else:
                    print(f"  ❌ Webhook failed: {webhook_result.get('error', 'Unknown error')}")
                
            else:
                print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
                failed += 1
                
        except Exception as e:
            print(f"❌ Test error: {e}")
            failed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%" if (passed+failed) > 0 else "📈 No tests run")
    
    # Test webhook connection separately
    print("\n🔗 Testing webhook connection...")
    test_data = {
        "name_of_requestor": "Test User",
        "homeless": "n",
        "request_on_behalf": "n",
        "name_of_child": None
    }
    
    webhook_result = agent.send_webhook(test_data)
    if webhook_result["success"]:
        print("✅ Webhook connection successful!")
        print(f"Status Code: {webhook_result.get('status_code', 'N/A')}")
        print(f"Response: {webhook_result.get('response_text', 'N/A')}")
    else:
        print("❌ Webhook connection failed!")
        print(f"Error: {webhook_result.get('error', 'Unknown error')}")

def test_form_schema():
    """Test the form schema validation."""
    print("\n📋 Testing Form Schema")
    print("=" * 30)
    
    agent = WebhookAgent()
    print(f"Form Schema: {json.dumps(agent.form_schema, indent=2)}")

if __name__ == "__main__":
    # Check if OpenAI API key is set
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key before running tests")
        exit(1)
    
    test_form_schema()
    test_agent()
