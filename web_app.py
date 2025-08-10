from flask import Flask, render_template, request, jsonify
import os
from webhook_agent import WebhookAgent
from conversational_agent import ConversationalAgent
import json

app = Flask(__name__)

# Initialize the agents
webhook_agent = None
conversational_agent = None

def get_agent():
    """Get or create the webhook agent instance."""
    global webhook_agent
    if webhook_agent is None:
        if not os.getenv('OPENAI_API_KEY'):
            return None
        try:
            webhook_agent = WebhookAgent()
        except Exception as e:
            print(f"Error initializing webhook agent: {e}")
            return None
    return webhook_agent

def get_conversational_agent():
    """Get or create the conversational agent instance."""
    global conversational_agent
    if conversational_agent is None:
        if not os.getenv('OPENAI_API_KEY'):
            return None
        try:
            conversational_agent = ConversationalAgent()
        except Exception as e:
            print(f"Error initializing conversational agent: {e}")
            return None
    return conversational_agent

@app.route('/')
def index():
    """Serve the main page."""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """Check if the API is configured properly."""
    return jsonify({
        'api_key_configured': bool(os.getenv('OPENAI_API_KEY')),
        'webhook_url': os.getenv('N8N_WEBHOOK_URL', 'https://dignifi.app.n8n.cloud/webhook/fill_spreadsheet')
    })

@app.route('/api/test-webhook', methods=['POST'])
def test_webhook():
    """Test the webhook connection."""
    agent = get_agent()
    if not agent:
        return jsonify({
            'success': False,
            'error': 'Agent not initialized - check API key configuration'
        })
    
    # Test data
    test_data = {
        "adult_name": "Test User",
        "email_address": "test@example.com",
        "signup_type": "self",
        "child_name": None
    }
    
    try:
        result = agent.send_webhook(test_data)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/process', methods=['POST'])
def process_form():
    """Process form data using the webhook agent."""
    agent = get_agent()
    if not agent:
        return jsonify({
            'success': False,
            'error': 'Agent not initialized - check API key configuration'
        })
    
    try:
        data = request.get_json()
        
        if data.get('input_type') == 'natural':
            # Process natural language input
            user_input = data.get('input', '').strip()
            if not user_input:
                return jsonify({
                    'success': False,
                    'error': 'No input provided'
                })
            
            result = agent.process_user_input(user_input)
            return jsonify(result)
            
        elif data.get('input_type') == 'structured':
            # Process structured form data
            form_data = {
                'adult_name': data.get('adult_name', '').strip(),
                'email_address': data.get('email_address', '').strip() if data.get('email_address') else None,
                'signup_type': data.get('signup_type', ''),
                'child_name': data.get('child_name', '').strip() if data.get('child_name') else None
            }
            
            # Validate required fields
            if not form_data['adult_name']:
                return jsonify({
                    'success': False,
                    'error': 'Adult name is required'
                })
            
            if not form_data['email_address']:
                return jsonify({
                    'success': False,
                    'error': 'Email address is required'
                })
            
            
            if form_data['signup_type'] not in ['self', 'child']:
                return jsonify({
                    'success': False,
                    'error': 'Signup type must be self or child'
                })
            
            if form_data['signup_type'] == 'child' and not form_data['child_name']:
                return jsonify({
                    'success': False,
                    'error': 'Child name is required when signing up for a child'
                })
            
            # Validate and send webhook
            validation_result = agent._validate_form_data(form_data)
            if not validation_result['valid']:
                return jsonify({
                    'success': False,
                    'error': validation_result['error'],
                    'extracted_data': form_data
                })
            
            webhook_result = agent.send_webhook(form_data)
            
            return jsonify({
                'success': webhook_result['success'],
                'form_data': form_data,
                'webhook_result': webhook_result,
                'error': webhook_result.get('error') if not webhook_result['success'] else None
            })
            
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid input type'
            })
            
    except Exception as e:
        print(f"Error processing form: {e}")
        return jsonify({
            'success': False,
            'error': f'Processing error: {str(e)}'
        })

@app.route('/api/chat/start', methods=['POST'])
def start_chat():
    """Start a new conversation."""
    agent = get_conversational_agent()
    if not agent:
        return jsonify({
            'success': False,
            'error': 'Conversational agent not initialized - check API key configuration'
        })
    
    try:
        result = agent.start_conversation()
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/chat/message', methods=['POST'])
def send_chat_message():
    """Send a message in an existing conversation."""
    agent = get_conversational_agent()
    if not agent:
        return jsonify({
            'success': False,
            'error': 'Conversational agent not initialized - check API key configuration'
        })
    
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        message = data.get('message', '').strip()
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'Session ID is required'
            })
        
        if not message:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            })
        
        result = agent.continue_conversation(session_id, message)
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        print(f"Error in chat message: {e}")
        return jsonify({
            'success': False,
            'error': f'Chat error: {str(e)}'
        })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Check if environment is set up
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  Warning: OPENAI_API_KEY environment variable not set")
        print("   Please create a .env file with your API key")
    
    # Check if templates and static directories exist
    if not os.path.exists('templates'):
        print("❌ Error: templates directory not found")
        exit(1)
    
    if not os.path.exists('static'):
        print("❌ Error: static directory not found")
        exit(1)
    
    print("🚀 Starting Birth Certificate Fee Waiver Web App")
    print("📱 Open your browser to: http://localhost:5001")
    
    app.run(debug=True, host='0.0.0.0', port=5001)