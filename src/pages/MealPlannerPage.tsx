import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ChefHat, Clock, RefreshCw, ShoppingCart, Calendar, Utensils, Star, TrendingUp, DollarSign, Users } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import Header from '../components/Header';
import { LLMMealPlan, MealPlanResponse, MealType, MealPlanItem } from '../types/mealPlanner';

const MealPlannerPage: React.FC = () => {
  const [mealPlan, setMealPlan] = useState<LLMMealPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [regeneratingMeal, setRegeneratingMeal] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [preferences, setPreferences] = useState<any>(null);
  const [preferencesLoading, setPreferencesLoading] = useState(true);
  const [weeklyBudget, setWeeklyBudget] = useState<string>('');
  const [servingAmount, setServingAmount] = useState<string>('');
  const navigate = useNavigate();

  // Load preferences from ChromaDB on mount
  useEffect(() => {
    const loadPreferences = async () => {
      console.log('🔥 MEAL_PLANNER_PAGE: Loading preferences...');
      try {
        const response = await fetch('http://localhost:5003/api/temp-preferences', {
          credentials: 'include' // Include cookies for session
        });
        console.log('🔥 MEAL_PLANNER_PAGE: Response status:', response.status);
        
        if (response.ok) {
          const data = await response.json();
          console.log('🔥 MEAL_PLANNER_PAGE: Response data:', data);
          
          if (data.preferences) {
            console.log('🔥 MEAL_PLANNER_PAGE: Setting preferences:', data.preferences);
            setPreferences(data.preferences);
            // Load budget and serving amount from preferences
            setWeeklyBudget(data.preferences.weeklyBudget || '');
            setServingAmount(data.preferences.servingAmount || '');
          } else {
            console.log('🔥 MEAL_PLANNER_PAGE: No preferences found in response');
            setError("Please set your preferences first to get personalized meal plans.");
          }
        } else {
          console.log('🔥 MEAL_PLANNER_PAGE: Response not ok');
          setError("Unable to load your preferences. Please try again.");
        }
      } catch (error) {
        console.error('🔥 MEAL_PLANNER_PAGE: Error loading preferences:', error);
        setError("Unable to load your preferences. Please try again.");
      } finally {
        setPreferencesLoading(false);
      }
    };

    loadPreferences();
  }, []);

  // Save budget and serving amount to ChromaDB
  const saveBudgetAndServing = async (budget: string, serving: string) => {
    try {
      const response = await fetch('http://localhost:5003/api/temp-preferences', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          preferences: {
            ...preferences,
            weeklyBudget: budget,
            servingAmount: serving
          }
        }),
      });

      if (response.ok) {
        console.log('🔥 MEAL_PLANNER_PAGE: Budget and serving amount saved successfully');
      } else {
        console.error('🔥 MEAL_PLANNER_PAGE: Failed to save budget and serving amount');
      }
    } catch (error) {
      console.error('🔥 MEAL_PLANNER_PAGE: Error saving budget and serving amount:', error);
    }
  };

  // Auto-save budget and serving amount when they change
  useEffect(() => {
    if (weeklyBudget !== '' || servingAmount !== '') {
      const timeoutId = setTimeout(() => {
        saveBudgetAndServing(weeklyBudget, servingAmount);
      }, 1000); // Save after 1 second of no changes

      return () => clearTimeout(timeoutId);
    }
  }, [weeklyBudget, servingAmount, preferences]);

  const generatePlan = async () => {
    if (!preferences) {
      setError("Please set your preferences first.");
      return;
    }

    setLoading(true);
    setError(null);
    setMealPlan(null);

    try {
      const response = await fetch('http://localhost:5003/api/meal-plan/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          preferences: {
            ...preferences,
            weeklyBudget: weeklyBudget,
            servingAmount: servingAmount
          }
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to generate meal plan");
      }

      const data: MealPlanResponse = await response.json();
      if (data.success) {
        setMealPlan(data.meal_plan);
        console.log(`Meal plan generated using: ${data.llm_used}`);
        console.log(`Plan type: ${data.meal_plan.plan_type}`);
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

  const regenerateMeal = async (day: string, mealType: MealType) => {
    if (!mealPlan || !preferences) return;

    const mealKey = `${day}-${mealType}`;
    setRegeneratingMeal(mealKey);

    try {
      const response = await fetch('http://localhost:5003/api/meal-plan/regenerate-meal', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          day,
          mealType,
          preferences: preferences
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to regenerate meal");
      }

      const data = await response.json();
      if (data.success) {
        // Update the specific meal in the plan
        setMealPlan(prev => {
          if (!prev) return null;
          
          const updatedDays = prev.days.map(dayPlan => {
            if (dayPlan.day.toLowerCase() === day.toLowerCase()) {
              return {
                ...dayPlan,
                meals: {
                  ...dayPlan.meals,
                  [mealType]: data.meal
                }
              };
            }
            return dayPlan;
          });

          return {
            ...prev,
            days: updatedDays
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

  const generateShoppingList = async () => {
    if (!mealPlan) return;

    setLoading(true);
    setError(null);

    try {
      // Use the built-in shopping list from the meal plan
      const shoppingList = mealPlan.weekly_shopping_list;
      
      // Store in localStorage for the shopping list page
      localStorage.setItem('agent-shopping-list', JSON.stringify({
        items: [
          ...shoppingList.proteins.map(item => ({ name: item, category: 'Proteins', completed: false })),
          ...shoppingList.vegetables.map(item => ({ name: item, category: 'Vegetables', completed: false })),
          ...shoppingList.grains.map(item => ({ name: item, category: 'Grains', completed: false })),
          ...shoppingList.dairy.map(item => ({ name: item, category: 'Dairy', completed: false })),
          ...shoppingList.pantry.map(item => ({ name: item, category: 'Pantry', completed: false }))
        ],
        estimated_cost: shoppingList.estimated_cost,
        generated_at: new Date().toISOString(),
        meal_plan_id: mealPlan.generated_at
      }));

      navigate('/shopping-list');

    } catch (err: any) {
      console.error("Error generating shopping list:", err);
      setError(err.message || "An unexpected error occurred while generating shopping list.");
    } finally {
      setLoading(false);
    }
  };

  if (preferencesLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main className="pt-24 md:pt-28">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <div className="text-center">
              <h1 className="text-4xl font-bold text-gray-800 mb-4">Loading Your Preferences...</h1>
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-1/3 mx-auto"></div>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="pt-24 md:pt-28">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gray-800 mb-4">🤖 AI-Powered Weekly Meal Planner</h1>
            <p className="text-lg text-gray-600 mb-2">
              Let our AI nutritionist create a personalized weekly meal plan based on your preferences.
            </p>
            <p className="text-sm text-blue-600">
              ✨ Powered by FREE AI models (Ollama/Hugging Face) - detailed recipes, shopping lists, and nutritional insights included!
            </p>
          </div>

          {preferences && (
            <div className="max-w-4xl mx-auto mb-8">
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center">
                  <Utensils className="h-5 w-5 mr-2" />
                  Your Saved Preferences
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Dietary Restrictions</label>
                    <div className="flex flex-wrap gap-2">
                      {preferences.dietaryRestrictions?.length > 0 ? (
                        preferences.dietaryRestrictions.map((diet: string) => (
                          <Badge key={diet} variant="secondary">{diet}</Badge>
                        ))
                      ) : (
                        <span className="text-gray-500 text-sm">None</span>
                      )}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Favorite Cuisines</label>
                    <div className="flex flex-wrap gap-2">
                      {preferences.favoriteCuisines?.length > 0 ? (
                        preferences.favoriteCuisines.map((cuisine: string) => (
                          <Badge key={cuisine} variant="outline">{cuisine}</Badge>
                        ))
                      ) : (
                        <span className="text-gray-500 text-sm">None</span>
                      )}
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Cooking Skill</label>
                    <Badge variant="default">{preferences.cookingSkillLevel || 'beginner'}</Badge>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Allergens to Avoid</label>
                    <div className="flex flex-wrap gap-2">
                      {preferences.allergens?.length > 0 ? (
                        preferences.allergens.map((allergen: string) => (
                          <Badge key={allergen} variant="destructive">{allergen}</Badge>
                        ))
                      ) : (
                        <span className="text-gray-500 text-sm">None</span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="mt-4 text-center">
                  <Link to="/preferences">
                    <Button variant="outline" size="sm">
                      Update Preferences
                    </Button>
                  </Link>
                </div>
              </Card>
            </div>
          )}

          {/* Budget and Serving Amount Inputs */}
          <div className="max-w-4xl mx-auto mb-8">
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <DollarSign className="h-5 w-5 mr-2" />
                Meal Planning Settings
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <Label htmlFor="weeklyBudget" className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                    <DollarSign className="h-4 w-4 mr-1" />
                    Weekly Budget (USD)
                  </Label>
                  <Input
                    id="weeklyBudget"
                    type="number"
                    placeholder="e.g., 100"
                    value={weeklyBudget}
                    onChange={(e) => setWeeklyBudget(e.target.value)}
                    className="w-full"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Set your weekly grocery budget to get cost-conscious meal suggestions
                  </p>
                </div>
                <div>
                  <Label htmlFor="servingAmount" className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                    <Users className="h-4 w-4 mr-1" />
                    Number of People
                  </Label>
                  <Input
                    id="servingAmount"
                    type="number"
                    placeholder="e.g., 2"
                    value={servingAmount}
                    onChange={(e) => setServingAmount(e.target.value)}
                    className="w-full"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    How many people will be eating these meals?
                  </p>
                </div>
              </div>
            </Card>
          </div>

          <div className="flex justify-center mb-8 gap-4">
            <Button 
              onClick={generatePlan}
              disabled={loading || !preferences}
              className="px-8 py-3 text-lg bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700"
            >
              {loading ? "🤖 AI is cooking up your plan..." : "Generate AI Meal Plan"}
            </Button>

            {mealPlan && (
              <Button
                onClick={generateShoppingList}
                disabled={loading}
                className="px-8 py-3 text-lg bg-green-500 hover:bg-green-600"
              >
                <ShoppingCart className="h-5 w-5 mr-2" />
                {loading ? "Generating List..." : "Get Shopping List"}
              </Button>
            )}
          </div>

          {error && (
            <Alert className="mb-8 border-red-200 bg-red-50">
              <AlertDescription className="text-red-800">
                <strong>Error:</strong> {error}
                {error.includes("preferences") && (
                  <p className="mt-2 text-sm">
                    <Link to="/preferences" className="text-red-800 underline">
                      Set your preferences here
                    </Link> to get personalized meal plans.
                  </p>
                )}
              </AlertDescription>
            </Alert>
          )}

          {mealPlan && (
            <div className="space-y-8">
              {/* Week Summary */}
              <Card className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-2xl font-bold flex items-center">
                    <Calendar className="h-6 w-6 mr-2" />
                    {mealPlan.week_summary.theme}
                  </h2>
                  <div className="flex items-center gap-2">
                    <Badge variant={mealPlan.plan_type === 'llm_generated' ? 'default' : 'secondary'}>
                      {mealPlan.plan_type === 'llm_generated' ? '🤖 AI Generated' : '📋 Rule-based'}
                    </Badge>
                    <Badge variant="outline">
                      {mealPlan.week_summary.total_recipes} recipes
                    </Badge>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="font-semibold mb-2 flex items-center">
                      <TrendingUp className="h-4 w-4 mr-1" />
                      Prep Tips
                    </h3>
                    <ul className="space-y-1 text-sm text-gray-600">
                      {mealPlan.week_summary.prep_tips.map((tip, index) => (
                        <li key={index} className="flex items-start">
                          <span className="text-blue-500 mr-2">•</span>
                          {tip}
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  <div>
                    <h3 className="font-semibold mb-2 flex items-center">
                      <Star className="h-4 w-4 mr-1" />
                      Nutritional Highlights
                    </h3>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span>Variety Score:</span>
                        <Badge variant="outline">{mealPlan.nutritional_summary.variety_score}</Badge>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span>Health Rating:</span>
                        <Badge variant="outline">{mealPlan.nutritional_summary.health_rating}</Badge>
                      </div>
                      <div className="text-xs text-gray-600">
                        {mealPlan.nutritional_summary.weekly_highlights.join(', ')}
                      </div>
                    </div>
                  </div>
                </div>
              </Card>

              {/* Daily Meal Plans */}
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 xl:grid-cols-3">
                {mealPlan.days.map((dayPlan, index) => (
                  <Card key={index} className="shadow-sm">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-xl text-center text-blue-700 flex items-center justify-center">
                        <Calendar className="h-5 w-5 mr-2" />
                        {dayPlan.day}
                      </CardTitle>
                      <p className="text-sm text-gray-500 text-center">{dayPlan.date}</p>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {(['breakfast', 'lunch', 'dinner'] as MealType[]).map(mealType => {
                        const meal = dayPlan.meals[mealType];
                        const isRegenerating = regeneratingMeal === `${dayPlan.day}-${mealType}`;
                        
                        return (
                          <div key={mealType} className="border rounded-lg p-4 bg-gray-50">
                            <div className="flex items-center justify-between mb-3">
                              <h4 className="font-medium text-gray-700 capitalize flex items-center">
                                <ChefHat className="h-4 w-4 mr-1" />
                                {mealType}
                              </h4>
                              <Button
                                onClick={() => regenerateMeal(dayPlan.day, mealType)}
                                disabled={isRegenerating}
                                variant="outline"
                                size="sm"
                                className="h-8 w-8 p-0"
                              >
                                <RefreshCw className={`h-4 w-4 ${isRegenerating ? 'animate-spin' : ''}`} />
                              </Button>
                            </div>
                            
                            <div className="space-y-3">
                              <h5 className="font-semibold text-gray-800">{meal.name}</h5>
                              
                              <div className="flex flex-wrap gap-2">
                                <Badge variant="secondary" className="text-xs">
                                  {meal.cuisine}
                                </Badge>
                                <Badge variant="outline" className="text-xs">
                                  <Clock className="h-3 w-3 mr-1" />
                                  {meal.prep_time} + {meal.cook_time}
                                </Badge>
                                <Badge 
                                  variant={meal.difficulty === 'Easy' ? 'default' : 
                                         meal.difficulty === 'Medium' ? 'secondary' : 'destructive'}
                                  className="text-xs"
                                >
                                  {meal.difficulty}
                                </Badge>
                              </div>
                              
                              <div className="text-xs text-gray-600">
                                <div className="mb-2">
                                  <strong>Servings:</strong> {meal.servings}
                                </div>
                                <div className="mb-2">
                                  <strong>Highlights:</strong> {meal.nutritional_highlights.join(', ')}
                                </div>
                                <div className="mb-2">
                                  <strong>Ingredients:</strong> {meal.ingredients.slice(0, 3).join(', ')}
                                  {meal.ingredients.length > 3 && ` +${meal.ingredients.length - 3} more`}
                                </div>
                              </div>
                              
                              <details className="text-xs text-gray-600">
                                <summary className="cursor-pointer hover:text-gray-800 font-medium">
                                  View Recipe Instructions
                                </summary>
                                <div className="mt-2 pl-3 border-l-2 border-blue-200 space-y-1">
                                  {meal.instructions.map((instruction, idx) => (
                                    <p key={idx} className="text-xs">
                                      <span className="font-medium">{idx + 1}.</span> {instruction}
                                    </p>
                                  ))}
                                </div>
                              </details>
                              
                              <div className="flex flex-wrap gap-1 mt-2">
                                {meal.tags.map((tag, idx) => (
                                  <Badge key={idx} variant="outline" className="text-xs px-2 py-0">
                                    {tag}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                      
                      {dayPlan.daily_notes && (
                        <div className="text-xs text-gray-500 italic p-2 bg-blue-50 rounded">
                          💡 {dayPlan.daily_notes}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Shopping List Preview */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center">
                  <ShoppingCart className="h-5 w-5 mr-2" />
                  Weekly Shopping List Preview
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                  {Object.entries(mealPlan.weekly_shopping_list).map(([category, items]) => {
                    if (category === 'estimated_cost' || !Array.isArray(items)) return null;
                    
                    return (
                      <div key={category} className="space-y-2">
                        <h4 className="font-medium text-sm capitalize text-gray-700">{category}</h4>
                        <ul className="space-y-1">
                          {items.slice(0, 3).map((item, idx) => (
                            <li key={idx} className="text-xs text-gray-600">• {item}</li>
                          ))}
                          {items.length > 3 && (
                            <li className="text-xs text-gray-500">+{items.length - 3} more</li>
                          )}
                        </ul>
                      </div>
                    );
                  })}
                </div>
                <div className="mt-4 pt-4 border-t flex items-center justify-between">
                  <span className="text-sm text-gray-600">
                    <strong>Estimated Cost:</strong> {mealPlan.weekly_shopping_list.estimated_cost}
                  </span>
                  <Button onClick={generateShoppingList} variant="outline" size="sm">
                    <ShoppingCart className="h-4 w-4 mr-2" />
                    View Full List
                  </Button>
                </div>
              </Card>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default MealPlannerPage; 