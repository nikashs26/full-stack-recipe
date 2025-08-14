#!/usr/bin/env python3
"""
Email Setup Script for Recipe App
This script helps you configure email settings to send verification emails to users.
"""

import os
import getpass
from pathlib import Path

def setup_email_config():
    """Setup email configuration for sending verification emails"""
    print("📧 Email Configuration Setup for Recipe App")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ No .env file found. Please run setup_auth_env.py first.")
        return
    
    print("\nThis will configure your email service to send verification emails to users.")
    print("For Gmail, you'll need an App Password (not your regular password).")
    print("\nTo get a Gmail App Password:")
    print("1. Go to https://myaccount.google.com/security")
    print("2. Enable 2-factor authentication if not already enabled")
    print("3. Generate an App Password for 'Mail'")
    print("4. Use your email and the app password below")
    
    use_email = input("\nDo you want to configure email sending? (y/n): ").lower().strip() == 'y'
    
    if not use_email:
        print("✓ Email configuration skipped. Users will see verification URLs in console.")
        return
    
    # Read existing .env file
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    # Email configuration
    mail_username = input("\nEmail address: ").strip()
    mail_password = getpass.getpass("Email password/app password: ").strip()
    
    # Check if email config already exists
    if 'MAIL_USERNAME' in env_content:
        print("⚠️  Email configuration already exists. Updating...")
        # Remove old email config
        lines = env_content.split('\n')
        new_lines = []
        skip_next = False
        for line in lines:
            if any(keyword in line for keyword in ['MAIL_SERVER', 'MAIL_PORT', 'MAIL_USE_TLS', 'MAIL_USE_SSL', 'MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_DEFAULT_SENDER']):
                continue
            new_lines.append(line)
        env_content = '\n'.join(new_lines)
    
    # Add new email configuration
    email_config = f"""
# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME={mail_username}
MAIL_PASSWORD={mail_password}
MAIL_DEFAULT_SENDER={mail_username}
FRONTEND_URL=http://localhost:8081
"""
    
    # Add to .env file
    with open(env_file, 'a') as f:
        f.write(email_config)
    
    print("\n✅ Email configuration added to .env file!")
    print(f"📧 Server: smtp.gmail.com")
    print(f"📧 Port: 587")
    print(f"📧 Username: {mail_username}")
    print(f"📧 TLS: Enabled")
    
    # Test the configuration
    test_config = input("\nWould you like to test the email configuration? (y/n): ").lower().strip() == 'y'
    if test_config:
        test_email_config(mail_username, mail_password)

def test_email_config(username, password):
    """Test the email configuration"""
    print("\n🧪 Testing email configuration...")
    
    try:
        # Test SMTP connection
        import smtplib
        from email.mime.text import MIMEText
        
        # Create test message
        msg = MIMEText("This is a test email from Recipe App to verify your email configuration.")
        msg['Subject'] = "Recipe App - Email Configuration Test"
        msg['From'] = username
        msg['To'] = username
        
        # Connect to SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(username, password)
        
        # Send test email
        server.send_message(msg)
        server.quit()
        
        print("✅ Email configuration test successful!")
        print(f"📧 Test email sent to {username}")
        print("Check your inbox for the test email.")
        
    except Exception as e:
        print(f"❌ Email configuration test failed: {e}")
        print("\nCommon issues:")
        print("- Make sure you're using an App Password, not your regular password")
        print("- Ensure 2-factor authentication is enabled on your Google account")
        print("- Check that the email and password are correct")

if __name__ == "__main__":
    setup_email_config()
