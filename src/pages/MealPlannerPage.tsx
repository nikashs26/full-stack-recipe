import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import Header from '../components/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Clock, ChefHat, RefreshCw, ShoppingCart } from 'lucide-react';
import { MealPlan, MealPlanResponse, MealPlanItem, MealType, WeekDay } from '../types/mealPlanner';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';

const daysOfWeek: WeekDay[] = [
  'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
];
const mealTypes: MealType[] = ['breakfast', 'lunch', 'dinner'];

const MealPlannerPage: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const [mealPlan, setMealPlan] = useState<MealPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [regeneratingMeal, setRegeneratingMeal] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [preferences, setPreferences] = useState({
    dietaryRestrictions: [] as string[],
    favoriteCuisines: ['International', 'Mediterranean', 'Asian'],
    allergens: [] as string[],
    cookingSkillLevel: 'beginner',
    healthGoals: ['General wellness'],
    maxCookingTime: '30 minutes'
  });
  const navigate = useNavigate();

  const generatePlan = async () => {
    setLoading(true);
    setError(null);
    setMealPlan(null);

    try {
      const response = await fetch('/api/meal-plan/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          preferences: preferences
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to generate meal plan");
      }

      const data: MealPlanResponse = await response.json();
      if (data.success) {
        setMealPlan(data.plan);
        // Show which LLM was used
        if (data.llm_used) {
          console.log(`Meal plan generated using: ${data.llm_used}`);
        }
      } else {
        throw new Error(data.error || "Failed to generate meal plan");
      }

    } catch (err: any) {
      console.error("Error generating meal plan:", err);
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  const regenerateMeal = async (day: WeekDay, mealType: MealType) => {
    if (!mealPlan) return;

    const mealKey = `${day}-${mealType}`;
    setRegeneratingMeal(mealKey);

    try {
      const response = await fetch('/api/meal-plan/regenerate-meal', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          day,
          mealType,
          currentPlan: mealPlan,
          preferences: preferences
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to regenerate meal");
      }

      const data = await response.json();
      if (data.success) {
        setMealPlan(prev => {
          if (!prev) return null;
          return {
            ...prev,
            [day]: {
              ...prev[day],
              [mealType]: data.meal
            }
          };
        });
      } else {
        throw new Error(data.error || "Failed to regenerate meal");
      }

    } catch (err: any) {
      console.error("Error regenerating meal:", err);
      setError(err.message || "Failed to regenerate meal.");
    } finally {
      setRegeneratingMeal(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="pt-24 md:pt-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12">
          <div className="text-center mb-10">
            <h1 className="text-4xl font-bold text-gray-800 mb-4">AI-Powered Weekly Meal Planner</h1>
            <p className="text-lg text-gray-600">
              Let our AI nutritionist create a personalized meal plan for your week based on your preferences, dietary restrictions, and cooking skills.
            </p>
            <p className="text-sm text-blue-600 mt-2">
              🤖 Uses free AI models - no login required for testing!
            </p>
          </div>

          {/* Simple Preferences Section */}
          <div className="max-w-2xl mx-auto mb-8">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Quick Preferences</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Dietary Restrictions</label>
                  <div className="flex flex-wrap gap-2">
                    {['vegetarian', 'vegan', 'keto', 'gluten-free'].map(diet => (
                      <Button
                        key={diet}
                        variant={preferences.dietaryRestrictions.includes(diet) ? "default" : "outline"}
                        size="sm"
                        onClick={() => {
                          setPreferences(prev => ({
                            ...prev,
                            dietaryRestrictions: prev.dietaryRestrictions.includes(diet)
                              ? prev.dietaryRestrictions.filter(d => d !== diet)
                              : [...prev.dietaryRestrictions, diet]
                          }));
                        }}
                      >
                        {diet}
                      </Button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Cooking Skill</label>
                  <div className="flex gap-2">
                    {['beginner', 'intermediate', 'advanced'].map(skill => (
                      <Button
                        key={skill}
                        variant={preferences.cookingSkillLevel === skill ? "default" : "outline"}
                        size="sm"
                        onClick={() => {
                          setPreferences(prev => ({
                            ...prev,
                            cookingSkillLevel: skill
                          }));
                        }}
                      >
                        {skill}
                      </Button>
                    ))}
                  </div>
                </div>
              </div>
            </Card>
          </div>

          <div className="flex justify-center mb-8 gap-4">
            <Button 
              onClick={generatePlan}
              disabled={loading}
              className="px-8 py-3 text-lg bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
            >
              {loading ? "AI is cooking up your plan..." : "Generate AI Meal Plan"}
            </Button>

            {mealPlan && (
              <Button
                onClick={async () => {
                  setLoading(true);
                  setError(null);
                  try {
                    const response = await fetch('/api/shopping-list/generate', {
                      method: 'POST',
                      headers: {
                        'Content-Type': 'application/json',
                      },
                      body: JSON.stringify({ weekly_plan: mealPlan }),
                    });

                    if (!response.ok) {
                      const errorData = await response.json();
                      throw new Error(errorData.error || "Failed to generate shopping list");
                    }

                    const data = await response.json();
                    localStorage.setItem('agent-shopping-list', JSON.stringify(data.shopping_list));
                    navigate('/shopping-list');

                  } catch (err: any) {
                    console.error("Error generating shopping list:", err);
                    setError(err.message || "An unexpected error occurred while generating shopping list.");
                  } finally {
                    setLoading(false);
                  }
                }}
                disabled={loading || !mealPlan}
                className="px-8 py-3 text-lg bg-green-500 hover:bg-green-600"
              >
                {loading ? "Generating List..." : "Generate Shopping List"}
              </Button>
            )}
          </div>

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-8" role="alert">
              <strong className="font-bold">Error:</strong>
              <span className="block sm:inline"> {error}</span>
              {error.includes("No recipes match") && (
                <p className="mt-2 text-sm">Consider adjusting your <Link to="/preferences" className="text-red-800 underline">preferences</Link>.</p>
              )}
            </div>
          )}

          {mealPlan && (
            <div className="bg-white shadow-md rounded-lg p-6">
              <h2 className="text-2xl font-bold mb-6 text-center">Your AI-Generated Weekly Plan</h2>
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 xl:grid-cols-3">
                {daysOfWeek.map(day => (
                  <Card key={day} className="shadow-sm">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-xl capitalize text-center text-blue-700">{day}</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {mealTypes.map(mealType => {
                        const meal = mealPlan[day][mealType];
                        const isRegenerating = regeneratingMeal === `${day}-${mealType}`;
                        
                        return (
                          <div key={mealType} className="border rounded-lg p-3 bg-gray-50">
                            <div className="flex items-center justify-between mb-2">
                              <h4 className="font-medium text-gray-700 capitalize">{mealType}</h4>
                              <Button
                                onClick={() => regenerateMeal(day, mealType)}
                                disabled={isRegenerating}
                                variant="outline"
                                size="sm"
                                className="h-7 w-7 p-0"
                              >
                                <RefreshCw className={`h-3 w-3 ${isRegenerating ? 'animate-spin' : ''}`} />
                              </Button>
                            </div>
                            
                            {meal ? (
                              <div className="space-y-2">
                                <h5 className="font-semibold text-gray-800">{meal.name}</h5>
                                <p className="text-sm text-gray-600">{meal.description}</p>
                                
                                <div className="flex flex-wrap gap-2">
                                  <Badge variant="secondary" className="text-xs">
                                    <ChefHat className="h-3 w-3 mr-1" />
                                    {meal.cuisine}
                                  </Badge>
                                  <Badge variant="outline" className="text-xs">
                                    <Clock className="h-3 w-3 mr-1" />
                                    {meal.cookingTime}
                                  </Badge>
                                  <Badge 
                                    variant={meal.difficulty === 'beginner' ? 'default' : 
                                           meal.difficulty === 'intermediate' ? 'secondary' : 'destructive'}
                                    className="text-xs"
                                  >
                                    {meal.difficulty}
                                  </Badge>
                                </div>
                                
                                <div className="text-xs text-gray-500">
                                  <strong>Ingredients:</strong> {meal.ingredients.slice(0, 3).join(', ')}
                                  {meal.ingredients.length > 3 && ` +${meal.ingredients.length - 3} more`}
                                </div>
                                
                                <details className="text-xs text-gray-600">
                                  <summary className="cursor-pointer hover:text-gray-800">Instructions</summary>
                                  <p className="mt-1 pl-2 border-l-2 border-gray-200">{meal.instructions}</p>
                                </details>
                              </div>
                            ) : (
                              <div className="text-center text-gray-500 italic text-sm py-4">
                                No meal assigned
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default MealPlannerPage; 