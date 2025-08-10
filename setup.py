#!/usr/bin/env python3
"""
Setup script for the Dignifi Form Webhook Agent.
"""

import os
import sys
import subprocess
import shutil

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_dependencies():
    """Install required dependencies."""
    print("\n📦 Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_env_file():
    """Create .env file if it doesn't exist."""
    env_file = ".env"
    
    if os.path.exists(env_file):
        print("✅ .env file already exists")
        return True
    
    print("\n🔧 Creating .env file...")
    
    env_content = """# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# N8N Webhook Configuration (optional - defaults to the provided URL)
N8N_WEBHOOK_URL=https://dignifi.app.n8n.cloud/webhook-test/fill_forms
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully")
        print("⚠️  Please edit .env file and add your OpenAI API key")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def check_openai_key():
    """Check if OpenAI API key is set."""
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key and api_key != 'your_openai_api_key_here':
        print("✅ OpenAI API key is configured")
        return True
    else:
        print("⚠️  OpenAI API key not configured")
        print("Please set your OpenAI API key in the .env file")
        return False

def test_imports():
    """Test if all required modules can be imported."""
    print("\n🧪 Testing imports...")
    
    required_modules = [
        'openai',
        'requests', 
        'streamlit',
        'dotenv'
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Failed to import: {', '.join(failed_imports)}")
        return False
    
    print("✅ All imports successful")
    return True

def main():
    """Main setup function."""
    print("🚀 Dignifi Form Webhook Agent Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Test imports
    if not test_imports():
        print("\n💡 Try running: pip install -r requirements.txt")
        sys.exit(1)
    
    # Create .env file
    create_env_file()
    
    # Check OpenAI key
    check_openai_key()
    
    print("\n🎉 Setup completed!")
    print("\n📋 Next steps:")
    print("1. Edit .env file and add your OpenAI API key")
    print("2. Run the web interface: streamlit run app.py")
    print("3. Or run the CLI: python cli.py")
    print("4. Test the agent: python test_agent.py")
    
    print("\n📚 For more information, see README.md")

if __name__ == "__main__":
    main()
