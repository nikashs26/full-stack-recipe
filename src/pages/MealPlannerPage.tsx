import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '@/hooks/use-toast';
import Header from '../components/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Loader2, ChefHat, Users, DollarSign, Clock, ShoppingCart, RefreshCw } from 'lucide-react';
import { Link } from 'react-router-dom';

interface MealPlanDay {
  day: string;
  date: string;
  breakfast: {
    name: string;
    ingredients: string[];
    cuisine?: string;
    cookingTime?: string;
    difficulty?: string;
  };
  lunch: {
    name: string;
    ingredients: string[];
    cuisine?: string;
    cookingTime?: string;
    difficulty?: string;
  };
  dinner: {
    name: string;
    ingredients: string[];
    cuisine?: string;
    cookingTime?: string;
    difficulty?: string;
  };
}

interface MealPlan {
  days: MealPlanDay[];
  shopping_list: string[];
  estimated_cost: string;
  generated_at: string;
  preferences_used?: any;
}

interface UserPreferences {
  dietaryRestrictions: string[];
  favoriteCuisines: string[];
  cookingSkillLevel: string;
  allergens: string[];
  healthGoals: string[];
  maxCookingTime: string;
}

const MealPlannerPage: React.FC = () => {
  const { isAuthenticated, user } = useAuth();
  const { toast } = useToast();
  
  // Form states
  const [weeklyBudget, setWeeklyBudget] = useState<string>('');
  const [servingAmount, setServingAmount] = useState<string>('');
  const [additionalRequirements, setAdditionalRequirements] = useState<string>('');
  
  // Meal plan states
  const [mealPlan, setMealPlan] = useState<MealPlan | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);
  
  // Load user preferences
  useEffect(() => {
    const loadPreferences = async () => {
      try {
        const response = await fetch('/api/preferences', {
          credentials: 'include'
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data.success) {
            setPreferences(data.preferences);
          }
        }
      } catch (error) {
        console.error('Error loading preferences:', error);
      }
    };
    
    if (isAuthenticated) {
      loadPreferences();
    }
  }, [isAuthenticated]);

  const generateMealPlan = async () => {
    if (!isAuthenticated) {
      toast({
        title: "Authentication Required",
        description: "Please sign in to generate meal plans.",
        variant: "destructive"
      });
      return;
    }

    if (!preferences) {
      toast({
        title: "Preferences Required",
        description: "Please set your dietary preferences first.",
        variant: "destructive"
      });
      return;
    }

    if (!weeklyBudget || !servingAmount) {
      toast({
        title: "Missing Information",
        description: "Please provide both weekly budget and serving amount.",
        variant: "destructive"
      });
      return;
    }

    setIsGenerating(true);

    try {
      // Enhanced preferences with budget and serving info
      const enhancedPreferences = {
        ...preferences,
        weeklyBudget: parseFloat(weeklyBudget),
        servingAmount: parseInt(servingAmount),
        additionalRequirements: additionalRequirements.trim() || undefined,
        planType: 'comprehensive'
      };

      const response = await fetch('/api/meal-plan/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          preferences: enhancedPreferences
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to generate meal plan: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success || data.plan) {
        const generatedPlan = data.plan || data;
        setMealPlan(generatedPlan);
        
        // Store in localStorage for shopping list access
        localStorage.setItem('current-meal-plan', JSON.stringify(generatedPlan));
        localStorage.setItem('agent-shopping-list', JSON.stringify({
          items: generatedPlan.shopping_list?.map((item: string) => ({
            name: item,
            category: 'Groceries',
            completed: false
          })) || [],
          estimated_cost: generatedPlan.estimated_cost || `$${weeklyBudget}`,
          generated_at: new Date().toISOString(),
          meal_plan_id: 'current'
        }));
        
        toast({
          title: "Meal Plan Generated!",
          description: `Your personalized weekly meal plan is ready! Estimated cost: ${generatedPlan.estimated_cost || `$${weeklyBudget}`}`,
        });
      } else {
        throw new Error(data.error || 'Unknown error generating meal plan');
      }
    } catch (error) {
      console.error('Error generating meal plan:', error);
      toast({
        title: "Generation Failed",
        description: error instanceof Error ? error.message : "Failed to generate meal plan. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const regenerateMealPlan = () => {
    setMealPlan(null);
    generateMealPlan();
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="pt-24 md:pt-28">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
            <Card className="text-center">
              <CardHeader>
                <div className="flex justify-center mb-4">
                  <ChefHat className="h-12 w-12 text-orange-500" />
                </div>
                <CardTitle className="text-2xl">AI Meal Planner</CardTitle>
                <CardDescription>
                  Sign in to generate personalized weekly meal plans with budget optimization
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
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              🤖 AI Meal Planner
            </h1>
            <p className="text-gray-600">
              Generate personalized weekly meal plans with budget optimization and shopping lists
            </p>
          </div>

          {!mealPlan ? (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ChefHat className="h-5 w-5" />
                  Meal Plan Preferences
                </CardTitle>
                <CardDescription>
                  Tell us about your budget and household size for a personalized meal plan
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <Label htmlFor="budget" className="flex items-center gap-2">
                      <DollarSign className="h-4 w-4" />
                      Weekly Budget (USD)
                    </Label>
                    <Input
                      id="budget"
                      type="number"
                      placeholder="50"
                      value={weeklyBudget}
                      onChange={(e) => setWeeklyBudget(e.target.value)}
                      min="10"
                      max="500"
                    />
                    <p className="text-sm text-gray-500">How much do you want to spend on groceries per week?</p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="serving" className="flex items-center gap-2">
                      <Users className="h-4 w-4" />
                      Serving Amount (People)
                    </Label>
                    <Select value={servingAmount} onValueChange={setServingAmount}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select serving size" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1">1 person</SelectItem>
                        <SelectItem value="2">2 people</SelectItem>
                        <SelectItem value="3">3 people</SelectItem>
                        <SelectItem value="4">4 people</SelectItem>
                        <SelectItem value="5">5 people</SelectItem>
                        <SelectItem value="6">6 people</SelectItem>
                        <SelectItem value="8">8+ people</SelectItem>
                      </SelectContent>
                    </Select>
                    <p className="text-sm text-gray-500">How many people will you be cooking for?</p>
                  </div>
                </div>

                {preferences && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold">Your Current Preferences</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {preferences.dietaryRestrictions && preferences.dietaryRestrictions.length > 0 && (
                        <div>
                          <Label className="text-sm font-medium">Dietary Restrictions</Label>
                          <div className="flex flex-wrap gap-2 mt-1">
                            {preferences.dietaryRestrictions.map((diet, index) => (
                              <Badge key={index} variant="secondary">{diet}</Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {preferences.favoriteCuisines && preferences.favoriteCuisines.length > 0 && (
                        <div>
                          <Label className="text-sm font-medium">Favorite Cuisines</Label>
                          <div className="flex flex-wrap gap-2 mt-1">
                            {preferences.favoriteCuisines.map((cuisine, index) => (
                              <Badge key={index} variant="outline">{cuisine}</Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      <div>
                        <Label className="text-sm font-medium">Cooking Skill</Label>
                        <p className="text-sm text-gray-600 mt-1 capitalize">{preferences.cookingSkillLevel}</p>
                      </div>
                      
                      <div>
                        <Label className="text-sm font-medium">Max Cooking Time</Label>
                        <p className="text-sm text-gray-600 mt-1">{preferences.maxCookingTime}</p>
                      </div>
                    </div>
                    
                    <Link to="/preferences">
                      <Button variant="outline" size="sm">Update Preferences</Button>
                    </Link>
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="additional">Additional Requirements (Optional)</Label>
                  <Textarea
                    id="additional"
                    placeholder="e.g., low sodium, high protein, meal prep friendly, specific ingredients to avoid..."
                    value={additionalRequirements}
                    onChange={(e) => setAdditionalRequirements(e.target.value)}
                    rows={3}
                  />
                </div>

                <Button 
                  onClick={generateMealPlan} 
                  disabled={isGenerating || !weeklyBudget || !servingAmount}
                  size="lg"
                  className="w-full"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Generating Your Meal Plan...
                    </>
                  ) : (
                    <>
                      <ChefHat className="mr-2 h-4 w-4" />
                      Generate AI Meal Plan
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-6">
              {/* Meal Plan Header */}
              <Card>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-2xl">Your Weekly Meal Plan</CardTitle>
                      <CardDescription>
                        Generated for {servingAmount} people with a ${weeklyBudget} budget
                      </CardDescription>
                    </div>
                    <div className="flex gap-2">
                      <Button onClick={regenerateMealPlan} variant="outline" size="sm">
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Regenerate
                      </Button>
                      <Link to="/shopping-list">
                        <Button size="sm">
                          <ShoppingCart className="h-4 w-4 mr-2" />
                          Shopping List
                        </Button>
                      </Link>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="flex items-center gap-2">
                      <DollarSign className="h-5 w-5 text-green-600" />
                      <span className="font-medium">Estimated Cost: {mealPlan.estimated_cost}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Users className="h-5 w-5 text-blue-600" />
                      <span className="font-medium">Serves: {servingAmount} people</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <ShoppingCart className="h-5 w-5 text-orange-600" />
                      <span className="font-medium">{mealPlan.shopping_list?.length || 0} ingredients</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Weekly Meal Plan */}
              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                {mealPlan.days?.map((day, index) => (
                  <Card key={day.day} className="h-fit">
                    <CardHeader>
                      <CardTitle className="text-lg">{day.day}</CardTitle>
                      {day.date && <CardDescription>{day.date}</CardDescription>}
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {/* Breakfast */}
                      <div className="border-l-4 border-yellow-400 pl-3">
                        <h4 className="font-semibold text-yellow-700">Breakfast</h4>
                        <p className="font-medium">{day.breakfast.name}</p>
                        {day.breakfast.cuisine && (
                          <Badge variant="outline" className="text-xs mt-1">{day.breakfast.cuisine}</Badge>
                        )}
                        {day.breakfast.cookingTime && (
                          <p className="text-xs text-gray-500 flex items-center gap-1 mt-1">
                            <Clock className="h-3 w-3" />
                            {day.breakfast.cookingTime}
                          </p>
                        )}
                      </div>

                      {/* Lunch */}
                      <div className="border-l-4 border-blue-400 pl-3">
                        <h4 className="font-semibold text-blue-700">Lunch</h4>
                        <p className="font-medium">{day.lunch.name}</p>
                        {day.lunch.cuisine && (
                          <Badge variant="outline" className="text-xs mt-1">{day.lunch.cuisine}</Badge>
                        )}
                        {day.lunch.cookingTime && (
                          <p className="text-xs text-gray-500 flex items-center gap-1 mt-1">
                            <Clock className="h-3 w-3" />
                            {day.lunch.cookingTime}
                          </p>
                        )}
                      </div>

                      {/* Dinner */}
                      <div className="border-l-4 border-green-400 pl-3">
                        <h4 className="font-semibold text-green-700">Dinner</h4>
                        <p className="font-medium">{day.dinner.name}</p>
                        {day.dinner.cuisine && (
                          <Badge variant="outline" className="text-xs mt-1">{day.dinner.cuisine}</Badge>
                        )}
                        {day.dinner.cookingTime && (
                          <p className="text-xs text-gray-500 flex items-center gap-1 mt-1">
                            <Clock className="h-3 w-3" />
                            {day.dinner.cookingTime}
                          </p>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MealPlannerPage; 