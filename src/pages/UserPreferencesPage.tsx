import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useAuth } from '../context/AuthContext';
import { useToast } from '@/hooks/use-toast';
import Header from '../components/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Loader2, Info, Lock } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

// Define the shape of user preferences from the API
type UserPreferences = {
  dietaryRestrictions?: string[];
  favoriteCuisines?: string[];
  allergens?: string[];
  cookingSkillLevel?: 'beginner' | 'intermediate' | 'advanced';
  favoriteFoods?: string[];
  healthGoals?: string[];
  maxCookingTime?: string;
  [key: string]: any; // Add index signature for additional properties
};

// Load user preferences from the backend
const loadUserPreferences = async (): Promise<UserPreferences> => {
  try {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch('http://localhost:5003/api/preferences', {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      credentials: 'include'
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Error response from server:', errorData);
      throw new Error(errorData.error || 'Failed to load preferences');
    }

    const data = await response.json();
    console.log('Received preferences data:', data);
    
    // The preferences are in the 'preferences' field of the response
    const preferences = data.preferences || data;
    
    // Ensure favoriteFoods is an array of exactly 3 strings
    const favoriteFoods = Array.isArray(preferences.favoriteFoods) 
      ? [...preferences.favoriteFoods, '', '', ''].slice(0, 3)
      : ['', '', ''];
    
    // Return with defaults for any missing fields
    return {
      dietaryRestrictions: [],
      favoriteCuisines: [],
      allergens: [],
      cookingSkillLevel: 'beginner',
      healthGoals: [],
      maxCookingTime: '30 minutes',
      ...preferences,
      favoriteFoods
    };
  } catch (error) {
    console.error('Error loading preferences:', error);
    // Return default values if there's an error
    return {
      dietaryRestrictions: [],
      favoriteCuisines: [],
      allergens: [],
      cookingSkillLevel: 'beginner',
      favoriteFoods: ['', '', ''],
      healthGoals: [],
      maxCookingTime: '30 minutes'
    };
  }
};

// Save user preferences to the backend
const saveUserPreferences = async (data: UserPreferences) => {
  try {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    console.log('Saving preferences:', data);

    // Ensure favoriteFoods is an array of exactly 3 strings
    const favoriteFoods = Array.isArray(data.favoriteFoods) 
      ? data.favoriteFoods.slice(0, 3).map(food => String(food || ''))
      : ['', '', ''];

    const response = await fetch('http://localhost:5003/api/preferences', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        preferences: {
          ...data,
          favoriteFoods
        }
      }),
      credentials: 'include'
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Error response from server:', errorData);
      throw new Error(errorData.error || 'Failed to save preferences');
    }

    const result = await response.json();
    console.log('Save response:', result);
    
    return result;
  } catch (error) {
    console.error('Error saving preferences:', error);
    throw error;
  }
};

// Interface for form options
interface FormOption {
  id: string;
  label: string;
  description: string;
}

// Form schema for validation
const formSchema = z.object({
  dietaryRestrictions: z.array(z.string()),
  favoriteCuisines: z.array(z.string()),
  allergens: z.array(z.string()),
  cookingSkillLevel: z.enum(['beginner', 'intermediate', 'advanced']),
  favoriteFoods: z.array(z.string()).length(3),
  healthGoals: z.array(z.string()).optional(),
  maxCookingTime: z.string().optional()
});

type FormValues = z.infer<typeof formSchema>;

// Form options
const dietaryOptions: FormOption[] = [
  { id: 'vegetarian', label: 'Vegetarian', description: 'No meat or fish' },
  { id: 'vegan', label: 'Vegan', description: 'No animal products' },
  { id: 'gluten-free', label: 'Gluten Free', description: 'No wheat, barley, or rye' },
  { id: 'dairy-free', label: 'Dairy Free', description: 'No milk products' },
  { id: 'keto', label: 'Keto', description: 'Low carb, high fat' },
  { id: 'paleo', label: 'Paleo', description: 'No processed foods' }
];

