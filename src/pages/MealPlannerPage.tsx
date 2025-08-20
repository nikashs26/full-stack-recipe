import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '@/hooks/use-toast';
import Header from '../components/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ChefHat, Loader2, RefreshCw, Settings, Lock } from 'lucide-react';
import { generateMealPlan, regenerateMeal, type MealPlanData, type MealDay, type Meal } from '../services/mealPlannerService';
import MealPlannerAdvancedSettings, { type MealPlannerSettings } from '../components/MealPlannerAdvancedSettings';

const MealPlannerPage: React.FC = () => {
  const { isAuthenticated, isLoading: authLoading, user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [mealPlan, setMealPlan] = useState<MealPlanData | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [advancedSettingsOpen, setAdvancedSettingsOpen] = useState(false);
  const [mealPlannerSettings, setMealPlannerSettings] = useState<MealPlannerSettings>({
    targetCalories: 2000,
    targetProtein: 150,
    targetCarbs: 200,
    targetFat: 65,
    includeSnacks: false
  });
  
  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate('/signin');
      toast({
        title: "Authentication Required",
        description: "Please sign in to access the AI Meal Planner.",
        variant: "destructive"
      });
    }
  }, [isAuthenticated, authLoading, navigate, toast]);

  // Show loading state while checking authentication
  if (authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Checking authentication...</p>
        </div>
      </div>
    );
  }

  // Show login prompt if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="pt-24 md:pt-28">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
            <Card className="text-center">
              <CardHeader>
                <div className="flex justify-center mb-4">
                  <Lock className="h-12 w-12 text-orange-500" />
                </div>
                <CardTitle className="text-2xl">Authentication Required</CardTitle>
                <CardDescription>
                  Sign in to access the AI Meal Planner and create personalized weekly meal plans
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                  <Link to="/signin">
                    <Button size="lg">Sign In</Button>
                  </Link>
                  <Link to="/signup">
                    <Button variant="outline" size="lg">Sign Up</Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  const handleGenerateMealPlan = async () => {
    if (!isAuthenticated) {
      toast({
        title: "Authentication Required",
        description: "Please sign in to generate a meal plan.",
        variant: "destructive"
      });
      return;
    }

    setIsGenerating(true);
    setError(null);
    
    try {
      const plan = await generateMealPlan({
        nutritionTargets: {
          targetCalories: mealPlannerSettings.targetCalories,
          targetProtein: mealPlannerSettings.targetProtein,
          targetCarbs: mealPlannerSettings.targetCarbs,
          targetFat: mealPlannerSettings.targetFat,
          includeSnacks: mealPlannerSettings.includeSnacks
        }
      });
      
      setMealPlan(plan);
      
      toast({
        title: "Success!",
        description: `Your personalized weekly meal plan is ready with ${mealPlannerSettings.targetCalories} calories/day.`,
      });
      
      return plan;
    } catch (error) {
      console.error('Error generating meal plan:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to generate meal plan';
      setError(errorMessage);
      
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
      
      throw error;
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRegenerateMeal = async (day: string, mealType: string) => {
    try {
      await regenerateMeal(day, mealType);
      toast({
        title: "Meal Regenerated",
        description: `New ${mealType} for ${day} has been generated.`,
      });
    } catch (error) {
      console.error('Error regenerating meal:', error);
      toast({
        title: "Error",
        description: "Failed to regenerate meal. Please try again.",
        variant: "destructive"
      });
    }
  };

  const getNutritionValue = (value: any): string => {
    if (!value) return '0';
    if (typeof value === 'number') return value.toString();
    if (typeof value === 'string') return value;
    if (typeof value === 'object') {
      return value.amount?.toString() || value.value?.toString() || '0';
    }
    return '0';
  };

  const renderNutritionalInfo = () => {
    if (!mealPlan?.nutrition_summary) {
      return null;
    }
    
    const nutritionSummary: any = mealPlan.nutrition_summary || {};
    
    // Safely extract values with fallbacks
    const dailyCalories = getNutritionValue(nutritionSummary.daily_average?.calories);
    const dailyProtein = getNutritionValue(nutritionSummary.daily_average?.protein);
    const dailyCarbs = getNutritionValue(nutritionSummary.daily_average?.carbs);
    const dailyFat = getNutritionValue(nutritionSummary.daily_average?.fat);
    
    const weeklyCalories = getNutritionValue(nutritionSummary.weekly_totals?.calories);
    const weeklyProtein = getNutritionValue(nutritionSummary.weekly_totals?.protein);
    const weeklyCarbs = getNutritionValue(nutritionSummary.weekly_totals?.carbs);
    
    const mealInclusions = nutritionSummary.meal_inclusions || {};
    const dietaryConsiderations = nutritionSummary.dietary_considerations || [];
    
    return (
      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Nutritional Summary</CardTitle>
          <CardDescription>
            Overview of your weekly nutritional intake
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <div>
              <h4 className="font-medium mb-2">Daily Averages</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-orange-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-orange-600">
                    {dailyCalories}
                  </div>
                  <div className="text-sm text-gray-500">Calories</div>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {dailyProtein} {typeof dailyProtein === 'string' && !isNaN(Number(dailyProtein)) ? 'g' : ''}
                  </div>
                  <div className="text-sm text-gray-500">Protein</div>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">
                    {dailyCarbs} {typeof dailyCarbs === 'string' && !isNaN(Number(dailyCarbs)) ? 'g' : ''}
                  </div>
                  <div className="text-sm text-gray-500">Carbs</div>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600">
                    {dailyFat} {typeof dailyFat === 'string' && !isNaN(Number(dailyFat)) ? 'g' : ''}
                  </div>
                  <div className="text-sm text-gray-500">Fat</div>
                </div>
              </div>
            </div>
            
            <div className="mt-6">
              <h4 className="font-medium mb-2">Weekly Totals</h4>
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="text-lg font-semibold">
                    {weeklyCalories} {!isNaN(Number(weeklyCalories)) ? 'cal' : ''}
                  </div>
                  <div className="text-sm text-gray-500">Total Calories</div>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="text-lg font-semibold">
                    {weeklyProtein} {typeof weeklyProtein === 'string' && !isNaN(Number(weeklyProtein)) ? 'g' : ''}
                  </div>
                  <div className="text-sm text-gray-500">Total Protein</div>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="text-lg font-semibold">
                    {weeklyCarbs} {typeof weeklyCarbs === 'string' && !isNaN(Number(weeklyCarbs)) ? 'g' : ''}
                  </div>
                  <div className="text-sm text-gray-500">Total Carbs</div>
                </div>
              </div>
            </div>
            
            <div>
              <h4 className="font-medium mb-2">Meal Inclusions</h4>
              <div className="flex flex-wrap gap-2">
                {Object.entries(mealInclusions).map(([meal, included]) => (
                  <div 
                    key={meal}
                    className={`px-3 py-1 rounded-full text-sm ${
                      included 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-500'
                    }`}
                  >
                    {meal.charAt(0).toUpperCase() + meal.slice(1)}: {included ? 'Included' : 'Excluded'}
                  </div>
                ))}
              </div>
            </div>
            
            {dietaryConsiderations.length > 0 && (
              <div>
                <h4 className="font-medium mb-2">Dietary Considerations</h4>
                <div className="flex flex-wrap gap-2">
                  {dietaryConsiderations.map((consideration: string, index: number) => (
                    <span 
                      key={index} 
                      className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      {consideration}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="pt-24 md:pt-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header Section */}
          <div className="text-center mb-8">
            <div className="flex items-center justify-center gap-2 mb-4">
              <ChefHat className="h-8 w-8 text-orange-500" />
              <h1 className="text-3xl text-gray-900">🤖 AI Meal Planner</h1>
            </div>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Welcome back, {user?.full_name || user?.email}! Generate personalized weekly meal plans based on your preferences.
            </p>
          </div>

          {/* Advanced Settings */}
          <div className="max-w-2xl mx-auto mb-8">
            <MealPlannerAdvancedSettings
              settings={mealPlannerSettings}
              onSettingsChange={setMealPlannerSettings}
              isOpen={advancedSettingsOpen}
              onToggle={setAdvancedSettingsOpen}
            />
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
            <Button 
              onClick={handleGenerateMealPlan} 
              disabled={isGenerating}
              size="lg"
              className="flex items-center gap-2"
            >
              {isGenerating ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ChefHat className="h-4 w-4" />
              )}
              {isGenerating ? 'Generating...' : 'Generate New Meal Plan'}
            </Button>
            
            <Link to="/preferences">
              <Button variant="outline" size="lg" className="flex items-center gap-2">
                <Settings className="h-4 w-4" />
                Update Preferences
              </Button>
            </Link>
          </div>

          {/* Error State */}
          {error && (
            <Card className="mb-8 border-red-200 bg-red-50">
              <CardContent className="p-6">
                <div className="text-center">
                  <p className="text-red-600 mb-4">{error}</p>
                  {error.includes('preferences') && (
                    <Link to="/preferences">
                      <Button variant="outline">Set Your Preferences</Button>
                    </Link>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Meal Plan Display */}
          {mealPlan && mealPlan.days && (
            <div className="space-y-6">
              <div className="text-center">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Your Weekly Meal Plan</h2>
                <div className="flex flex-wrap justify-center gap-4 mt-3 mb-4">
                  <div className="bg-blue-50 text-blue-800 text-sm px-4 py-2 rounded-full">
                    Estimated Cost: {mealPlan.shopping_list?.estimated_cost ? `$${mealPlan.shopping_list.estimated_cost.toFixed(2)}` : 'N/A'}
                  </div>
                </div>
                <p className="text-gray-600">
                  {mealPlan.days.flatMap(day => day.meals || []).length} meals planned • 
                  {getNutritionValue(mealPlan.nutrition_summary?.daily_average?.calories)} avg calories/day
                </p>
              </div>

              {/* Meal Plan Days */}
              <div className="grid gap-6">
                {mealPlan.days.map((dayPlan: MealDay, index: number) => (
                  <Card key={dayPlan.day || index}>
                    <CardHeader>
                      <div className="flex justify-between items-center">
                        <CardTitle className="capitalize text-xl">
                          {dayPlan.day}
                          {dayPlan.date && (
                            <span className="ml-2 text-sm font-normal text-gray-500">
                              {new Date(dayPlan.date).toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}
                            </span>
                          )}
                        </CardTitle>
                        {dayPlan.daily_notes && (
                          <span className="text-sm text-gray-500 italic">{dayPlan.daily_notes}</span>
                        )}
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid md:grid-cols-3 gap-4">
                        {Object.entries(dayPlan.meals || {}).map(([mealType, meal]) => (
                          <div key={mealType} className="border rounded-lg p-4">
                            <div className="flex justify-between items-start mb-2">
                              <h4 className="font-semibold capitalize text-lg">{mealType}</h4>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleRegenerateMeal(dayPlan.day, mealType)}
                                className="p-1 h-8 w-8"
                              >
                                <RefreshCw className="h-4 w-4" />
                              </Button>
                            </div>
                            
                            <h5 className="font-medium text-gray-900 mb-1">{meal.name}</h5>
                            
                            <div className="text-xs space-y-1 mb-3">
                              <p><span className="font-medium">Cuisine:</span> {meal.cuisine || 'N/A'}</p>
                              <p><span className="font-medium">Prep Time:</span> {meal.prep_time}</p>
                              <p><span className="font-medium">Cook Time:</span> {meal.cook_time}</p>
                              <p><span className="font-medium">Difficulty:</span> {meal.difficulty}</p>
                              <p><span className="font-medium">Servings:</span> {meal.servings}</p>
                              
                              {meal.nutritional_highlights?.length > 0 && (
                                <div className="mt-1 pt-1 border-t border-gray-100">
                                  <p className="font-medium">Highlights:</p>
                                  <p className="text-xs">{meal.nutritional_highlights.join(', ')}</p>
                                </div>
                              )}
                            </div>

                            {meal.ingredients && (
                              <div className="mt-3">
                                <p className="text-xs font-medium mb-1">Ingredients:</p>
                                <ul className="text-xs text-gray-600 space-y-0.5">
                                  {(Array.isArray(meal.ingredients) ? meal.ingredients : [meal.ingredients])
                                    .slice(0, 3)
                                    .map((ingredient: any, idx: number) => {
                                      // Handle both string and object formats
                                      let ingredientText = ingredient;
                                      if (ingredient && typeof ingredient === 'object') {
                                        ingredientText = ingredient.name || 
                                                       (ingredient.amount ? `${ingredient.amount} ${ingredient.unit || ''} ${ingredient.name || ''}` : '');
                                      }
                                      return <li key={idx}>• {ingredientText}</li>;
                                    })}
                                  {Array.isArray(meal.ingredients) && meal.ingredients.length > 3 && (
                                    <li>• ... and {meal.ingredients.length - 3} more</li>
                                  )}
                                </ul>
                              </div>
                            )}

                            {meal.instructions && (
                              <div className="mt-3">
                                <p className="text-xs font-medium mb-1">Instructions:</p>
                                <ol className="text-xs text-gray-600 space-y-0.5">
                                  {(Array.isArray(meal.instructions) ? meal.instructions : [meal.instructions])
                                    .slice(0, 2)
                                    .map((instruction: any, idx: number) => (
                                      <li key={idx} className="pl-2">{(idx + 1)}. {instruction}</li>
                                    ))}
                                  {Array.isArray(meal.instructions) && meal.instructions.length > 2 && (
                                    <li className="pl-2 text-gray-500">... and {meal.instructions.length - 2} more steps</li>
                                  )}
                                </ol>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Initial State */}
          {!mealPlan && !error && !isGenerating && (
            <Card>
              <CardContent className="p-12 text-center">
                <ChefHat className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Ready to Plan Your Week?</h3>
                <p className="text-gray-600 mb-6">
                  Click "Generate New Meal Plan" to create a personalized weekly meal plan based on your preferences.
                </p>
                <Button onClick={handleGenerateMealPlan} size="lg">
                  <ChefHat className="mr-2 h-4 w-4" />
                  Get Started
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default MealPlannerPage; 