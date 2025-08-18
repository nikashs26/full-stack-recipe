# Ollama Setup Guide for AI Meal Planner

The AI meal planner uses Ollama to generate personalized meal plans based on your preferences. This guide will help you set up Ollama on your system.

## What is Ollama?

Ollama is a free, local AI model runner that allows you to run large language models (LLMs) on your own computer without needing to pay for API calls or send your data to external services.

## Installation

### macOS
```bash
# Install using Homebrew
brew install ollama

# Or download from the official website
# https://ollama.ai/download
```

### Linux
```bash
# Install using curl
curl -fsSL https://ollama.ai/install.sh | sh

# Or download from the official website
# https://ollama.ai/download
```

### Windows
1. Download the installer from [https://ollama.ai/download](https://ollama.ai/download)
2. Run the installer and follow the prompts
3. Ollama will be available as a Windows service

## Getting Started

### 1. Start Ollama
```bash
ollama serve
```

This will start the Ollama server. Keep this terminal window open.

### 2. Pull a Model
In a new terminal window, pull a model that the meal planner can use:

```bash
# Recommended models (in order of preference):
ollama pull llama3.2:latest    # Best for meal planning
ollama pull llama3:latest      # Good alternative
ollama pull mistral:latest     # Smaller, faster model
ollama pull llama2:latest      # Older but reliable
```

### 3. Verify Installation
```bash
# List available models
ollama list

# Test a simple prompt
ollama run llama3.2:latest "Hello, can you help me plan meals?"
```

## Configuration

### Environment Variables
Create a `.env` file in your backend directory with:

```bash
OLLAMA_URL=http://localhost:11434
```

### Model Requirements
- **Minimum RAM**: 8GB (for llama3.2:latest)
- **Recommended RAM**: 16GB+ for optimal performance
- **Storage**: 4-8GB per model

## Testing the Integration

Run the test script to verify everything is working:

```bash
cd backend
python test_ollama_meal_planner.py
```

This will test:
1. ✅ Ollama connection
2. ✅ Model availability
3. ✅ Meal plan generation

## Troubleshooting

### Ollama won't start
```bash
# Check if Ollama is already running
ps aux | grep ollama

# Kill any existing processes
pkill ollama

# Start fresh
ollama serve
```

### Connection refused
```bash
# Check if the port is in use
lsof -i :11434

# Restart Ollama
ollama serve
```

### Model not found
```bash
# List available models
ollama list

# Pull the model again
ollama pull llama3.2:latest
```

### Out of memory errors
- Close other applications to free up RAM
- Use a smaller model: `ollama pull mistral:latest`
- Restart your computer

## Performance Tips

1. **Use SSD storage** for faster model loading
2. **Close unnecessary applications** to free up RAM
3. **Start with smaller models** if you have limited resources
4. **Keep Ollama running** to avoid model reloading delays

## Alternative Models

If you have limited resources, try these smaller models:

```bash
# Small models (2-4GB RAM)
ollama pull mistral:latest
ollama pull llama2:7b:latest

# Medium models (4-8GB RAM)
ollama pull llama3:8b:latest
ollama pull codellama:7b:latest

# Large models (8GB+ RAM)
ollama pull llama3.2:latest
ollama pull llama3:70b:latest
```

## Security

- Ollama runs locally on your machine
- No data is sent to external servers
- Models are downloaded from Ollama's official repository
- All meal planning data stays on your local system

## Support

- **Ollama Documentation**: [https://ollama.ai/docs](https://ollama.ai/docs)
- **GitHub Issues**: [https://github.com/ollama/ollama/issues](https://github.com/ollama/ollama/issues)
- **Community Discord**: [https://discord.gg/ollama](https://discord.gg/ollama)

## Next Steps

Once Ollama is set up and running:

1. ✅ Start your backend server
2. ✅ Set your meal preferences in the app
3. ✅ Generate your first AI meal plan!
4. 🎉 Enjoy personalized meal suggestions based on your preferences

The AI meal planner will now use Ollama to generate unique, personalized meal plans instead of falling back to basic templates.
