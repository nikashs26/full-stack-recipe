#!/usr/bin/env python3
"""
Setup script for environment variables.
Run this script to configure your OpenAI API key and other environment variables.
"""

import os
import sys

def create_env_file():
    """Create a .env file with required environment variables."""
    
    print("🤖 Setting up your AI Meal Planner Environment Variables")
    print("=" * 60)
    
    # Check if .env already exists
    if os.path.exists('.env'):
        overwrite = input("⚠️  .env file already exists. Overwrite? (y/N): ").lower()
        if overwrite != 'y':
            print("❌ Setup cancelled.")
            return
    
    # Choose LLM option
    print("\n🤖 Choose Your Free LLM Option:")
    print("1. Ollama (Local, completely free) - Recommended")
    print("2. Hugging Face (Free tier, cloud-based)")
    print("3. Rule-based fallback (No AI, but always works)")
    
    choice = input("Enter your choice (1-3) [1]: ").strip() or "1"
    
    hf_key = ""
    if choice == "2":
        print("\n🤗 Hugging Face API Key (Optional)")
        print("Get your free API key from: https://huggingface.co/settings/tokens")
        hf_key = input("Enter your Hugging Face API key (optional): ").strip()
    
    # Optional: Other configuration
    print("\n⚙️  Optional Configuration")
    flask_env = input("Flask environment (development/production) [development]: ").strip() or "development"
    
    # Generate a simple secret key
    import secrets
    secret_key = secrets.token_urlsafe(32)
    jwt_secret = secrets.token_urlsafe(32)
    
    # Create .env content
    env_content = f"""# Free LLM Configuration
OLLAMA_URL=http://localhost:11434
HUGGING_FACE_API_KEY={hf_key}

# Flask Configuration
FLASK_ENV={flask_env}
SECRET_KEY={secret_key}

# JWT Configuration
JWT_SECRET_KEY={jwt_secret}

# Supabase Configuration (optional - add if you use Supabase)
# SUPABASE_URL=your_supabase_url_here
# SUPABASE_KEY=your_supabase_key_here
"""
    
    # Write to .env file
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("\n✅ Environment variables configured successfully!")
        print("📁 Created .env file with your configuration")
        
        if choice == "1":
            print("\n🦙 Ollama Setup Instructions:")
            print("1. Install Ollama: https://ollama.ai/download")
            print("2. Run: ollama pull llama3.2:3b")
            print("3. Start Ollama: ollama serve")
        elif choice == "2":
            print("\n🤗 Hugging Face Setup Complete!")
            print("Your agent will use Hugging Face's free inference API")
        
        print("\n🚀 You can now run your Flask app with:")
        print("   python app.py")
        print("\n💡 Remember to:")
        print("   - Keep your .env file secure and never commit it to version control")
        print("   - Set up your user preferences in the app before generating meal plans")
        print("   - The agent will automatically fallback to rule-based planning if LLMs fail")
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_env_file() 