#!/bin/bash

# Railway + Netlify Deployment Script
# This script helps you deploy your full-stack recipe app

echo "🚀 Full-Stack Recipe App Deployment Script"
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "railway.json" ] || [ ! -d "backend" ]; then
    echo "❌ Error: Please run this script from the root directory of your project"
    exit 1
fi

echo "✅ Project structure looks good!"

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "📥 Installing Railway CLI..."
    npm install -g @railway/cli
else
    echo "✅ Railway CLI is already installed"
fi

echo ""
echo "🔧 Railway Backend Deployment"
echo "=============================="
echo "1. Make sure you're logged into Railway:"
echo "   railway login"
echo ""
echo "2. Deploy to Railway:"
echo "   railway up"
echo ""
echo "3. Get your Railway URL:"
echo "   railway status"
echo ""

echo "🌐 Netlify Frontend Deployment"
echo "=============================="
echo "1. Push your changes to GitHub:"
echo "   git add ."
echo "   git commit -m 'Deploy to Railway and Netlify'"
echo "   git push origin main"
echo ""
echo "2. Netlify will auto-deploy from GitHub"
echo ""

echo "🔗 Connect Frontend to Backend"
echo "==============================="
echo "1. Update src/config/api.ts with your Railway URL"
echo "2. Update backend/app_railway.py CORS origins with your Netlify URL"
echo "3. Push changes to trigger redeployment"
echo ""

echo "📖 For detailed instructions, see: RAILWAY_DEPLOYMENT_GUIDE.md"
echo ""

# Check if there are any obvious issues
echo "🔍 Pre-deployment checks:"
if [ -f "backend/Dockerfile" ]; then
    echo "✅ Dockerfile exists in backend/"
else
    echo "❌ Dockerfile missing in backend/"
fi

if [ -f "backend/app_railway.py" ]; then
    echo "✅ Railway app exists"
else
    echo "❌ Railway app missing"
fi

if [ -f "backend/requirements-railway.txt" ]; then
    echo "✅ Railway requirements exist"
else
    echo "❌ Railway requirements missing"
fi

echo ""
echo "🎯 Ready to deploy! Follow the steps above."
