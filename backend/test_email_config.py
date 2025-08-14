#!/usr/bin/env python3
"""
Test email configuration script
This will test if your Gmail SMTP configuration is working correctly.
"""

import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

def test_email_config():
    """Test the email configuration"""
    print("🧪 Testing Email Configuration...")
    print("=" * 40)
    
    # Load environment variables
    load_dotenv()
    
    # Get email configuration
    mail_server = os.getenv('MAIL_SERVER')
    mail_port = int(os.getenv('MAIL_PORT', '587'))
    mail_username = os.getenv('MAIL_USERNAME')
    mail_password = os.getenv('MAIL_PASSWORD')
    mail_use_tls = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    
    print(f"📧 Server: {mail_server}")
    print(f"📧 Port: {mail_port}")
    print(f"📧 Username: {mail_username}")
    print(f"📧 TLS: {mail_use_tls}")
    print(f"📧 Password: {'*' * len(mail_password) if mail_password else 'NOT SET'}")
    
    if not all([mail_server, mail_username, mail_password]):
        print("\n❌ Missing email configuration!")
        print("Please check your .env file has all required email settings.")
        return False
    
    try:
        print(f"\n🔌 Connecting to {mail_server}:{mail_port}...")
        
        # Create SMTP connection
        server = smtplib.SMTP(mail_server, mail_port)
        server.starttls()
        
        print("✅ TLS connection established")
        
        # Login
        print(f"🔐 Logging in as {mail_username}...")
        server.login(mail_username, mail_password)
        print("✅ Login successful!")
        
        # Create test message
        test_email = mail_username  # Send to yourself
        msg = MIMEText("This is a test email from Recipe App to verify your email configuration is working correctly!")
        msg['Subject'] = "Recipe App - Email Configuration Test ✅"
        msg['From'] = mail_username
        msg['To'] = test_email
        
        # Send test email
        print(f"📤 Sending test email to {test_email}...")
        server.send_message(msg)
        print("✅ Test email sent successfully!")
        
        # Close connection
        server.quit()
        print("✅ SMTP connection closed")
        
        print(f"\n🎉 Email configuration test PASSED!")
        print(f"📧 Check your inbox at {test_email} for the test email.")
        print(f"📧 If you see the test email, your configuration is working!")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ Authentication failed: {e}")
        print("\nCommon causes:")
        print("- Wrong password (make sure you're using the App Password, not your regular password)")
        print("- 2-factor authentication not enabled")
        print("- App Password not generated correctly")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"\n❌ Connection failed: {e}")
        print("\nCommon causes:")
        print("- Wrong server/port")
        print("- Firewall blocking connection")
        print("- Network issues")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = test_email_config()
    if success:
        print("\n🚀 Your email configuration is working! You can now test user registration.")
    else:
        print("\n🔧 Please fix the configuration issues and try again.")
