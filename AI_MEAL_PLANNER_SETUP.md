# AI Meal Planner Setup Guide

The AI meal planner is now working and ready to use! It takes your preferences and generates personalized weekly meal plans.

## How It Works

The meal planner uses a **smart fallback system**:

1. **First choice**: Ollama (local AI models) - completely free, runs on your computer
2. **Fallback**: Rule-based system - always works, no setup required

## Quick Start

### 1. Set Your Preferences
Go to your app and set your preferences:
- Dietary restrictions (vegetarian, vegan, etc.)
- Favorite cuisines (Italian, Mexican, etc.)
- Favorite foods (pasta, chicken, etc.)
- Cooking skill level
- Meal preferences (breakfast, lunch, dinner, snacks)

### 2. Generate Meal Plan
The meal planner will automatically:
- Use your preferences to create personalized meals
- Generate a full week of meals
- Include cooking times and difficulty levels
- Respect your dietary restrictions

## Optional: Setup Ollama for Better AI-Generated Plans

If you want AI-generated meal plans (instead of rule-based), install Ollama:

### Install Ollama
1. Visit [ollama.ai](https://ollama.ai/) and download for your OS
2. Install and start Ollama
3. Pull a model: `ollama pull llama3.2:3b`
4. Start the server: `ollama serve`

### Benefits of Ollama
- ✅ Completely free with no limits
- ✅ Runs locally (no internet required)
- ✅ Better, more creative meal plans
- ✅ Privacy-focused (data never leaves your computer)

## API Endpoints

### Generate Meal Plan
```
GET /api/simple-meal-plan
```
Returns a weekly meal plan based on your preferences.

### Generate AI Meal Plan
```
POST /api/ai/meal_plan
```
Returns an AI-generated meal plan (requires Ollama or Hugging Face).

## Example Response

```json
{
  "success": true,
  "meal_plan": {
    "days": {
      "monday": {
        "breakfast": {
          "name": "Vegetable Omelet",
          "cuisine": "French",
          "cookingTime": "15 minutes",
          "difficulty": "beginner"
        },
        "lunch": {
          "name": "Quinoa Buddha Bowl",
          "cuisine": "International",
          "cookingTime": "25 minutes"
        },
        "dinner": {
          "name": "Pasta Primavera",
          "cuisine": "Italian",
          "cookingTime": "30 minutes"
        }
      }
    }
  },
  "llm_used": "Rule-based (Fallback)",
  "generated_at": "2024-01-01T12:00:00Z"
}
```

## Features

- ✅ **Personalized**: Uses your preferences and dietary restrictions
- ✅ **Complete**: Generates breakfast, lunch, and dinner for the whole week
- ✅ **Flexible**: Works with or without AI setup
- ✅ **Fast**: Rule-based fallback is instant
- ✅ **Free**: No API costs or subscriptions required

## Troubleshooting

### No meal plan generated?
- Make sure you've set your preferences in the app
- Check that the backend is running on port 5004

### Want AI-generated plans?
- Install and start Ollama
- The system will automatically detect and use it

### Port conflicts?
- The backend now runs on port 5004 by default
- Change the PORT environment variable if needed

## That's it!

Your AI meal planner is ready to use. It will generate personalized meal plans based on your preferences, and you can optionally enhance it with Ollama for AI-generated plans. 