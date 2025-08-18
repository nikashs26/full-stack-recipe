#!/bin/bash

echo "🚀 Recipe App Deployment Script"
echo "================================"

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
else
    echo "✅ Railway CLI found"
fi

# Check if user is logged in to Railway
if ! railway whoami &> /dev/null; then
    echo "🔐 Please login to Railway:"
    railway login
else
    echo "✅ Already logged in to Railway"
fi

# Deploy to Railway
echo "🚂 Deploying to Railway..."
railway up

echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Get your backend URL from Railway dashboard"
echo "2. Update your frontend API calls to use the new URL"
echo "3. Deploy your frontend to Netlify/Vercel"
echo "4. Update CORS origins in backend/app.py with your frontend URL"
echo ""
echo "🔗 Railway Dashboard: https://railway.app/dashboard"
