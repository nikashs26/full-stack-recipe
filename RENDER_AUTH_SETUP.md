# 🔐 Render Authentication Setup Guide

This guide will help you set up proper user authentication with ChromaDB on Render, just like your local setup.

## 🌟 What's Included

### ✅ Complete Authentication System
- **User Registration** with email verification
- **Secure Login** with JWT tokens  
- **Password Security** with bcrypt hashing
- **Session Management** with JWT tokens (7-day expiry)
- **Admin Interface** for user management

### 🗄️ ChromaDB Collections
- **`users`** - User accounts and profiles
- **`verification_tokens`** - Email verification tokens
- **`user_preferences`** - User meal preferences
- **`recipes`** - Recipe data (existing)
- **`search_cache`** - Recipe search cache (existing)

## 🚀 Quick Setup

### 1. Deploy to Render
Your `render.yaml` is already configured with all necessary environment variables:
- `JWT_SECRET_KEY` - Auto-generated
- `ADMIN_SEED_TOKEN` - Auto-generated  
- `CHROMA_DB_PATH` - Set to `/opt/render/project/src/chroma_db`
- `RENDER_ENVIRONMENT` - Set to `true`

### 2. Test the System
```bash
# Test authentication system
python setup_render_auth.py

# Or with custom URL
RENDER_URL='https://your-app.onrender.com' python setup_render_auth.py
```

### 3. Get Admin Access
1. Go to your Render dashboard
2. Select your backend service
3. Go to Environment tab
4. Copy the `ADMIN_SEED_TOKEN` value
5. Set it as environment variable:
   ```bash
   export ADMIN_TOKEN='your-admin-token-here'
   ```

### 4. Manage Users
```bash
# View system statistics
python admin_interface.py stats

# List all users (paginated)
python admin_interface.py users

# Get user details
python admin_interface.py user <user_id>

# Verify a user manually
python admin_interface.py verify <user_id>

# Delete a user
python admin_interface.py delete <user_id>
```

## 🔧 API Endpoints

### Authentication Endpoints
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/verify-email` - Verify email with token
- `GET /api/auth/me` - Get current user info (protected)
- `POST /api/auth/logout` - Logout user

### Admin Endpoints (Require Admin Token)
- `GET /api/admin/stats` - System statistics
- `GET /api/admin/users` - List users with pagination
- `GET /api/admin/users/<user_id>` - Get user details
- `POST /api/admin/users/<user_id>/verify` - Verify user
- `DELETE /api/admin/users/<user_id>` - Delete user
- `POST /api/admin/seed` - Seed recipes

### Protected User Endpoints
- `GET /api/preferences` - Get user preferences
- `POST /api/preferences` - Save user preferences
- `POST /api/meal-plan/generate` - Generate AI meal plan
- `POST /api/shopping-list/generate` - Generate shopping list

## 📊 User Management

### Viewing Users
The admin interface provides comprehensive user management:

```bash
# Basic stats
python admin_interface.py stats

# List users with pagination
python admin_interface.py users 1 20  # page 1, 20 per page

# Search users by email
python admin_interface.py users 1 20 false "gmail"  # search for gmail users

# View only verified users
python admin_interface.py users 1 20 true  # verified only
```

### User Details
Each user record includes:
- **Basic Info**: user_id, email, full_name
- **Status**: is_verified, created_at, last_login
- **Preferences**: meal preferences and settings
- **Metadata**: ChromaDB metadata

### Admin Actions
- **Verify Users**: Manually verify users who haven't received emails
- **Delete Users**: Remove users and all their data
- **View Statistics**: Monitor system usage and growth

## 🔒 Security Features

### Password Security
- **bcrypt hashing** with salt
- **Minimum 8 characters** with complexity requirements
- **Secure password verification**

### JWT Tokens
- **7-day expiration** for security
- **HS256 algorithm** for signing
- **Automatic token validation** on protected routes

### Admin Security
- **Admin token required** for all admin endpoints
- **Token-based authentication** for admin actions
- **Secure user data access**

## 🗄️ ChromaDB Storage

### Persistent Storage
- **Render persistent volume** at `/opt/render/project/src/chroma_db`
- **Automatic directory creation** with proper permissions
- **Fallback to local storage** if needed

### Data Collections
1. **users** - User accounts and authentication data
2. **verification_tokens** - Email verification system
3. **user_preferences** - User meal preferences
4. **recipes** - Recipe database (existing)
5. **search_cache** - Recipe search optimization (existing)

## 🚨 Troubleshooting

### Common Issues

#### 1. Connection Failed
```bash
# Check if your Render service is running
curl https://your-app.onrender.com/api/health
```
- **Free tier limitation**: Services sleep after 15 minutes of inactivity
- **Solution**: Make a request to wake up the service

#### 2. Authentication Not Working
- Check Render environment variables are set
- Verify JWT_SECRET_KEY is generated
- Check backend logs in Render dashboard

#### 3. Admin Access Denied
- Verify ADMIN_SEED_TOKEN is set correctly
- Check token in Render environment variables
- Ensure token is passed in X-Admin-Token header

#### 4. ChromaDB Issues
- Check CHROMA_DB_PATH is set to `/opt/render/project/src/chroma_db`
- Verify RENDER_ENVIRONMENT is set to `true`
- Check directory permissions in logs

### Debug Commands
```bash
# Test basic connectivity
python setup_render_auth.py

# Check specific user
python admin_interface.py user <user_id>

# View system stats
python admin_interface.py stats
```

## 📈 Monitoring

### System Statistics
The admin interface provides real-time statistics:
- **Total users** and verification status
- **Recipe count** in database
- **User preferences** count
- **System health** indicators

### User Growth
Monitor user registration and activity:
- New user registrations
- Email verification rates
- User engagement metrics
- System performance

## 🎯 Next Steps

1. **Deploy to Render** using the existing configuration
2. **Test authentication** with the setup script
3. **Get admin access** and explore user management
4. **Monitor user activity** through the admin interface
5. **Customize preferences** and meal planning features

## 📞 Support

If you encounter issues:
1. Check Render service logs
2. Run the setup script for diagnostics
3. Verify environment variables
4. Test individual endpoints with curl

Your Render deployment now has the same user authentication capabilities as your local setup! 🎉
