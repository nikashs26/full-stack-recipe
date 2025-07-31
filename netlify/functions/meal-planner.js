const { LLMMealPlannerAgent } = require('../../backend/services/llm_meal_planner_agent');
const { UserPreferencesService } = require('../../backend/services/user_preferences_service');

// Initialize services
const userPreferencesService = new UserPreferencesService();
const llmMealPlannerAgent = new LLMMealPlannerAgent();

exports.handler = async (event, context) => {
  // Enable CORS
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Content-Type': 'application/json'
  };

  // Handle preflight requests
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({ message: 'OK' })
    };
  }

  try {
    // Parse the request
    const { user_id, preferences } = JSON.parse(event.body || '{}');

    if (!user_id) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({ error: 'User ID is required' })
      };
    }

    // Get user preferences if not provided
    let userPrefs = preferences;
    if (!userPrefs) {
      userPrefs = userPreferencesService.get_preferences(user_id);
      if (!userPrefs) {
        return {
          statusCode: 404,
          headers,
          body: JSON.stringify({ 
            error: 'No preferences found for user',
            user_id,
            message: 'Please set your preferences first.'
          })
        };
      }
    }

    // Generate meal plan
    const result = llmMealPlannerAgent.generate_weekly_meal_plan(userPrefs);

    if (!result || result.error) {
      return {
        statusCode: 500,
        headers,
        body: JSON.stringify({
          error: 'Failed to generate meal plan',
          details: result?.error || 'Unknown error'
        })
      };
    }

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        success: true,
        plan: result.get('plan', result),
        preferences_used: userPrefs
      })
    };

  } catch (error) {
    console.error('Error in meal planner function:', error);
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({
        error: 'Internal server error',
        details: error.message
      })
    };
  }
}; 