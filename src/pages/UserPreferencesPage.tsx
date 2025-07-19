import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '@/hooks/use-toast';
import Header from '../components/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Form, FormField, FormItem, FormLabel } from '@/components/ui/form';
import { Settings, Save, Loader2, Lock, ChefHat, Utensils } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Info, DollarSign, Users } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { loadUserPreferences, saveUserPreferences, UserPreferences } from '../services/preferencesService';

const dietaryOptions = [
  { id: 'vegetarian', label: 'Vegetarian', description: 'No meat or fish' },
  { id: 'vegan', label: 'Vegan', description: 'No animal products' },
  { id: 'gluten-free', label: 'Gluten Free', description: 'No wheat, barley, or rye' },
  { id: 'dairy-free', label: 'Dairy Free', description: 'No milk products' },
  { id: 'keto', label: 'Keto', description: 'Low carb, high fat' },
  { id: 'paleo', label: 'Paleo', description: 'No processed foods' }
];

const cuisineOptions = [
  { id: 'italian', label: 'Italian', description: 'Pasta, pizza, regional flavors' },
  { id: 'mexican', label: 'Mexican', description: 'Spicy, flavorful, corn and flour-based dishes' },
  { id: 'indian', label: 'Indian', description: 'Curry, aromatic spices, diverse flavors' },
  { id: 'chinese', label: 'Chinese', description: 'Stir-fry, rice, diverse regional cuisines' },
  { id: 'japanese', label: 'Japanese', description: 'Sushi, ramen, delicate flavors' },
  { id: 'thai', label: 'Thai', description: 'Sweet, sour, spicy balance' },
  { id: 'mediterranean', label: 'Mediterranean', description: 'Olive oil, fresh vegetables, seafood' },
  { id: 'french', label: 'French', description: 'Classic techniques, rich sauces' },
  { id: 'greek', label: 'Greek', description: 'Olive oil, feta, fresh herbs' },
  { id: 'spanish', label: 'Spanish', description: 'Paella, tapas, olive oil' },
  { id: 'korean', label: 'Korean', description: 'Kimchi, barbecue, fermented foods' },
  { id: 'vietnamese', label: 'Vietnamese', description: 'Fresh herbs, fish sauce, balance' },
  { id: 'american', label: 'American', description: 'Comfort food, grilled dishes, fusion' },
  { id: 'british', label: 'British', description: 'Hearty dishes, pies, roasts' },
  { id: 'irish', label: 'Irish', description: 'Stews, potato dishes, breads' },
  { id: 'caribbean', label: 'Caribbean', description: 'Spicy, tropical flavors, seafood' },
  { id: 'moroccan', label: 'Moroccan', description: 'Tagines, couscous, aromatic spices' }
];

const allergenOptions = [
  { id: 'nuts', label: 'Nuts', description: 'Tree nuts and peanuts' },
  { id: 'shellfish', label: 'Shellfish', description: 'Shrimp, crab, lobster' },
  { id: 'dairy', label: 'Dairy', description: 'Milk and milk products' },
  { id: 'eggs', label: 'Eggs', description: 'All egg products' },
  { id: 'soy', label: 'Soy', description: 'Soybeans and soy products' },
  { id: 'wheat', label: 'Wheat', description: 'Wheat and wheat products' }
];

// Define schema for form validation
const formSchema = z.object({
  dietaryRestrictions: z.array(z.string()),
  favoriteCuisines: z.array(z.string()),
  allergens: z.array(z.string()),
  cookingSkillLevel: z.enum(['beginner', 'intermediate', 'advanced'])
});

