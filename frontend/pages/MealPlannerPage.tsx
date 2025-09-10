import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '@/hooks/use-toast';
import Header from '../components/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ChefHat, Loader2, RefreshCw, Settings, Lock, History, X, Clock, ChevronLeft, ChevronRight, AlertCircle } from 'lucide-react';
import { generateMealPlan, regenerateMeal, saveMealPlanToHistory, type MealPlanData, type MealDay, type Meal } from '../services/mealPlannerService';
import MealPlannerAdvancedSettings, { type MealPlannerSettings } from '../components/MealPlannerAdvancedSettings';
import MealPlanHistory from '../components/MealPlanHistory';

const MealPlannerPage: React.FC = () => {
  const { isAuthenticated, isLoading: authLoading, user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  // Helper function to format time
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return mins > 0 ? `${mins}:${secs.toString().padStart(2, '0')}` : `${secs}s`;
  };

  const [mealPlan, setMealPlan] = useState<MealPlanData | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [advancedSettingsOpen, setAdvancedSettingsOpen] = useState(false);
  const [showHistory, setShowHistory] = useState(true); // Default to visible
  const [selectedHistoryPlan, setSelectedHistoryPlan] = useState<MealPlanData | null>(null);
  const [abortController, setAbortController] = useState<AbortController | null>(null);
  const [estimatedTime, setEstimatedTime] = useState<number>(0);
  const [elapsedTime, setElapsedTime] = useState<number>(0);
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

  // Timer for elapsed time during generation
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    
    if (isGenerating) {
      setElapsedTime(0);
      interval = setInterval(() => {
        setElapsedTime(prev => prev + 1);
      }, 1000);
    } else {
      setElapsedTime(0);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isGenerating]);

  const handleGenerateMealPlan = async () => {
    if (!isAuthenticated) {
      toast({
        title: "Authentication Required",
        description: "Please sign in to generate a meal plan.",
        variant: "destructive"
      });
      return;
    }

    // Create abort controller for cancellation
    const controller = new AbortController();
    setAbortController(controller);
    setIsGenerating(true);
    setError(null);
    
    // Calculate estimated time based on complexity
    const baseTime = 60; // Base time in seconds
    const complexityMultiplier = mealPlannerSettings.includeSnacks ? 1.3 : 1.0;
    const calorieMultiplier = mealPlannerSettings.targetCalories > 3000 ? 1.2 : 1.0;
    const estimatedSeconds = Math.round(baseTime * complexityMultiplier * calorieMultiplier);
    setEstimatedTime(estimatedSeconds);
    
    try {
      const plan = await generateMealPlan({
        nutritionTargets: {
          targetCalories: mealPlannerSettings.targetCalories,
          targetProtein: mealPlannerSettings.targetProtein,
          targetCarbs: mealPlannerSettings.targetCarbs,
          targetFat: mealPlannerSettings.targetFat,
          includeSnacks: mealPlannerSettings.includeSnacks
        }
      }, controller.signal);
      
      setMealPlan(plan);
      
      // Save meal plan to history
      try {
        await saveMealPlanToHistory(plan, {
          targetCalories: mealPlannerSettings.targetCalories,
          targetProtein: mealPlannerSettings.targetProtein,
          targetCarbs: mealPlannerSettings.targetCarbs,
          targetFat: mealPlannerSettings.targetFat,
          includeSnacks: mealPlannerSettings.includeSnacks
        });
      } catch (error) {
        console.warn('Failed to save meal plan to history:', error);
      }
      
      toast({
        title: "Success!",
        description: `Your personalized weekly meal plan is ready with ${mealPlannerSettings.targetCalories} calories/day.`,
      });
      
      return plan;
    } catch (error) {
      console.error('Error generating meal plan:', error);
      
      // Check if it was cancelled
      if (error instanceof Error && error.name === 'AbortError') {
        toast({
          title: "Cancelled",
          description: "Meal plan generation was cancelled.",
          variant: "default"
        });
        return;
      }
      
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
      setAbortController(null);
      setEstimatedTime(0);
    }
  };

  const handleCancelGeneration = () => {
    if (abortController) {
      abortController.abort();
      setIsGenerating(false);
      setAbortController(null);
      setEstimatedTime(0);
      
      toast({
        title: "Cancelled",
        description: "Meal plan generation has been cancelled.",
        variant: "default"
      });
    }
  };

  const handleRegenerateMeal = async (day: string, mealType: string) => {
    try {
      await regenerateMeal(day, mealType);
      
      // Save updated meal plan to history
      if (mealPlan) {
        try {
          await saveMealPlanToHistory(mealPlan, {
            targetCalories: mealPlannerSettings.targetCalories,
            targetProtein: mealPlannerSettings.targetProtein,
            targetCarbs: mealPlannerSettings.targetCarbs,
            targetFat: mealPlannerSettings.targetFat,
            includeSnacks: mealPlannerSettings.includeSnacks
          });
        } catch (error) {
          console.warn('Failed to save regenerated meal plan to history:', error);
        }
      }
      
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

  const handleSelectHistoryPlan = (plan: MealPlanData) => {
    setSelectedHistoryPlan(plan);
    setMealPlan(plan);
    toast({
      title: "Meal Plan Loaded",
      description: "Previous meal plan has been loaded from history.",
    });
  };

  const handleBackToCurrentPlan = () => {
    setSelectedHistoryPlan(null);
    setMealPlan(null);
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

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="pt-24 md:pt-28">
        <div className="flex">
          {/* Side History Panel */}
          <div className={`${showHistory ? 'w-80' : 'w-0'} transition-all duration-300 ease-in-out overflow-hidden`}>
            {showHistory && (
              <div className="h-screen overflow-y-auto border-r border-gray-200 bg-white p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">Meal Plan History</h3>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowHistory(false)}
                    className="p-1 h-8 w-8"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
                <MealPlanHistory 
                  onSelectPlan={handleSelectHistoryPlan}
                  className="h-full"
                />
              </div>
            )}
          </div>

          {/* Main Content */}
          <div className="flex-1 transition-all duration-300 ease-in-out">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
              {/* Header Section */}
              <div className="text-center mb-8">
                <div className="flex items-center justify-center gap-2 mb-4">
                  {!showHistory && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setShowHistory(true)}
                      className="p-2 h-10 w-10"
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  )}
                  <h1 className="text-3xl text-gray-900">AI Meal Planner</h1>
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
                {!isGenerating ? (
                  <>
                    <Button 
                      onClick={handleGenerateMealPlan} 
                      size="lg"
                      className="flex items-center gap-2"
                    >
                      <ChefHat className="h-4 w-4" />
                      Generate New Meal Plan
                    </Button>
                    
                    <Button 
                      onClick={() => setShowHistory(!showHistory)}
                      variant="outline" 
                      size="lg" 
                      className="flex items-center gap-2"
                    >
                      <History className="h-4 w-4" />
                      {showHistory ? 'Hide History' : 'View History'}
                    </Button>
                    
                    <Link to="/preferences">
                      <Button variant="outline" size="lg" className="flex items-center gap-2">
                        <Settings className="h-4 w-4" />
                        Update Preferences
                      </Button>
                    </Link>
                  </>
                ) : (
                  <div className="flex flex-col items-center gap-4">
                    {/* Progress and time display */}
                    <div className="flex items-center gap-4 text-center">
                      <div className="flex items-center gap-2">
                        <Loader2 className="h-5 w-5 animate-spin text-orange-500" />
                        <span className="text-lg font-medium text-gray-900">Generating your meal plan...</span>
                      </div>
                    </div>
                    
                    {/* Progress bar */}
                    <div className="w-80 max-w-full">
                      <div className="flex justify-between text-xs text-gray-600 mb-1">
                        <span>Progress</span>
                        <span>{Math.min(Math.round((elapsedTime / estimatedTime) * 100), 100)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-orange-500 h-2 rounded-full transition-all duration-1000 ease-out"
                          style={{ 
                            width: `${Math.min((elapsedTime / estimatedTime) * 100, 100)}%` 
                          }}
                        ></div>
                      </div>
                    </div>

                    {/* Time information */}
                    <div className="flex items-center gap-6 text-sm text-gray-600">
                      <div className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        <span>Elapsed: {formatTime(elapsedTime)}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <span>Estimated: {formatTime(estimatedTime)}</span>
                      </div>
                      <div className="text-xs bg-gray-100 px-2 py-1 rounded">
                        {elapsedTime > estimatedTime ? 'Almost done...' : 
                         elapsedTime > estimatedTime * 0.8 ? 'Nearly finished...' : 
                         'Processing...'}
                      </div>
                    </div>
                    
                    {/* Cancel button */}
                    <Button 
                      onClick={handleCancelGeneration}
                      variant="outline" 
                      size="lg"
                      className="flex items-center gap-2 border-red-200 text-red-600 hover:bg-red-50"
                    >
                      <X className="h-4 w-4" />
                      Cancel Generation
                    </Button>
                  </div>
                )}
              </div>

              {/* Error Display */}
              {error && (
                <Card className="mb-8 border-red-200">
                  <CardContent className="p-6">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertCircle className="h-5 w-5 text-red-500" />
                      <h3 className="text-lg font-semibold text-red-800">Error Generating Meal Plan</h3>
                    </div>
                    <p className="text-red-600 mb-4">{error}</p>
                    {error.includes('preferences') && (
                      <Link to="/preferences">
                        <Button variant="outline">Set Your Preferences</Button>
                      </Link>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Back to Current Plan Button */}
              {selectedHistoryPlan && (
                <div className="mb-8">
                  <Button
                    onClick={handleBackToCurrentPlan}
                    variant="outline"
                    className="flex items-center gap-2"
                  >
                    <ChevronLeft className="h-4 w-4" />
                    Back to Current Plan
                  </Button>
                </div>
              )}

              {/* Meal Plan Display */}
              {mealPlan && mealPlan.days && (
                <div className="space-y-6">
                  <div className="text-center">
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">
                      {selectedHistoryPlan ? 'Historical Meal Plan' : 'Your Weekly Meal Plan'}
                    </h2>
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
                                  {!selectedHistoryPlan && (
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => handleRegenerateMeal(dayPlan.day, mealType)}
                                      className="p-1 h-8 w-8"
                                    >
                                      <RefreshCw className="h-4 w-4" />
                                    </Button>
                                  )}
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
      </div>
    </div>
  );
};

export default MealPlannerPage; 