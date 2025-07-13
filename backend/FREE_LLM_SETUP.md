# Free LLM Setup Guide for AI Meal Planner

This meal planner uses **completely free** LLM models to generate personalized meal plans. You have three options:

## Option 1: Ollama (Recommended - Best Quality, Completely Free)

Ollama runs AI models locally on your computer for free with no limits.

### Setup Steps:
1. **Install Ollama**: Visit [ollama.ai](https://ollama.ai/) and download for your OS
2. **Install a model**: Run in terminal:
   ```bash
   ollama pull llama3.2:3b
   ```
3. **Start Ollama**: Run:
   ```bash
   ollama serve
   ```
4. **That's it!** The meal planner will automatically detect and use Ollama

### Benefits:
- ✅ Completely free with no limits
- ✅ Runs locally (no internet required after setup)
- ✅ Best quality meal plans
- ✅ Privacy-focused (data never leaves your computer)

## Option 2: Hugging Face (Free Tier)

Use Hugging Face's free cloud API for AI-generated meal plans.

### Setup Steps:
1. **Sign up**: Create account at [huggingface.co](https://huggingface.co/)
2. **Get API key**: Go to [Settings > Tokens](https://huggingface.co/settings/tokens)
3. **Set environment variable**:
   ```bash
   export HUGGINGFACE_API_KEY="your-api-key-here"
   ```
4. **Restart the backend** and it will use Hugging Face

### Benefits:
- ✅ Free tier available
- ✅ Cloud-based (no local installation)
- ✅ Good quality meal plans
- ⚠️ Rate limits on free tier

## Option 3: Fallback (Always Available)

If neither Ollama nor Hugging Face is set up, the system automatically uses a smart rule-based meal planner.

### Benefits:
- ✅ Always works
- ✅ Fast and reliable
- ✅ No setup required
- ⚠️ Less personalized than AI options

## How It Works

The system automatically detects which option is available and uses the best one:

1. **First choice**: Ollama (if running locally)
2. **Second choice**: Hugging Face (if API key is set)
3. **Fallback**: Rule-based system (always available)

## Testing Your Setup

1. Start your backend server
2. Check the logs - you'll see which service is being used:
   ```
   INFO:llm_meal_planner_agent:Using LLM service: ollama
   ```
3. Generate a meal plan to test!

## Troubleshooting

### Ollama Issues:
- Make sure Ollama is running: `ollama serve`
- Check if model is installed: `ollama list`
- Verify port 11434 is available

### Hugging Face Issues:
- Verify API key is set correctly
- Check rate limits on free tier
- Ensure internet connection is stable

### Still Having Issues?
The fallback system will always work, providing good meal plans even without AI!

## Performance Comparison

| Option | Quality | Speed | Cost | Setup |
|--------|---------|--------|------|-------|
| Ollama | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | FREE | Medium |
| Hugging Face | ⭐⭐⭐⭐ | ⭐⭐⭐ | FREE* | Easy |
| Fallback | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | FREE | None |

*Free tier with limits 