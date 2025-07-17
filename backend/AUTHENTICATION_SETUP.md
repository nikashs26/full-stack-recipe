# 🔐 Authentication System - ChromaDB Implementation

This document describes the new authentication system that replaces Supabase with a ChromaDB-based solution.

## 🌟 Features

### ✅ Complete Authentication Flow
- **User Registration** with email verification
- **Secure Login** with JWT tokens
- **Email Verification** with expiring tokens (24 hours)
- **Password Security** with bcrypt hashing
- **Session Management** with JWT tokens (7-day expiry)

### 🔒 Protected Features
The following features now require authentication:
- **Preferences Management** (`/api/preferences`)
- **AI Meal Planning** (`/api/meal-plan/generate`)
- **Shopping List Generation** (`/api/shopping-list/generate`)

### 📧 Email System
- **Development Mode**: Verification URLs printed to console
- **Production Mode**: Real email sending via SMTP
- **Beautiful HTML emails** with verification links
- **Welcome emails** after successful verification

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
cd backend
pip install flask-mail werkzeug pyjwt itsdangerous bcrypt
```

### 2. Configure Environment
```bash
python setup_auth_env.py
```

This will guide you through setting up:
- Secret keys for Flask and JWT
- Email configuration (optional)
- AI API keys
- Database settings

### 3. Start the Server
```bash
python app.py
```

## 🏗️ Architecture

### ChromaDB Collections
The system uses ChromaDB to store:

1. **`users`** - User accounts
   ```json
   {
     "user_id": "user_abc123",
     "email": "user@example.com",
     "password_hash": "bcrypt_hash",
     "full_name": "John Doe",
     "is_verified": true,
     "created_at": "2024-01-01T00:00:00Z"
   }
   ```

2. **`verification_tokens`** - Email verification tokens
   ```json
   {
     "token": "uuid-token",
     "user_id": "user_abc123",
     "email": "user@example.com",
     "expires_at": "2024-01-02T00:00:00Z"
   }
   ```

3. **`user_preferences`** - User meal preferences (existing)

### Security Features
- **Password Hashing**: bcrypt with salt
- **JWT Tokens**: HS256 algorithm, 7-day expiry
- **Email Verification**: Required before access
- **Input Validation**: Email format, password strength
- **Rate Limiting**: Built-in via middleware

## 📡 API Endpoints

### Authentication Routes (`/api/auth/`)

#### `POST /api/auth/register`
Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "success": true,
  "message": "User registered successfully. Please check your email for verification.",
  "user_id": "user_abc123",
  "email": "user@example.com",
  "verification_url": "http://localhost:8080/verify-email?token=..."
}
```

#### `POST /api/auth/login`
Authenticate user login.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "user_id": "user_abc123",
    "email": "user@example.com",
    "full_name": "John Doe"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### `POST /api/auth/verify-email`
Verify email address.

**Request:**
```json
{
  "token": "verification-token-uuid"
}
```

#### `GET /api/auth/verify-email/<token>`
Verify email via GET request (for email links).

#### `POST /api/auth/resend-verification`
Resend verification email.

**Request:**
```json
{
  "email": "user@example.com"
}
```

#### `GET /api/auth/me`
Get current user information (requires authentication).

**Headers:**
```
Authorization: Bearer <jwt_token>
```

#### `POST /api/auth/logout`
Logout user (client-side token removal).

### Protected Routes

All protected routes require the `Authorization` header:
```
Authorization: Bearer <jwt_token>
```

- `GET/POST /api/preferences` - User preferences
- `GET/POST /api/meal-plan/generate` - AI meal planning
- `POST /api/shopping-list/generate` - Shopping list generation

## 🎨 Frontend Integration

### AuthContext Updates
The new `AuthContext` provides:

```typescript
interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  signIn: (email: string, password: string) => Promise<{success: boolean; error?: any}>;
  signUp: (email: string, password: string, fullName?: string) => Promise<{success: boolean; error?: any}>;
  signOut: () => Promise<void>;
  verifyEmail: (token: string) => Promise<{success: boolean; error?: any}>;
  resendVerification: (email: string) => Promise<{success: boolean; error?: any}>;
}
```

### New Pages
- **SignUpPage**: Enhanced with email verification flow
- **SignInPage**: Updated with verification status handling
- **VerifyEmailPage**: New page for email verification

### Making Authenticated Requests
```typescript
const response = await fetch('/api/preferences', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
```

## 🔧 Development

### Environment Variables
```env
# Required
SECRET_KEY=your-super-secret-flask-key
JWT_SECRET_KEY=your-super-secret-jwt-key
FRONTEND_URL=http://localhost:8080

# Optional (for email sending)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

### Testing the System

1. **Register a user:**
   ```bash
   curl -X POST http://localhost:5003/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "TestPass123",
       "full_name": "Test User"
     }'
   ```

2. **Verify email** (use token from registration response):
   ```bash
   curl -X POST http://localhost:5003/api/auth/verify-email \
     -H "Content-Type: application/json" \
     -d '{"token": "verification-token-here"}'
   ```

3. **Login:**
   ```bash
   curl -X POST http://localhost:5003/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "TestPass123"
     }'
   ```

4. **Access protected route:**
   ```bash
   curl -X GET http://localhost:5003/api/preferences \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
   ```

## 🛠️ Troubleshooting

### Common Issues

1. **"Email not verified" error**
   - Check console for verification URL in development mode
   - Ensure email service is configured correctly
   - Token expires after 24 hours

2. **"Invalid token" error**
   - JWT tokens expire after 7 days
   - Check token format: `Bearer <token>`
   - Ensure token is being stored/retrieved correctly

3. **Email not sending**
   - Check SMTP configuration
   - Verify app password for Gmail
   - Check firewall/network settings

### Database Reset
To reset the authentication database:
```bash
rm -rf backend/chroma_db/
```

## 🔄 Migration from Supabase

The new system maintains the same user experience while:
- **Removing** Supabase dependency
- **Adding** email verification requirement
- **Improving** security with proper password hashing
- **Maintaining** all existing functionality

Users will need to re-register as the database schema has changed.

## 🎯 Next Steps

1. **Setup email sending** for production
2. **Configure SSL/HTTPS** for production deployment
3. **Add password reset** functionality (future enhancement)
4. **Implement admin features** (future enhancement)
5. **Add OAuth integration** (future enhancement) 