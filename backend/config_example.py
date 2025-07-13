# Configuration Example for Free LLM Meal Planner
# Copy this file to config.py and update with your settings

import os

# Free LLM Configuration Options

# Option 1: Ollama (Completely Free - Runs Locally)
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')

# Option 2: Hugging Face (Free Tier Available)
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY', '')

# Flask Configuration
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

# MongoDB Configuration (optional)
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/recipe_app')

# ChromaDB Configuration
CHROMADB_PERSIST_DIRECTORY = os.getenv('CHROMADB_PERSIST_DIRECTORY', './chromadb_data')

# Instructions for Free LLM Setup:

# OPTION 1: Ollama (Recommended - Completely Free)
# 1. Install Ollama: https://ollama.ai/
# 2. Run: ollama pull llama3.2:3b
# 3. Start Ollama service: ollama serve
# 4. The system will automatically detect and use Ollama

# OPTION 2: Hugging Face (Free Tier)
# 1. Sign up at https://huggingface.co/
# 2. Get your API key from https://huggingface.co/settings/tokens
# 3. Set HUGGINGFACE_API_KEY environment variable
# 4. Free tier has rate limits but works well for testing

# OPTION 3: Fallback (Always Available)
# If neither Ollama nor Hugging Face is available, the system will use
# a rule-based meal planning system that still provides good results

# Performance Notes:
# - Ollama: Best quality, runs locally, completely free, no rate limits
# - Hugging Face: Good quality, cloud-based, free tier with limits
# - Fallback: Fast, reliable, but less personalized 