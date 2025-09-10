import os
from flask import Flask
from typing import Dict, Any

# Try to import flask_mail, fallback to mock if not available
try:
    from flask_mail import Mail, Message
    FLASK_MAIL_AVAILABLE = True
except ImportError:
    FLASK_MAIL_AVAILABLE = False
    print("Warning: flask_mail not available, email functionality will be disabled")


class EmailService:
    """
    Email service for sending verification and notification emails
    Uses Flask-Mail with SMTP configuration
    """
    
    def __init__(self, app: Flask = None):
        self.mail = None
        self.app = app
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize email service with Flask app"""
        if not FLASK_MAIL_AVAILABLE:
            print("Warning: Flask-Mail not available, email service disabled")
            return
            
        # Email configuration
        app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
        app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', '587'))
        app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
        app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
        app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', '')
        app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', '')
        app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', app.config.get('MAIL_USERNAME', ''))
        
        self.mail = Mail(app)
        self.app = app
    
    def send_verification_email(self, email: str, verification_token: str, full_name: str = "") -> Dict[str, Any]:
        """Send email verification email"""
        try:
            if not FLASK_MAIL_AVAILABLE or not self.mail:
                # Email service not configured - return success with development info
                frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:8081')
                verification_url = f"{frontend_url}/verify-email?token={verification_token}"
                
                return {
                    "success": True,
                    "message": "Email service not configured. User registered successfully.",
                    "verification_url": verification_url,
                    "dev_mode": True
                }
            
            # Create verification URL
            frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:8081')
            verification_url = f"{frontend_url}/verify-email?token={verification_token}"
            
            # Create email message
            subject = "Verify Your Email - Recipe App"
            recipient_name = full_name if full_name else email.split('@')[0]
            
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Verify Your Email</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background-color: #ffffff; padding: 30px; border: 1px solid #e9ecef; }}
                    .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 0 0 8px 8px; font-size: 12px; color: #6c757d; }}
                    .button {{ display: inline-block; padding: 12px 24px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px; font-weight: bold; }}
                    .button:hover {{ background-color: #0056b3; }}
                    .verification-code {{ font-family: monospace; font-size: 16px; background-color: #f8f9fa; padding: 10px; border-radius: 4px; border: 1px solid #dee2e6; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🍳 Recipe App</h1>
                        <h2>Email Verification</h2>
                    </div>
                    <div class="content">
                        <p>Hi {recipient_name},</p>
                        <p>Thank you for signing up for our Recipe App! To complete your registration and start creating personalized meal plans, please verify your email address.</p>
                        
                        <p style="text-align: center; margin: 30px 0;">
                            <a href="{verification_url}" class="button">Verify Email Address</a>
                        </p>
                        
                        <p>If the button doesn't work, you can also copy and paste this link into your browser:</p>
                        <p class="verification-code">{verification_url}</p>
                        
                        <p><strong>This verification link will expire in 24 hours.</strong></p>
                        
                        <p>Once verified, you'll be able to access:</p>
                        <ul>
                            <li>🎯 Personalized meal planning with AI</li>
                            <li>📝 Smart shopping list generation</li>
                            <li>⚙️ Custom dietary preferences</li>
                            <li>💾 Save your favorite recipes</li>
                        </ul>
                        
                        <p>If you didn't create an account with us, please ignore this email.</p>
                        
                        <p>Happy cooking!<br>The Recipe App Team</p>
                    </div>
                    <div class="footer">
                        <p>This is an automated message. Please do not reply to this email.</p>
                        <p>Recipe App &copy; 2024. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_body = f"""
            Hi {recipient_name},
            
            Thank you for signing up for our Recipe App! 
            
            To complete your registration, please verify your email address by clicking the link below:
            {verification_url}
            
            This verification link will expire in 24 hours.
            
            Once verified, you'll be able to access:
            - Personalized meal planning with AI
            - Smart shopping list generation
            - Custom dietary preferences
            - Save your favorite recipes
            
            If you didn't create an account with us, please ignore this email.
            
            Happy cooking!
            The Recipe App Team
            """
            
            msg = Message(
                subject=subject,
                recipients=[email],
                html=html_body,
                body=text_body
            )
            
            self.mail.send(msg)
            
            return {
                "success": True,
                "message": "Verification email sent successfully",
                "verification_url": verification_url
            }
            
        except Exception as e:
            # If email sending fails, still return success for user registration
            frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:8081')
            verification_url = f"{frontend_url}/verify-email?token={verification_token}"
            
            return {
                "success": True,
                "message": f"User registered successfully. Email sending failed: {str(e)}",
                "verification_url": verification_url,
                "email_error": str(e)
            }
    
    def send_welcome_email(self, email: str, full_name: str = "") -> Dict[str, Any]:
        """Send welcome email after successful verification"""
        try:
            if not self.mail:
                return {"success": True, "message": "Email service not configured. Welcome message skipped."}
            
            subject = "Welcome to Recipe App! 🎉"
            recipient_name = full_name if full_name else email.split('@')[0]
            
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Welcome to Recipe App</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #28a745; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ background-color: #ffffff; padding: 30px; border: 1px solid #e9ecef; }}
                    .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 0 0 8px 8px; font-size: 12px; color: #6c757d; }}
                    .button {{ display: inline-block; padding: 12px 24px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px; font-weight: bold; }}
                    .feature {{ background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 4px; border-left: 4px solid #007bff; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🍳 Welcome to Recipe App!</h1>
                        <p>Your culinary journey starts here</p>
                    </div>
                    <div class="content">
                        <p>Hi {recipient_name},</p>
                        <p>🎉 Congratulations! Your email has been verified and your account is now active.</p>
                        
                        <p>You now have access to all our amazing features:</p>
                        
                        <div class="feature">
                            <h3>AI Meal Planning</h3>
                            <p>Get personalized weekly meal plans based on your dietary preferences, cooking skills, and favorite cuisines.</p>
                        </div>
                        
                        <div class="feature">
                            <h3>📝 Smart Shopping Lists</h3>
                            <p>Automatically generate organized shopping lists from your meal plans with smart ingredient grouping.</p>
                        </div>
                        
                        <div class="feature">
                            <h3>⚙️ Custom Preferences</h3>
                            <p>Set your dietary restrictions, allergens, cooking skill level, and favorite cuisines for personalized recommendations.</p>
                        </div>
                        
                        <p style="text-align: center; margin: 30px 0;">
                            <a href="{os.getenv('FRONTEND_URL', 'http://localhost:8081')}/preferences" class="button">Set Your Preferences</a>
                        </p>
                        
                        <p>Ready to start your personalized cooking adventure? Sign in and explore all the features we have to offer!</p>
                        
                        <p>Happy cooking!<br>The Recipe App Team</p>
                    </div>
                    <div class="footer">
                        <p>Need help? Contact us at support@recipeapp.com</p>
                        <p>Recipe App &copy; 2024. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg = Message(
                subject=subject,
                recipients=[email],
                html=html_body
            )
            
            self.mail.send(msg)
            
            return {"success": True, "message": "Welcome email sent successfully"}
            
        except Exception as e:
            return {"success": True, "message": f"Welcome message skipped due to email error: {str(e)}"} 