const UserPreferencesPage: React.FC = () => {
  const { isAuthenticated, isLoading: authLoading, user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [preferences, setPreferences] = useState({
    dietaryRestrictions: [] as string[],
    favoriteCuisines: [] as string[],
    allergens: [] as string[],
    cookingSkillLevel: 'beginner' as string,
    healthGoals: [] as string[],
    maxCookingTime: '30 minutes' as string
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  
  // Initialize form with current preferences
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      dietaryRestrictions: [],
      favoriteCuisines: [],
      allergens: [],
      cookingSkillLevel: 'beginner'
    }
  });

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate('/signin');
      toast({
        title: "Authentication Required",
        description: "Please sign in to access your preferences.",
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
                  Sign in to access and customize your meal preferences
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

  // Load user preferences from authenticated backend
  useEffect(() => {
    if (!isAuthenticated) return;

    const loadPreferences = async () => {
      setIsLoading(true);
      try {
        const loadedPreferences = await loadUserPreferences();
        setPreferences(loadedPreferences);
        // Update form with loaded preferences
        form.reset({
          dietaryRestrictions: loadedPreferences.dietaryRestrictions || [],
          favoriteCuisines: loadedPreferences.favoriteCuisines || [],
          allergens: loadedPreferences.allergens || [],
          cookingSkillLevel: loadedPreferences.cookingSkillLevel || 'beginner'
        });
      } catch (error) {
        console.error('Error loading preferences:', error);
        toast({
          title: "Error Loading Preferences",
          description: "Could not load your preferences. Using defaults.",
          variant: "destructive"
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadPreferences();
  }, [isAuthenticated, toast, form]);

  // Auto-save preferences when form changes
  useEffect(() => {
    if (!hasChanges) return;

    const timeoutId = setTimeout(async () => {
      const values = form.getValues();
      await savePreferences(values, false); // Save without showing success message
    }, 1000); // Auto-save after 1 second of no changes

    return () => clearTimeout(timeoutId);
  }, [form.watch(), hasChanges]);

  // Create a convenience variable for the current form values
  const currentPreferences = form.watch();

  const savePreferences = async (values: z.infer<typeof formSchema>, showToast: boolean = true) => {
    console.log('Saving preferences:', values);
    setIsSaving(true);
    
    try {
      await saveUserPreferences({
        dietaryRestrictions: values.dietaryRestrictions,
        favoriteCuisines: values.favoriteCuisines,
        allergens: values.allergens,
        cookingSkillLevel: values.cookingSkillLevel
      });

      if (showToast) {
        toast({
          title: "Preferences Saved",
          description: "Your preferences have been updated successfully.",
        });
      }
      setHasChanges(false);
    } catch (error) {
      console.error('Error saving preferences:', error);
      toast({
        title: "Error Saving Preferences",
        description: "Failed to save your preferences. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDietaryChange = (id: string) => {
    const currentValues = form.getValues('dietaryRestrictions');
    const newValues = currentValues.includes(id)
      ? currentValues.filter(item => item !== id)
      : [...currentValues, id];
    
    form.setValue('dietaryRestrictions', newValues);
    setHasChanges(true);
  };

  const handleCuisineChange = (id: string) => {
    const currentValues = form.getValues('favoriteCuisines');
    const newValues = currentValues.includes(id)
      ? currentValues.filter(item => item !== id)
      : [...currentValues, id];
    
    form.setValue('favoriteCuisines', newValues);
    setHasChanges(true);
  };

  const handleAllergenChange = (id: string) => {
    const currentValues = form.getValues('allergens');
    const newValues = currentValues.includes(id)
      ? currentValues.filter(item => item !== id)
      : [...currentValues, id];
    
    form.setValue('allergens', newValues);
    setHasChanges(true);
  };

  const handleSkillLevelChange = (value: string) => {
    form.setValue('cookingSkillLevel', value as 'beginner' | 'intermediate' | 'advanced');
    setHasChanges(true);
  };

  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    setIsLoading(true);
    const success = await savePreferences(values, true);
    setIsLoading(false);

    if (success) {
      navigate('/');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="pt-24 md:pt-28">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 py-12 bg-white shadow-sm rounded-lg mt-8">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold">Your Recipe Preferences</h1>
            <p className="text-gray-500 mt-2">Tell us what you like, and we'll personalize your recipe recommendations</p>
            <div className="flex items-center justify-center mt-4 p-3 bg-blue-50 rounded-lg">
              <Info className="h-4 w-4 text-blue-600 mr-2" />
              <span className="text-sm text-blue-800">
                Your preferences are automatically saved as you make changes
              </span>
            </div>
          </div>

          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
              <div>
                <h2 className="text-xl font-medium mb-4">Dietary Restrictions</h2>
                <p className="text-sm text-gray-600 mb-4">Select any dietary restrictions you follow</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {dietaryOptions.map((option) => (
                    <div key={option.id} className="flex items-start space-x-3 p-3 border rounded-lg hover:bg-gray-50">
                      <Checkbox 
                        id={`dietary-${option.id}`}
                        checked={currentPreferences.dietaryRestrictions.includes(option.id)}
                        onCheckedChange={() => handleDietaryChange(option.id)}
                      />
                      <div className="flex-1">
                        <label 
                          htmlFor={`dietary-${option.id}`}
                          className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                        >
                          {option.label}
                        </label>
                        <p className="text-xs text-gray-500 mt-1">{option.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h2 className="text-xl font-medium mb-4">Favorite Cuisines</h2>
                <p className="text-sm text-gray-600 mb-4">Choose cuisines you enjoy - we'll recommend similar recipes</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {cuisineOptions.map((option) => (
                    <div key={option.id} className="flex items-start space-x-3 p-3 border rounded-lg hover:bg-gray-50">
                      <Checkbox 
                        id={`cuisine-${option.id}`}
                        checked={currentPreferences.favoriteCuisines.includes(option.id)}
                        onCheckedChange={() => handleCuisineChange(option.id)}
                      />
                      <div className="flex-1">
                        <label 
                          htmlFor={`cuisine-${option.id}`}
                          className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                        >
                          {option.label}
                        </label>
                        <p className="text-xs text-gray-500 mt-1">{option.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h2 className="text-xl font-medium mb-4">Allergens to Avoid</h2>
                <p className="text-sm text-gray-600 mb-4">We'll exclude recipes containing these ingredients</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {allergenOptions.map((option) => (
                    <div key={option.id} className="flex items-start space-x-3 p-3 border rounded-lg hover:bg-gray-50">
                      <Checkbox 
                        id={`allergen-${option.id}`}
                        checked={currentPreferences.allergens.includes(option.id)}
                        onCheckedChange={() => handleAllergenChange(option.id)}
                      />
                      <div className="flex-1">
                        <label 
                          htmlFor={`allergen-${option.id}`}
                          className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                        >
                          {option.label}
                        </label>
                        <p className="text-xs text-gray-500 mt-1">{option.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h2 className="text-xl font-medium mb-4">Cooking Skill Level</h2>
                <p className="text-sm text-gray-600 mb-4">This helps us recommend recipes appropriate for your experience</p>
                <Select 
                  value={currentPreferences.cookingSkillLevel} 
                  onValueChange={handleSkillLevelChange}
                >
                  <SelectTrigger className="w-full md:w-72">
                    <SelectValue placeholder="Select your cooking skill level" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="beginner">Beginner - Simple recipes under 45 minutes</SelectItem>
                    <SelectItem value="intermediate">Intermediate - Moderate complexity allowed</SelectItem>
                    <SelectItem value="advanced">Advanced - All recipe types welcome</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="pt-4 border-t">
                <div className="mb-4">
                  <h3 className="font-medium text-gray-900">Your Selection Summary:</h3>
                  <ul className="text-sm text-gray-600 mt-2 space-y-1">
                    <li>• {currentPreferences.favoriteCuisines.length} favorite cuisines selected</li>
                    <li>• {currentPreferences.dietaryRestrictions.length} dietary restrictions</li>
                    <li>• {currentPreferences.allergens.length} allergens to avoid</li>
                    <li>• Skill level: {currentPreferences.cookingSkillLevel}</li>
                  </ul>
                </div>
                
                <Button 
                  type="submit" 
                  className="w-full md:w-auto"
                  disabled={isLoading}
                >
                  {isLoading ? "Saving..." : "Save & Go to Home"}
                </Button>
              </div>
            </form>
          </Form>
        </div>
      </main>
    </div>
  );
};

export default UserPreferencesPage;
