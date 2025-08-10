import streamlit as st
import json
from webhook_agent import WebhookAgent
import os

# Page configuration
st.set_page_config(
    page_title="Dignifi Form Webhook Agent",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

def initialize_agent():
    """Initialize the webhook agent."""
    try:
        if not os.getenv('OPENAI_API_KEY'):
            st.error("❌ OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
            return None
        
        agent = WebhookAgent()
        return agent
    except Exception as e:
        st.error(f"❌ Error initializing agent: {e}")
        return None

def main():
    st.title("🤖 Dignifi Form Webhook Agent")
    st.markdown("This agent uses OpenAI GPT-5 to collect form data and send it to your n8n workflow.")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Check if agent is initialized
        if st.session_state.agent is None:
            st.session_state.agent = initialize_agent()
        
        if st.session_state.agent:
            st.success("✅ Agent initialized successfully")
            
            # Display webhook URL
            webhook_url = st.session_state.agent.webhook_url
            st.info(f"**Webhook URL:** {webhook_url}")
            
            # Test connection button
            if st.button("🔗 Test Webhook Connection"):
                with st.spinner("Testing connection..."):
                    test_data = {
                        "name_of_requestor": "Test User",
                        "homeless": "n",
                        "request_on_behalf": "n",
                        "name_of_child": None
                    }
                    result = st.session_state.agent.send_webhook(test_data)
                    if result["success"]:
                        st.success("✅ Webhook connection successful!")
                    else:
                        st.error(f"❌ Webhook connection failed: {result.get('error', 'Unknown error')}")
        else:
            st.error("❌ Agent not initialized")
            if st.button("🔄 Retry Initialization"):
                st.session_state.agent = initialize_agent()
                st.rerun()
    
    # Main content area
    if st.session_state.agent:
        st.markdown("---")
        
        # Form information
        st.subheader("📋 Required Information")
        st.markdown("""
        The agent will collect the following information:
        - **Name of Requestor**: The person making the request
        - **Homeless Status**: Whether the person is homeless (y/n)
        - **Request on Behalf**: Whether the request is being made on behalf of someone else (y/n)
        - **Name of Child**: The child's name (only if request_on_behalf is 'y')
        """)
        
        # Input area
        st.subheader("💬 Enter Information")
        
        # Option 1: Free text input
        st.markdown("**Option 1: Free Text Input**")
        user_input = st.text_area(
            "Describe the situation or provide the required information:",
            height=150,
            placeholder="Example: My name is John Smith. I am not homeless. I am making this request on behalf of my child, Sarah Smith."
        )
        
        # Option 2: Structured form
        st.markdown("**Option 2: Structured Form**")
        with st.expander("📝 Fill out structured form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name_of_requestor = st.text_input("Name of Requestor:")
                homeless = st.selectbox("Homeless Status:", ["", "y", "n"], format_func=lambda x: {"": "Select...", "y": "Yes", "n": "No"}[x])
            
            with col2:
                request_on_behalf = st.selectbox("Request on Behalf:", ["", "y", "n"], format_func=lambda x: {"": "Select...", "y": "Yes", "n": "No"}[x])
                name_of_child = st.text_input("Name of Child (if applicable):")
            
            # Create structured input
            if st.button("📤 Submit Structured Form"):
                if name_of_requestor and homeless and request_on_behalf:
                    structured_input = f"""
                    Name of requestor: {name_of_requestor}
                    Homeless: {homeless}
                    Request on behalf: {request_on_behalf}
                    """
                    if request_on_behalf == "y" and name_of_child:
                        structured_input += f"Name of child: {name_of_child}"
                    
                    user_input = structured_input
        
        # Process button
        if st.button("🚀 Process and Send Webhook", disabled=not user_input.strip()):
            if user_input.strip():
                with st.spinner("Processing with GPT-5..."):
                    result = st.session_state.agent.process_user_input(user_input)
                
                # Display results
                st.subheader("📊 Results")
                
                if result["success"]:
                    st.success("✅ Form data processed and webhook sent successfully!")
                    
                    # Display extracted data
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**📋 Extracted Data:**")
                        form_data = result["form_data"]
                        for key, value in form_data.items():
                            st.write(f"**{key.replace('_', ' ').title()}:** {value}")
                    
                    with col2:
                        st.markdown("**🔗 Webhook Response:**")
                        webhook_result = result["webhook_result"]
                        st.write(f"**Status Code:** {webhook_result.get('status_code', 'N/A')}")
                        st.write(f"**Response:** {webhook_result.get('response_text', 'N/A')}")
                    
                    # Add to conversation history
                    st.session_state.conversation_history.append({
                        "input": user_input,
                        "result": result,
                        "timestamp": "Now"
                    })
                    
                else:
                    st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
                    
                    if "extracted_data" in result:
                        st.markdown("**📋 Partially Extracted Data:**")
                        for key, value in result["extracted_data"].items():
                            st.write(f"**{key.replace('_', ' ').title()}:** {value}")
        
        # Conversation history
        if st.session_state.conversation_history:
            st.markdown("---")
            st.subheader("📚 Conversation History")
            
            for i, entry in enumerate(reversed(st.session_state.conversation_history)):
                with st.expander(f"Entry {len(st.session_state.conversation_history) - i}"):
                    st.markdown(f"**Input:** {entry['input']}")
                    st.markdown(f"**Success:** {entry['result']['success']}")
                    if entry['result']['success']:
                        st.markdown("**Form Data:**")
                        st.json(entry['result']['form_data'])
                    else:
                        st.markdown(f"**Error:** {entry['result'].get('error', 'Unknown error')}")
        
        # Clear history button
        if st.session_state.conversation_history:
            if st.button("🗑️ Clear History"):
                st.session_state.conversation_history = []
                st.rerun()
    
    else:
        st.error("❌ Please check your configuration and try again.")
        st.markdown("""
        ### Setup Instructions:
        1. Create a `.env` file in the project root
        2. Add your OpenAI API key: `OPENAI_API_KEY=your_key_here`
        3. Optionally set the webhook URL: `N8N_WEBHOOK_URL=your_webhook_url`
        4. Restart the application
        """)

if __name__ == "__main__":
    main()
