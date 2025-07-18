import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '@/hooks/use-toast';
import Header from '../components/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ChefHat, Loader2, RefreshCw, Settings, Lock } from 'lucide-react';
import { generateMealPlan, regenerateMeal, MealPlan } from '../services/mealPlannerService';

const MealPlannerPage: React.FC = () => {
  const { isAuthenticated, isLoading: authLoading, user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [mealPlan, setMealPlan] = useState<MealPlan | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    setIsGenerating(true);
    setError(null);
    
    try {
      const newMealPlan = await generateMealPlan();
      setMealPlan(newMealPlan);
      toast({
        title: "Meal Plan Generated!",
        description: "Your personalized weekly meal plan is ready.",
      });
    } catch (error: any) {
      console.error('Error generating meal plan:', error);
      setError(error.message);
      
      if (error.message.includes('preferences')) {
        toast({
          title: "Preferences Required",
          description: error.message,
          variant: "destructive"
        });
      } else {
        toast({
          title: "Generation Failed",
          description: error.message || 'Failed to generate meal plan',
          variant: "destructive"
        });
      }
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
                <p className="text-gray-600">Generated using {mealPlan.plan_type === 'llm_generated' ? 'AI' : 'Rule-based system'}</p>
              </div>

              <div className="grid gap-6">
                {mealPlan.days.map((dayPlan: any, index: number) => (
                  <Card key={dayPlan.day || index}>
                    <CardHeader>
                      <CardTitle className="capitalize text-xl">{dayPlan.day}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid md:grid-cols-3 gap-4">
                        {Object.entries(dayPlan.meals || {}).map(([mealType, meal]: [string, any]) => (
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
                            <p className="text-sm text-gray-600 mb-2">{meal.description}</p>
                            
                            <div className="text-xs space-y-1">
                              <p><span className="font-medium">Cuisine:</span> {meal.cuisine}</p>
                              <p><span className="font-medium">Time:</span> {meal.cookingTime || meal.cook_time || meal.prep_time}</p>
                              <p><span className="font-medium">Difficulty:</span> {meal.difficulty}</p>
                            </div>

                            {meal.ingredients && (
                              <div className="mt-3">
                                <p className="text-xs font-medium mb-1">Ingredients:</p>
                                <ul className="text-xs text-gray-600 space-y-0.5">
                                  {meal.ingredients.slice(0, 3).map((ingredient: string, idx: number) => (
                                    <li key={idx}>• {ingredient}</li>
                                  ))}
                                  {meal.ingredients.length > 3 && (
                                    <li>• ... and {meal.ingredients.length - 3} more</li>
                                  )}
                                </ul>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Action Buttons for Generated Plan */}
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