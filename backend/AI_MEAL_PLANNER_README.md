# 🤖 AI-Powered Meal Planner

This feature uses OpenAI's GPT-4 to generate personalized weekly meal plans based on user preferences, dietary restrictions, and cooking skills.

## 🚀 Features

### ✨ Intelligent Meal Planning
- **AI-Generated Plans**: Uses GPT-4o-mini to create balanced, varied meal plans
- **Personalized Recommendations**: Based on user preferences, dietary restrictions, and cooking skills
- **Nutritional Balance**: Ensures meals are nutritionally balanced across the week
- **Variety & Creativity**: Prevents meal monotony with diverse cuisines and cooking methods

### 🔄 Interactive Features
- **Regenerate Individual Meals**: Don't like a specific meal? Regenerate it instantly
- **Detailed Meal Information**: Each meal includes:
  - Description and cuisine type
  - Cooking time and difficulty level
  - Complete ingredients list
  - Step-by-step instructions
  - Nutritional considerations

### 🎯 User-Centric Design
- **Preference-Aware**: Respects dietary restrictions, allergens, and favorite cuisines
- **Skill-Appropriate**: Matches recipes to user's cooking skill level
- **Time-Conscious**: Considers maximum cooking time preferences
- **Health-Focused**: Aligns with user's health goals

## 🛠️ Setup Instructions

### 1. Install Dependencies
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Run the setup script to configure your OpenAI API key:
```bash
python setup_env.py
```

Or manually create a `.env` file with:
```env
OPENAI_API_KEY=your_openai_api_key_here
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here
```

### 3. Get Your OpenAI API Key
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create an account or sign in
3. Generate a new API key
4. Add it to your `.env` file

### 4. Run the Application
```bash
python app.py
```

## 📡 API Endpoints

### Generate Weekly Meal Plan
```
GET /api/meal-plan/generate
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "plan": {
    "monday": {
      "breakfast": {
        "id": "unique_id",
        "name": "Avocado Toast with Poached Egg",
        "description": "Creamy avocado on sourdough with perfectly poached egg",
        "cuisine": "American",
        "cookingTime": "15 minutes",
        "difficulty": "beginner",
        "ingredients": ["avocado", "sourdough bread", "eggs", "lemon juice"],
        "instructions": "Toast bread, mash avocado with lemon juice..."
      },
      "lunch": { ... },
      "dinner": { ... }
    },
    "tuesday": { ... },
    ...
  },
  "preferences_used": { ... }
}
```

### Regenerate Specific Meal
```
POST /api/meal-plan/regenerate-meal
Authorization: Bearer <token>
Content-Type: application/json

{
  "day": "monday",
  "mealType": "breakfast",
  "currentPlan": { ... }
}
```

## 🧠 How It Works

### 1. User Preference Analysis
The AI analyzes user preferences including:
- Dietary restrictions (vegetarian, vegan, keto, etc.)
- Allergens to avoid
- Favorite cuisines
- Cooking skill level
- Health goals
- Maximum cooking time

### 2. Intelligent Prompt Engineering
Creates detailed prompts that instruct the AI to:
- Generate exactly 21 meals (3 per day × 7 days)
- Ensure nutritional balance
- Respect all dietary constraints
- Vary cuisines and cooking methods
- Match complexity to skill level

### 3. Structured Response Processing
- Validates AI response format
- Ensures all required fields are present
- Formats data for frontend consumption
- Handles errors gracefully

### 4. Continuous Improvement
- Meal regeneration for user satisfaction
- Context-aware replacements
- Avoids repetition across the plan

## 🎨 Frontend Integration

### Enhanced UI Components
- **Interactive Meal Cards**: Show detailed meal information
- **Regeneration Buttons**: Allow users to replace individual meals
- **Progress Indicators**: Show AI generation status
- **Responsive Design**: Works on all device sizes

### User Experience Features
- **Loading States**: Clear feedback during AI generation
- **Error Handling**: Helpful error messages and recovery options
- **Preference Links**: Easy access to update preferences
- **Shopping List Integration**: Generate shopping lists from meal plans

## 🔒 Security & Privacy

### API Key Security
- Environment variables for sensitive data
- No API keys in client-side code
- Secure token-based authentication

### User Data Protection
- Preferences stored securely in ChromaDB
- No personal data sent to OpenAI
- JWT-based user authentication

## 💡 Usage Tips

### For Best Results
1. **Set Detailed Preferences**: The more specific your preferences, the better the AI recommendations
2. **Update Regularly**: Refresh your preferences as your tastes change
3. **Experiment**: Try regenerating meals to explore different options
4. **Plan Ahead**: Generate plans at the beginning of each week

### Troubleshooting
- **No meal plan generated**: Check your preferences are set
- **API errors**: Verify your OpenAI API key is valid
- **Slow generation**: AI processing can take 10-30 seconds
- **Repetitive meals**: Try regenerating or updating preferences

## 🚦 Rate Limits & Costs

### OpenAI API Usage
- Uses GPT-4o-mini for cost efficiency
- Typical cost: ~$0.10-0.20 per meal plan
- Rate limits: 500 requests per minute (standard)

### Optimization Tips
- Cache meal plans to reduce API calls
- Use regeneration sparingly
- Consider batch processing for multiple users

## 🔮 Future Enhancements

### Planned Features
- **Seasonal Ingredients**: Incorporate seasonal produce
- **Nutritional Analysis**: Detailed macro/micronutrient breakdowns
- **Recipe Scaling**: Adjust portions for household size
- **Learning System**: Improve recommendations based on user feedback
- **Integration**: Connect with grocery delivery services
- **Meal Prep Mode**: Generate prep-friendly meal plans

### Technical Improvements
- **Caching Layer**: Reduce API calls with intelligent caching
- **Fallback Systems**: Alternative AI providers for redundancy
- **Performance Optimization**: Faster response times
- **Analytics**: Track user satisfaction and preferences

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify your environment variables are set correctly
3. Ensure your OpenAI API key has sufficient credits
4. Check the Flask app logs for detailed error messages

---

*Enjoy your AI-powered meal planning experience! 🍽️✨* 