const cuisineOptions: FormOption[] = [
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

const allergenOptions: FormOption[] = [
  { id: 'nuts', label: 'Nuts', description: 'Tree nuts and peanuts' },
  { id: 'shellfish', label: 'Shellfish', description: 'Shrimp, crab, lobster' },
  { id: 'dairy', label: 'Dairy', description: 'Milk and milk products' },
  { id: 'eggs', label: 'Eggs', description: 'All egg products' },
  { id: 'soy', label: 'Soy', description: 'Soybeans and soy products' },
  { id: 'wheat', label: 'Wheat', description: 'Wheat and wheat products' }
];

const UserPreferencesPage: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      dietaryRestrictions: [],
      favoriteCuisines: [],
      allergens: [],
      cookingSkillLevel: 'beginner',
      favoriteFoods: ['', '', ''],
      healthGoals: [],
      maxCookingTime: '30 minutes'
    }
  });

  // Load user preferences on mount
  useEffect(() => {
    const loadPreferences = async () => {
      if (!isAuthenticated) {
        setIsLoading(false);
        return;
      }

      try {
        const preferences = await loadUserPreferences();
        // Ensure we have exactly 3 favorite foods
        const favoriteFoods = [...preferences.favoriteFoods, '', '', ''].slice(0, 3) as [string, string, string];
        
        form.reset({
          ...preferences,
          favoriteFoods
        });
      } catch (error) {
        console.error('Failed to load preferences:', error);
        toast({
          title: 'Error',
          description: 'Failed to load your preferences. Please try again.',
          variant: 'destructive',
        });
      } finally {
        setIsLoading(false);
      }
    };

    if (isAuthenticated) {
      loadPreferences();
    }
  }, [isAuthenticated, form, toast]);

  // Handle form submission
  const onSubmit = async (data: FormValues) => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    try {
      setIsSaving(true);
      
      // Prepare the data to be saved
      const preferencesData: UserPreferences = {
        dietaryRestrictions: data.dietaryRestrictions || [],
        favoriteCuisines: data.favoriteCuisines || [],
        allergens: data.allergens || [],
        cookingSkillLevel: data.cookingSkillLevel as 'beginner' | 'intermediate' | 'advanced',
        favoriteFoods: data.favoriteFoods.filter(Boolean),
        healthGoals: data.healthGoals || [],
        maxCookingTime: data.maxCookingTime || '30 minutes'
      };

      await saveUserPreferences(preferencesData);
      
      toast({
        title: 'Success',
        description: 'Your preferences have been saved.',
      });
      
      // Optional: Refresh the preferences after saving
      const updatedPreferences = await loadUserPreferences();
      form.reset({
        ...updatedPreferences,
        favoriteFoods: [...updatedPreferences.favoriteFoods || [], '', '', ''].slice(0, 3) as [string, string, string]
      });
      
    } catch (error) {
      console.error('Failed to save preferences:', error);
      toast({
        title: 'Error',
        description: 'Failed to save your preferences. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsSaving(false);
    }
  };

  // Render loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  // Render sign-in prompt for unauthenticated users
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Sign In Required</CardTitle>
            <CardDescription>
              Please sign in to view and edit your preferences.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button className="w-full" onClick={() => navigate('/login')}>
              Sign In
            </Button>
            <div className="text-center text-sm text-gray-500">
              Don't have an account?{' '}
              <Button variant="link" className="p-0 h-auto" onClick={() => navigate('/signup')}>
                Sign up
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="pt-24 md:pt-28">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 py-12">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold">Your Recipe Preferences</h1>
            <p className="text-gray-500 mt-2">
              Tell us what you like, and we'll personalize your recipe recommendations
            </p>
            <div className="flex items-center justify-center mt-4 p-3 bg-blue-50 rounded-lg">
              <Info className="h-4 w-4 text-blue-600 mr-2" />
              <span className="text-sm text-blue-800">
                Your preferences are automatically saved as you make changes
              </span>
            </div>
          </div>

          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
              {/* Favorite Foods */}
              <div>
                <h2 className="text-xl font-medium mb-4">Favorite Foods</h2>
                <p className="text-sm text-gray-600 mb-4">Enter up to 3 of your favorite foods</p>
                <div className="space-y-3">
                  {[0, 1, 2].map((index) => (
                    <FormField
                      key={index}
                      control={form.control}
                      name={`favoriteFoods.${index}`}
                      render={({ field }) => (
                        <FormItem>
                          <FormControl>
                            <Input
                              placeholder={`Favorite food #${index + 1}`}
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  ))}
                </div>
              </div>

              {/* Dietary Restrictions */}
              <div>
                <h2 className="text-xl font-medium mb-4">Dietary Restrictions</h2>
                <p className="text-sm text-gray-600 mb-4">Select any dietary restrictions you follow</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {dietaryOptions.map((option) => (
                    <FormField
                      key={option.id}
                      control={form.control}
                      name="dietaryRestrictions"
                      render={({ field }) => (
                        <FormItem className="flex items-center space-x-3 space-y-0">
                          <FormControl>
                            <Checkbox
                              checked={field.value?.includes(option.id)}
                              onCheckedChange={(checked) => {
                                return checked
                                  ? field.onChange([...field.value, option.id])
                                  : field.onChange(
                                      field.value?.filter((value: string) => value !== option.id)
                                    );
                              }}
                            />
                          </FormControl>
                          <FormLabel className="font-normal">
                            {option.label}
                            <p className="text-xs text-gray-500">{option.description}</p>
                          </FormLabel>
                        </FormItem>
                      )}
                    />
                  ))}
                </div>
              </div>

              {/* Cuisines */}
              <div>
                <h2 className="text-xl font-medium mb-4">Favorite Cuisines</h2>
                <p className="text-sm text-gray-600 mb-4">Choose cuisines you enjoy</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {cuisineOptions.map((option) => (
                    <FormField
                      key={option.id}
                      control={form.control}
                      name="favoriteCuisines"
                      render={({ field }) => (
                        <FormItem className="flex items-center space-x-3 space-y-0">
                          <FormControl>
                            <Checkbox
                              checked={field.value?.includes(option.id)}
                              onCheckedChange={(checked) => {
                                return checked
                                  ? field.onChange([...field.value, option.id])
                                  : field.onChange(
                                      field.value?.filter((value: string) => value !== option.id)
                                    );
                              }}
                            />
                          </FormControl>
                          <FormLabel className="font-normal">
                            {option.label}
                            <p className="text-xs text-gray-500">{option.description}</p>
                          </FormLabel>
                        </FormItem>
                      )}
                    />
                  ))}
                </div>
              </div>

              {/* Allergens */}
              <div>
                <h2 className="text-xl font-medium mb-4">Allergens to Avoid</h2>
                <p className="text-sm text-gray-600 mb-4">Select any food allergies</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {allergenOptions.map((option) => (
                    <FormField
                      key={option.id}
                      control={form.control}
                      name="allergens"
                      render={({ field }) => (
                        <FormItem className="flex items-center space-x-3 space-y-0">
                          <FormControl>
                            <Checkbox
                              checked={field.value?.includes(option.id)}
                              onCheckedChange={(checked) => {
                                return checked
                                  ? field.onChange([...field.value, option.id])
                                  : field.onChange(
                                      field.value?.filter((value: string) => value !== option.id)
                                    );
                              }}
                            />
                          </FormControl>
                          <FormLabel className="font-normal">
                            {option.label}
                            <p className="text-xs text-gray-500">{option.description}</p>
                          </FormLabel>
                        </FormItem>
                      )}
                    />
                  ))}
                </div>
              </div>

              {/* Cooking Skill Level */}
              <div>
                <h2 className="text-xl font-medium mb-4">Cooking Skill Level</h2>
                <p className="text-sm text-gray-600 mb-4">Select your comfort level in the kitchen</p>
                <FormField
                  control={form.control}
                  name="cookingSkillLevel"
                  render={({ field }) => (
                    <FormItem>
                      <Select onValueChange={field.onChange} defaultValue={field.value}>
                        <FormControl>
                          <SelectTrigger className="w-full md:w-1/2">
                            <SelectValue placeholder="Select your skill level" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="beginner">Beginner - Just getting started</SelectItem>
                          <SelectItem value="intermediate">Intermediate - Comfortable with basics</SelectItem>
                          <SelectItem value="advanced">Advanced - Experienced cook</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              {/* Form Actions */}
              <div className="flex justify-end space-x-4 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => form.reset()}
                  disabled={isSaving}
                >
                  Reset
                </Button>
                <Button type="submit" disabled={isSaving}>
                  {isSaving ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    'Save Preferences'
                  )}
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
