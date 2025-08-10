#!/usr/bin/env python3
"""
Command-line interface for the Dignifi Form Webhook Agent.
"""

import argparse
import json
import sys
from webhook_agent import WebhookAgent

def main():
    parser = argparse.ArgumentParser(
        description="Dignifi Form Webhook Agent - Collect form data and send to n8n webhook",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python cli.py

  # Process text input
  python cli.py --input "My name is John Smith. I am not homeless. I am making this request on behalf of my child, Sarah Smith."

  # Test webhook connection
  python cli.py --test

  # Show form schema
  python cli.py --schema
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        type=str,
        help='Text input containing form information'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test webhook connection with sample data'
    )
    
    parser.add_argument(
        '--schema',
        action='store_true',
        help='Show the form schema'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize agent
        print("🤖 Initializing Dignifi Form Webhook Agent...")
        agent = WebhookAgent()
        
        # Show schema if requested
        if args.schema:
            print("\n📋 Form Schema:")
            print(json.dumps(agent.form_schema, indent=2))
            return
        
        # Test webhook if requested
        if args.test:
            print("\n🔗 Testing webhook connection...")
            test_data = {
                "name_of_requestor": "Test User",
                "homeless": "n",
                "request_on_behalf": "n",
                "name_of_child": None
            }
            
            result = agent.send_webhook(test_data)
            if result["success"]:
                print("✅ Webhook connection successful!")
                print(f"Status Code: {result.get('status_code', 'N/A')}")
                print(f"Response: {result.get('response_text', 'N/A')}")
            else:
                print("❌ Webhook connection failed!")
                print(f"Error: {result.get('error', 'Unknown error')}")
            return
        
        # Process input if provided
        if args.input:
            print(f"\n📝 Processing input: {args.input}")
            result = agent.process_user_input(args.input)
            display_result(result, args.verbose)
            return
        
        # Interactive mode
        print("\n🎯 Interactive Mode")
        print("Enter form information or type 'quit' to exit.")
        print("Example: My name is John Smith. I am not homeless. I am making this request on behalf of my child, Sarah Smith.")
        print("-" * 80)
        
        while True:
            try:
                user_input = input("\n💬 Enter information: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not user_input:
                    print("❌ Please enter some information.")
                    continue
                
                print("🔄 Processing with GPT-5...")
                result = agent.process_user_input(user_input)
                display_result(result, args.verbose)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        print("\n💡 Make sure you have:")
        print("1. Set the OPENAI_API_KEY environment variable")
        print("2. Installed all required dependencies (pip install -r requirements.txt)")
        sys.exit(1)

def display_result(result, verbose=False):
    """Display the processing result."""
    print("\n" + "="*50)
    
    if result["success"]:
        print("✅ SUCCESS: Form data processed and webhook sent!")
        
        print("\n📋 Extracted Data:")
        form_data = result["form_data"]
        for key, value in form_data.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        
        if verbose:
            print("\n🔗 Webhook Details:")
            webhook_result = result["webhook_result"]
            print(f"  Status Code: {webhook_result.get('status_code', 'N/A')}")
            print(f"  Response: {webhook_result.get('response_text', 'N/A')}")
    
    else:
        print("❌ ERROR: Failed to process form data")
        print(f"  Error: {result.get('error', 'Unknown error')}")
        
        if "extracted_data" in result:
            print("\n📋 Partially Extracted Data:")
            for key, value in result["extracted_data"].items():
                print(f"  {key.replace('_', ' ').title()}: {value}")
    
    print("="*50)

if __name__ == "__main__":
    main()
