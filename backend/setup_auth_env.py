#!/usr/bin/env python3
"""
Setup script for authentication environment variables
Run this script to configure your .env file for the new authentication system
"""

import os
import secrets
import getpass


def generate_secret_key():
    """Generate a secure secret key"""
    return secrets.token_urlsafe(32)


def setup_env_file():
    """Setup .env file with authentication configuration"""
    
    print("🔐 Setting up authentication environment variables")
    print("=" * 50)
    
    env_path = ".env"
    env_content = []
    
    # Read existing .env if it exists
    existing_env = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    existing_env[key] = value
    
    # Flask Configuration
    print("\n📝 Flask Configuration")
    
    if 'SECRET_KEY' not in existing_env:
        secret_key = generate_secret_key()
        env_content.append(f"SECRET_KEY={secret_key}")
        print(f"✓ Generated SECRET_KEY")
    else:
        env_content.append(f"SECRET_KEY={existing_env['SECRET_KEY']}")
        print(f"✓ Using existing SECRET_KEY")
    
    if 'JWT_SECRET_KEY' not in existing_env:
        jwt_secret = generate_secret_key()
        env_content.append(f"JWT_SECRET_KEY={jwt_secret}")
        print(f"✓ Generated JWT_SECRET_KEY")
    else:
        env_content.append(f"JWT_SECRET_KEY={existing_env['JWT_SECRET_KEY']}")
        print(f"✓ Using existing JWT_SECRET_KEY")
    
    # Frontend URL
    frontend_url = existing_env.get('FRONTEND_URL', 'http://localhost:8080')
    env_content.append(f"FRONTEND_URL={frontend_url}")
    print(f"✓ Frontend URL: {frontend_url}")
    
    # Email Configuration
    print("\n📧 Email Configuration (Optional)")
    print("Leave empty to use development mode (verification URLs printed to console)")
    
    use_email = input("Do you want to configure email sending? (y/n): ").lower().strip() == 'y'
    
    if use_email:
        print("\nFor Gmail, you'll need an App Password:")
        print("1. Go to https://myaccount.google.com/security")
        print("2. Enable 2-factor authentication")
        print("3. Generate an App Password for 'Mail'")
        print("4. Use your email and the app password below")
        
        mail_username = input("Email address: ").strip()
        mail_password = getpass.getpass("Email password/app password: ").strip()
        
        env_content.extend([
            f"MAIL_SERVER=smtp.gmail.com",
            f"MAIL_PORT=587",
            f"MAIL_USE_TLS=True",
            f"MAIL_USE_SSL=False",
            f"MAIL_USERNAME={mail_username}",
            f"MAIL_PASSWORD={mail_password}",
            f"MAIL_DEFAULT_SENDER={mail_username}"
        ])
        print("✓ Email configuration added")
    else:
        env_content.extend([
            "# Email Configuration (optional - leave empty for development mode)",
            "# MAIL_SERVER=smtp.gmail.com",
            "# MAIL_PORT=587",
            "# MAIL_USE_TLS=True",
            "# MAIL_USE_SSL=False",
            "# MAIL_USERNAME=your-email@gmail.com",
            "# MAIL_PASSWORD=your-app-password",
            "# MAIL_DEFAULT_SENDER=your-email@gmail.com"
        ])
        print("✓ Email configuration skipped (development mode)")
    
    # AI Configuration
    print("\n🤖 AI Configuration")
    
    openai_key = existing_env.get('OPENAI_API_KEY', '')
    if not openai_key:
        openai_key = input("OpenAI API Key (optional): ").strip()
    
    ollama_url = existing_env.get('OLLAMA_URL', 'http://localhost:11434')
    hf_key = existing_env.get('HUGGING_FACE_API_KEY', '')
    
    env_content.extend([
        "",
        "# AI Configuration",
        f"OPENAI_API_KEY={openai_key}",
        f"OLLAMA_URL={ollama_url}",
        f"HUGGING_FACE_API_KEY={hf_key}"
    ])
    
    # Database Configuration
    print("\n🗄️ Database Configuration")
    
    mongo_uri = existing_env.get('MONGO_URI', 'mongodb://localhost:27017/recipe_app')
    
    env_content.extend([
        "",
        "# Database Configuration",
        f"MONGO_URI={mongo_uri}",
        "MONGO_CONNECT_TIMEOUT_MS=5000",
        "MONGO_RETRY_COUNT=3"
    ])
    
    # Write .env file
    with open(env_path, 'w') as f:
        f.write('\n'.join(env_content))
    
    print(f"\n✅ Configuration saved to {env_path}")
    
    # Show next steps
    print("\n🚀 Next Steps:")
    print("1. Start the backend server: python app.py")
    print("2. The authentication system uses ChromaDB for user storage")
    print("3. Email verification links will be printed to console in development mode")
    print("4. Protected routes: /api/preferences, /api/meal-plan/generate, /api/shopping-list/generate")
    print("\n📋 Test the system:")
    print("- Sign up: POST /api/auth/register")
    print("- Verify email: GET /api/auth/verify-email/<token>")
    print("- Sign in: POST /api/auth/login")
    print("- Access protected routes with Authorization: Bearer <token>")


def main():
    """Main setup function"""
    try:
        setup_env_file()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled")
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")


if __name__ == "__main__":
    main() 