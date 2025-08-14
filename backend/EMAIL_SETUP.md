# 📧 Email Service Setup for Recipe App

This guide will help you set up the email service to send verification emails to users during signup.

## 🚀 Quick Setup

### 1. Run the Email Setup Script
```bash
cd backend
python3 setup_email.py
```

This script will:
- Guide you through email configuration
- Add email settings to your `.env` file
- Test the email configuration
- Set up Gmail SMTP (recommended)

### 2. Alternative: Manual Setup
If you prefer to set up manually, add these variables to your `.env` file:

```bash
# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
FRONTEND_URL=http://localhost:8081
```

## 🔐 Gmail App Password Setup

**Important**: You need an App Password, not your regular Gmail password!

### Steps:
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Factor Authentication if not already enabled
3. Go to "App passwords" (under 2-Step Verification)
4. Select "Mail" and "Other (Custom name)"
5. Enter "Recipe App" as the name
6. Copy the generated 16-character password
7. Use this password in your email configuration

## 🧪 Testing the Setup

### 1. Test Email Configuration
The setup script will offer to test your email configuration by sending a test email to yourself.

### 2. Test User Registration
1. Start your backend server: `python3 app.py`
2. Go to your frontend signup page
3. Register a new user with a real email address
4. Check the user's email for the verification link

## 🔧 Troubleshooting

### Common Issues:

#### 1. "Email service not initialized"
- Make sure you've run the setup script
- Check that your `.env` file contains email configuration
- Restart your backend server after configuration changes

#### 2. "Authentication failed"
- Ensure you're using an App Password, not your regular password
- Verify 2-factor authentication is enabled on your Google account
- Check that the email and password are correct

#### 3. "Connection refused"
- Verify the SMTP server and port are correct
- Check your firewall/antivirus settings
- Ensure your network allows SMTP connections

#### 4. "Rate limit exceeded"
- Gmail has daily sending limits
- Consider using a different email service for production

## 📱 Frontend Configuration

Make sure your frontend is configured to use the correct backend URL:

```typescript
// In your frontend config
const API_BASE_URL = 'http://localhost:5003'; // or your backend port
```

## 🚀 Production Considerations

For production deployment:

1. **Use a dedicated email service** like SendGrid, Mailgun, or AWS SES
2. **Set up proper DNS records** (SPF, DKIM, DMARC)
3. **Monitor email delivery rates**
4. **Implement email templates** for better deliverability
5. **Set up email analytics** to track open/click rates

## 📋 Email Templates

The app includes beautiful HTML email templates for:
- **Verification emails** - Sent when users sign up
- **Welcome emails** - Sent after email verification

Templates are customizable in `services/email_service.py`.

## ✅ Success Indicators

You'll know the email service is working when:
1. ✅ "Email service initialized" appears in backend console
2. ✅ Users receive verification emails after signup
3. ✅ Users receive welcome emails after verification
4. ✅ No "Email service not initialized" errors in logs

## 🆘 Getting Help

If you're still having issues:
1. Check the backend console for error messages
2. Verify your `.env` file configuration
3. Test SMTP connection manually
4. Check Gmail's "Less secure app access" settings (if applicable)

---

**Happy emailing! 📧✨**
