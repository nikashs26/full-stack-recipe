#!/bin/bash
# Keep Alive Script for Render Free Tier
# Run this script to keep your backend alive

echo "🚀 Starting Keep-Alive service for Render backend"
echo "📍 Backend URL: https://dietary-delight.onrender.com"
echo "⏰ Ping interval: 5 minutes"
echo ""

# Install requirements if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "📦 Activating virtual environment..."
source venv/bin/activate

echo "📦 Installing requirements..."
pip install -r requirements_keep_alive.txt

echo "🔄 Starting keep-alive service..."
echo "Press Ctrl+C to stop"
echo ""

# Run the keep-alive script
python3 keep_alive.py
