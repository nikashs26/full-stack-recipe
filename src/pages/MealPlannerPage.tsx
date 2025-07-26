import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '@/hooks/use-toast';
import Header from '../components/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ChefHat, Loader2, RefreshCw, Settings, Lock, DollarSign, Plus, X } from 'lucide-react';
import { generateMealPlan, regenerateMeal, type MealPlanData, type MealDay, type Meal, type NutritionSummary } from '../services/mealPlannerService';

const MealPlannerPage: React.FC = () => {
  const { isAuthenticated, isLoading: authLoading, user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [mealPlan, setMealPlan] = useState<MealPlanData | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);
  const [budget, setBudget] = useState<number | ''>('');
  const [dietaryGoals, setDietaryGoals] = useState<string[]>([]);
  const [customDietInput, setCustomDietInput] = useState('');
  const [currency, setCurrency] = useState('$');
  
  // Meal inclusion preferences
  const [includeBreakfast, setIncludeBreakfast] = useState(true);
  const [includeLunch, setIncludeLunch] = useState(true);
  const [includeDinner, setIncludeDinner] = useState(true);
  const [includeSnacks, setIncludeSnacks] = useState(true);
  
  // Macro targets
  const [targetCalories, setTargetCalories] = useState<number | ''>(2000);
  const [targetProtein, setTargetProtein] = useState<number | ''>(150);
  const [targetCarbs, setTargetCarbs] = useState<number | ''>(200);
  const [targetFat, setTargetFat] = useState<number | ''>(65);
  
  const commonDietGoals = [
    'High Protein',
    'Low Carb',
    'Keto',
    'Paleo',
    'Vegetarian',
    'Vegan',
    'Mediterranean',
    'High Fiber',
    'Low Calorie',
    'Balanced'
  ];

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

  const toggleDietGoal = (goal: string) => {
    setDietaryGoals(prev => 
      prev.includes(goal)
        ? prev.filter(g => g !== goal)
        : [...prev, goal]
    );
  };

  const addCustomDietGoal = () => {
    if (customDietInput.trim() && !dietaryGoals.includes(customDietInput.trim())) {
      setDietaryGoals(prev => [...prev, customDietInput.trim()]);
      setCustomDietInput('');
    }
  };

  const removeDietGoal = (goal: string) => {
    setDietaryGoals(prev => prev.filter(g => g !== goal));
  };

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
        budget: budget || undefined,
        dietaryGoals: dietaryGoals.length > 0 ? dietaryGoals : undefined,
        currency: currency,
        mealPreferences: {
          includeBreakfast,
          includeLunch,
          includeDinner,
          includeSnacks
        },
        nutritionTargets: {
          calories: targetCalories || 2000,
          protein: targetProtein || 150,
          carbs: targetCarbs || 200,
          fat: targetFat || 65
        }
      });
      
      setMealPlan(plan);
      
      toast({
        title: "Success!",
        description: `Your personalized weekly meal plan ${budget ? `(Budget: ${currency}${budget})` : ''} is ready.`,
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
    if (!mealPlan?.days) return;
    
    try {
      await regenerateMeal(day, mealType);
      toast({
        title: "Coming Soon",
        description: "Individual meal regeneration will be available soon!",
      });
    } catch (error: any) {
      console.error('Error regenerating meal:', error);
      toast({
        title: "Regeneration Failed",
        description: error.message || 'Failed to regenerate meal',
        variant: "destructive"
      });
    }
  };

  const renderNutritionalInfo = () => {
    if (!mealPlan?.nutrition_summary) return null;
    
    const nutritionSummary = mealPlan.nutrition_summary;
    const dailyAverage = nutritionSummary?.daily_average;
    const weeklyTotals = nutritionSummary?.weekly_totals;
    const mealInclusions = nutritionSummary?.meal_inclusions || {};
    const dietaryConsiderations = nutritionSummary?.dietary_considerations || [];
    
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
              {!dailyAverage ? (
                <p className="text-sm text-gray-500">No daily average data available</p>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-orange-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-orange-600">
                      {dailyAverage.calories || 'N/A'}
                    </div>
                    <div className="text-sm text-gray-500">Calories</div>
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">
                      {dailyAverage.protein || 'N/A'}
                    </div>
                    <div className="text-sm text-gray-500">Protein</div>
                  </div>
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">
                      {dailyAverage.carbs || 'N/A'}
                    </div>
                    <div className="text-sm text-gray-500">Carbs</div>
                  </div>
                  <div className="bg-purple-50 p-4 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600">
                      {dailyAverage.fat || 'N/A'}
                    </div>
                    <div className="text-sm text-gray-500">Fat</div>
                  </div>
                </div>
              )}
            </div>
            
            <div className="mt-6">
              <h4 className="font-medium mb-2">Weekly Totals</h4>
              {!weeklyTotals ? (
                <p className="text-sm text-gray-500">No weekly total data available</p>
              ) : (
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="text-lg font-semibold">
                      {weeklyTotals.calories ? `${weeklyTotals.calories} cal` : 'N/A'}
                    </div>
                    <div className="text-sm text-gray-500">Total Calories</div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="text-lg font-semibold">
                      {weeklyTotals.protein || 'N/A'}
                    </div>
                    <div className="text-sm text-gray-500">Total Protein</div>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="text-lg font-semibold">
                      {weeklyTotals.carbs || 'N/A'}
                    </div>
                    <div className="text-sm text-gray-500">Total Carbs</div>
                  </div>
                </div>
              )}
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
                    {meal}: {included ? 'Included' : 'Excluded'}
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
              <h1 className="text-3xl font-bold text-gray-900">🤖 AI Meal Planner</h1>
            </div>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Welcome back, {user?.full_name || user?.email}! Generate personalized weekly meal plans based on your preferences.
            </p>
          </div>

          {/* Advanced Options Toggle */}
          <div className="text-center mb-6">
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
              className="text-sm text-primary hover:bg-primary/10"
            >
              {showAdvancedOptions ? 'Hide' : 'Show'} Advanced Options
              {showAdvancedOptions ? (
                <X className="ml-2 h-4 w-4" />
              ) : (
                <Plus className="ml-2 h-4 w-4" />
              )}
            </Button>
          </div>

          {/* Advanced Options Form */}
          {showAdvancedOptions && (
            <Card className="mb-8 p-6 bg-white/50 backdrop-blur-sm">
              <div className="grid md:grid-cols-2 gap-6">
                {/* Budget Section */}
                <div>
                  <h3 className="font-medium mb-3 flex items-center">
                    <DollarSign className="h-4 w-4 mr-2" />
                    Weekly Budget
                  </h3>
                  <div className="flex items-center">
                    <select 
                      value={currency}
                      onChange={(e) => setCurrency(e.target.value)}
                      className="h-10 rounded-l-md border-r-0 border-gray-300 bg-gray-50 px-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                    >
                      <option value="$">$ USD</option>
                      <option value="€">€ EUR</option>
                      <option value="£">£ GBP</option>
                      <option value="¥">¥ JPY</option>
                    </select>
                    <input
                      type="number"
                      min="0"
                      step="10"
                      value={budget}
                      onChange={(e) => setBudget(e.target.value ? parseFloat(e.target.value) : '')}
                      placeholder="Enter your weekly budget"
                      className="h-10 flex-1 rounded-r-md border-l-0 border-gray-300 px-3 text-sm focus:ring-2 focus:ring-primary/50 focus:outline-none"
                    />
                  </div>
                  <p className="mt-2 text-xs text-gray-500">
                    {budget ? `~${currency}${(Number(budget) / 21).toFixed(2)} per meal` : 'Leave empty for no budget limit'}
                  </p>
                </div>

                {/* Meal Inclusions */}
                <div>
                  <h3 className="font-medium mb-3">Meal Inclusions</h3>
                  <div className="grid grid-cols-2 gap-3 mb-4">
                    <label className="flex items-center space-x-2">
                      <input 
                        type="checkbox" 
                        checked={includeBreakfast}
                        onChange={(e) => setIncludeBreakfast(e.target.checked)}
                        className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                      />
                      <span>Breakfast</span>
                    </label>
                    <label className="flex items-center space-x-2">
                      <input 
                        type="checkbox" 
                        checked={includeLunch}
                        onChange={(e) => setIncludeLunch(e.target.checked)}
                        className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                      />
                      <span>Lunch</span>
                    </label>
                    <label className="flex items-center space-x-2">
                      <input 
                        type="checkbox" 
                        checked={includeDinner}
                        onChange={(e) => setIncludeDinner(e.target.checked)}
                        className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                      />
                      <span>Dinner</span>
                    </label>
                    <label className="flex items-center space-x-2">
                      <input 
                        type="checkbox" 
                        checked={includeSnacks}
                        onChange={(e) => setIncludeSnacks(e.target.checked)}
                        className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary"
                      />
                      <span>Snacks</span>
                    </label>
                  </div>
                </div>

                {/* Nutrition Targets */}
                <div>
                  <h3 className="font-medium mb-3">Daily Nutrition Targets</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Calories</label>
                      <input
                        type="number"
                        value={targetCalories}
                        onChange={(e) => setTargetCalories(e.target.value ? parseInt(e.target.value) : '')}
                        className="w-full h-10 rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary"
                        min="0"
                        step="50"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Protein (g)</label>
                      <input
                        type="number"
                        value={targetProtein}
                        onChange={(e) => setTargetProtein(e.target.value ? parseInt(e.target.value) : '')}
                        className="w-full h-10 rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary"
                        min="0"
                        step="5"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Carbs (g)</label>
                      <input
                        type="number"
                        value={targetCarbs}
                        onChange={(e) => setTargetCarbs(e.target.value ? parseInt(e.target.value) : '')}
                        className="w-full h-10 rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary"
                        min="0"
                        step="5"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Fat (g)</label>
                      <input
                        type="number"
                        value={targetFat}
                        onChange={(e) => setTargetFat(e.target.value ? parseInt(e.target.value) : '')}
                        className="w-full h-10 rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary"
                        min="0"
                        step="1"
                      />
                    </div>
                  </div>
                </div>

                {/* Diet Goals Section */}
                <div className="md:col-span-2">
                  <h3 className="font-medium mb-3">Dietary Goals</h3>
                  <div className="flex flex-wrap gap-2 mb-3">
                    {commonDietGoals.map((goal) => (
                      <button
                        key={goal}
                        type="button"
                        onClick={() => toggleDietGoal(goal)}
                        className={`text-xs px-3 py-1 rounded-full border ${
                          dietaryGoals.includes(goal)
                            ? 'bg-primary/10 border-primary text-primary'
                            : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50'
                        }`}
                      >
                        {goal}
                      </button>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={customDietInput}
                      onChange={(e) => setCustomDietInput(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && addCustomDietGoal()}
                      placeholder="Add custom goal..."
                      className="flex-1 h-10 rounded-md border border-gray-300 px-3 text-sm focus:ring-2 focus:ring-primary/50 focus:outline-none"
                    />
                    <Button 
                      type="button" 
                      variant="outline" 
                      size="sm"
                      onClick={addCustomDietGoal}
                      className="h-10"
                    >
                      Add
                    </Button>
                  </div>
                  
                  {/* Selected Goals */}
                  {dietaryGoals.length > 0 && (
                    <div className="mt-3">
                      <h4 className="text-xs font-medium text-gray-500 mb-1">Selected Goals:</h4>
                      <div className="flex flex-wrap gap-2">
                        {dietaryGoals.map((goal) => (
                          <span 
                            key={goal}
                            className="inline-flex items-center text-xs bg-primary/10 text-primary rounded-full px-3 py-1"
                          >
                            {goal}
                            <button 
                              type="button"
                              onClick={() => removeDietGoal(goal)}
                              className="ml-1.5 text-primary/70 hover:text-primary"
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </Card>
          )}

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
                  <div className="bg-green-50 text-green-800 text-sm px-4 py-2 rounded-full flex items-center">
                    <DollarSign className="h-4 w-4 mr-1" />
                    Budget: {currency}{budget || 'Not specified'}
                  </div>
                  <div className="bg-blue-50 text-blue-800 text-sm px-4 py-2 rounded-full">
                    Estimated Cost: {mealPlan.shopping_list?.estimated_cost ? `${currency}${mealPlan.shopping_list.estimated_cost.toFixed(2)}` : 'N/A'}
                  </div>
                  {dietaryGoals.length > 0 && (
                    <div className="bg-purple-50 text-purple-800 text-sm px-4 py-2 rounded-full">
                      {dietaryGoals.join(', ')}
                    </div>
                  )}
                </div>
                <p className="text-gray-600">
                  {mealPlan.days.flatMap(day => day.meals || []).length} meals planned • 
                  {mealPlan.nutrition_summary?.daily_average?.calories || 'N/A'} avg calories/day
                </p>
              </div>

              {/* Nutrition Summary */}
              {renderNutritionalInfo()}

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
                                    .map((ingredient: string, idx: number) => (
                                      <li key={idx}>• {ingredient}</li>
                                    ))}
                                  {Array.isArray(meal.ingredients) && meal.ingredients.length > 3 && (
                                    <li>• ... and {meal.ingredients.length - 3} more</li>
                                  )}
                                </ul>
                              </div>
                            )}

                            {meal.instructions && (
                              <div className="mt-3">
                                <p className="text-xs font-medium mb-1">Instructions:</p>
                                <ol className="text-xs text-gray-600 space-y-1 list-decimal list-inside">
                                  {(Array.isArray(meal.instructions) ? meal.instructions : [meal.instructions])
                                    .slice(0, 2)
                                    .map((step: string, idx: number) => (
                                      <li key={idx} className="truncate">{step}</li>
                                    ))}
                                  {Array.isArray(meal.instructions) && meal.instructions.length > 2 && (
                                    <li>... and {meal.instructions.length - 2} more steps</li>
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
              <div className="flex flex-col sm:flex-row gap-4 justify-center pt-8">
                <Button 
                  onClick={handleGenerateMealPlan} 
                  disabled={isGenerating}
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  <RefreshCw className="h-4 w-4" />
                  Generate Another Plan
                </Button>
                
                <Link to="/shopping-list">
                  <Button className="flex items-center gap-2">
                    🛒 Generate Shopping List
                  </Button>
                </Link>
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