import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useAuth } from '../context/AuthContext';
import { apiCall } from '../utils/apiUtils';
import { getApiUrl } from '../config/api';
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

// Interface for form options
interface FormOption {
  id: string;
  label: string;
  description: string;
}

// Define the form schema with proper types
const formSchema = z.object({
  dietaryRestrictions: z.array(z.string()).default([]),
  favoriteCuisines: z.array(z.string()).default([]),
  foodsToAvoid: z.array(z.string()).default([]),
  allergens: z.array(z.string()).default([]), // Backend expects this field
  cookingSkillLevel: z.enum(['beginner', 'intermediate', 'advanced'] as const).default('beginner'),
  favoriteFoods: z.array(z.string()).default([]), // Optional - only if user wants to add them
  healthGoals: z.array(z.string()).default([]),
  maxCookingTime: z.string().default('30 minutes'),
  includeBreakfast: z.boolean().default(true),
  includeLunch: z.boolean().default(true),
  includeDinner: z.boolean().default(true),
  includeSnacks: z.boolean().default(false),
  targetCalories: z.number().min(0).default(2000),
  targetProtein: z.number().min(0).default(150),
  targetCarbs: z.number().min(0).default(200),
  targetFat: z.number().min(0).default(65),
});

type FormValues = z.infer<typeof formSchema>;

// Define the shape of user preferences from the API
type UserPreferences = FormValues;

// Form options
const dietaryOptions: FormOption[] = [
  { id: 'vegetarian', label: 'Vegetarian', description: 'No meat or fish' },
  { id: 'vegan', label: 'Vegan', description: 'No animal products' },
  { id: 'gluten-free', label: 'Gluten Free', description: 'No gluten' },
  { id: 'dairy-free', label: 'Dairy Free', description: 'No dairy' },
  { id: 'nut-free', label: 'Nut Free', description: 'No nuts' },

];

const cuisineOptions: FormOption[] = [
  { id: 'american', label: 'American', description: 'Burgers, BBQ, comfort food' },
  { id: 'british', label: 'British', description: 'Fish and chips, pies, roasts' },
  { id: 'chinese', label: 'Chinese', description: 'Stir-fries, dumplings, noodles' },
  { id: 'french', label: 'French', description: 'Coq au vin, ratatouille, croissants' },
  { id: 'greek', label: 'Greek', description: 'Gyros, moussaka, tzatziki' },
  { id: 'indian', label: 'Indian', description: 'Curries, biryani, naan' },
  { id: 'irish', label: 'Irish', description: 'Irish stew, colcannon, boxty' },
  { id: 'italian', label: 'Italian', description: 'Pasta, pizza, risotto' },
  { id: 'japanese', label: 'Japanese', description: 'Sushi, ramen, tempura' },
  { id: 'mexican', label: 'Mexican', description: 'Tacos, enchiladas, mole' },
  { id: 'moroccan', label: 'Moroccan', description: 'Tagine, couscous, pastilla' },
  { id: 'spanish', label: 'Spanish', description: 'Paella, tapas, gazpacho' },
  { id: 'thai', label: 'Thai', description: 'Pad thai, green curry, tom yum' },
  { id: 'vietnamese', label: 'Vietnamese', description: 'Pho, banh mi, spring rolls' },
  { id: 'mediterranean', label: 'Mediterranean', description: 'Olive oil, fresh herbs, seafood' },
  { id: 'korean', label: 'Korean', description: 'Bibimbap, kimchi, bulgogi' },
  { id: 'caribbean', label: 'Caribbean', description: 'Jerk chicken, rice and peas' },
  { id: 'cajun', label: 'Cajun', description: 'Gumbo, jambalaya, étouffée' },


];

const healthGoalOptions: FormOption[] = [
  { id: 'weight-loss', label: 'Weight Loss', description: 'Lower calorie options' },
  { id: 'muscle-gain', label: 'Muscle Gain', description: 'Higher protein options' },
  { id: 'heart-health', label: 'Heart Health', description: 'Low sodium, healthy fats' },
  { id: 'digestive-health', label: 'Digestive Health', description: 'High fiber, probiotics' },
  { id: 'energy', label: 'More Energy', description: 'Balanced macronutrients' },
  { id: 'immunity', label: 'Immunity Boost', description: 'Rich in vitamins and minerals' },
];

const foodAvoidanceOptions: FormOption[] = [
  { id: 'pork', label: 'Pork', description: 'No pork products' },
  { id: 'beef', label: 'Beef', description: 'No beef products' },
  { id: 'poultry', label: 'Poultry', description: 'No chicken or turkey' },
  { id: 'seafood', label: 'Seafood', description: 'No fish or shellfish' },
  { id: 'eggs', label: 'Eggs', description: 'No eggs' },
  { id: 'dairy', label: 'Dairy', description: 'No milk, cheese, or yogurt' },
  { id: 'gluten', label: 'Gluten', description: 'No wheat, barley, rye' },
];

const cookingSkillOptions: FormOption[] = [
  { id: 'beginner', label: 'Beginner', description: 'New to cooking' },
  { id: 'intermediate', label: 'Intermediate', description: 'Some cooking experience' },
  { id: 'advanced', label: 'Advanced', description: 'Experienced cook' },
];

// Load user preferences from the backend
const loadUserPreferences = async (): Promise<UserPreferences> => {
  try {
    console.log('Loading user preferences...');
    
    // First try the authenticated endpoint
            let response = await apiCall('/api/preferences', {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    });

    console.log('Preferences API response status:', response.status);
    console.log('Preferences API response headers:', response.headers);

    // If authentication fails, try the session-based endpoint
    if (response.status === 401) {
      console.log('Authentication failed, trying session-based preferences...');
      response = await fetch(`${getApiUrl()}/preferences`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      });
      console.log('Session-based preferences response status:', response.status);
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Error response from server:', errorData);
      
      // If it's an authentication error, throw a specific error
      if (response.status === 401) {
        throw new Error('Authentication required. Please sign in again.');
      }
      
      throw new Error(errorData.error || 'Failed to load preferences');
    }

    const data = await response.json();
    console.log('Received preferences data:', data);
    
    // The preferences are in the 'preferences' field of the response
    const preferences = data.preferences || data;
    
    // Ensure favoriteFoods is an array of non-empty strings
    const favoriteFoods = (() => {
      const foods = Array.isArray(preferences.favoriteFoods) 
        ? preferences.favoriteFoods.filter((f): f is string => typeof f === 'string' && f.trim().length > 0)
        : [];
      return foods;
    })();
    
    // Ensure favoriteCuisines is an array and filter out any empty strings or invalid values
    const favoriteCuisines = Array.isArray(preferences.favoriteCuisines) 
      ? preferences.favoriteCuisines.filter((c: any) => c && typeof c === 'string')
      : [];
    
    // Ensure foodsToAvoid is an array
    const foodsToAvoid = Array.isArray(preferences.foodsToAvoid) 
      ? preferences.foodsToAvoid
      : [];
    
    // Default values for all preferences
    const defaultPreferences = {
      dietaryRestrictions: [],
      foodsToAvoid: [],
      cookingSkillLevel: 'beginner',
      healthGoals: [],
      maxCookingTime: '30 minutes',
      includeBreakfast: true,
      includeLunch: true,
      includeDinner: true,
      includeSnacks: false,
      favoriteFoods,
      favoriteCuisines
    };
    
    // Merge with API preferences, ensuring our defaults are used for missing values
    return {
      ...defaultPreferences,
      ...preferences, // Spread API preferences second to override defaults
      favoriteFoods,  // Ensure our processed favoriteFoods is used
      favoriteCuisines, // Ensure our processed favoriteCuisines is used
      foodsToAvoid    // Ensure our processed foodsToAvoid is used
    };
  } catch (error) {
    console.error('Error loading preferences:', error);
    throw error;
  }
};

// Save user preferences to the backend
const saveUserPreferences = async (data: UserPreferences, toast: any) => {
  try {
    console.log('Saving preferences with data:', data);
    
    // Prepare the payload according to the backend's expected format
    const payload = {
      preferences: {
        ...data,
        // Ensure arrays are always arrays and not undefined
        dietaryRestrictions: data.dietaryRestrictions || [],
        favoriteCuisines: data.favoriteCuisines || [],
        foodsToAvoid: data.foodsToAvoid || [],
        healthGoals: data.healthGoals || [],
        favoriteFoods: data.favoriteFoods || ['', '', ''],
        cookingSkillLevel: data.cookingSkillLevel || 'beginner',
        // Include meal preferences
        includeBreakfast: data.includeBreakfast ?? true,
        includeLunch: data.includeLunch ?? true,
        includeDinner: data.includeDinner ?? true,
        includeSnacks: data.includeSnacks ?? false,
        // Include nutrition targets
        targetCalories: data.targetCalories,
        targetProtein: data.targetProtein,
        targetCarbs: data.targetCarbs,
        targetFat: data.targetFat,
      },
    };

    console.log('Saving preferences with payload:', payload);

    // Use the apiCall utility which handles authentication and token refresh
            const response = await apiCall('/api/preferences', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Error response from server:', errorData);
      
      if (response.status === 401) {
        throw new Error('Your session has expired. Please sign in again.');
      }
      
      throw new Error(errorData.error || `Failed to save preferences: ${response.statusText}`);
    }

    const result = await response.json();
    console.log('Preferences saved successfully:', result);
    
    return result;
  } catch (error) {
    console.error('Error saving preferences:', error);
    
    // If it's an auth error, show a more user-friendly message
    if (error.message.includes('auth') || error.message.includes('token') || error.message.includes('session')) {
      toast({
        title: 'Authentication Error',
        description: 'Your session has expired. Please sign in again.',
        variant: 'destructive',
      });
      // Redirect to login after showing the toast
      setTimeout(() => {
        window.location.href = '/signin';
      }, 2000);
    } else {
      // For other errors, just show the error message
      toast({
        title: 'Error',
        description: error.message || 'Failed to save preferences',
        variant: 'destructive',
      });
    }
    
    throw error;
  }
};

// Common foods to avoid options
const commonFoodsToAvoid: FormOption[] = [
  { id: 'nuts', label: 'Nuts', description: 'Tree nuts and peanuts' },
  { id: 'shellfish', label: 'Shellfish', description: 'Shrimp, crab, lobster' },
  { id: 'dairy', label: 'Dairy', description: 'Milk and milk products' },
  { id: 'eggs', label: 'Eggs', description: 'All egg products' },
  { id: 'soy', label: 'Soy', description: 'Soybeans and soy products' },
  { id: 'wheat', label: 'Wheat', description: 'Wheat and wheat products' },
  { id: 'beef', label: 'Beef', description: 'All beef products' },
  { id: 'pork', label: 'Pork', description: 'All pork products' },
  { id: 'poultry', label: 'Poultry', description: 'Chicken, turkey, etc.' },
  { id: 'fish', label: 'Fish', description: 'All fish' },
  { id: 'seafood', label: 'Seafood', description: 'All seafood' },
  { id: 'gluten', label: 'Gluten', description: 'Wheat, barley, rye' }
];

const UserPreferencesPage = () => {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [customCuisine, setCustomCuisine] = useState('');
  const [customFoodToAvoid, setCustomFoodToAvoid] = useState('');

  // Define default values separately to ensure type safety
  const defaultValues: FormValues = {
    dietaryRestrictions: [],
    favoriteCuisines: [],
    foodsToAvoid: [],
    cookingSkillLevel: 'beginner',
    favoriteFoods: [], // Changed from tuple to array
    healthGoals: [],
    maxCookingTime: '30 minutes',
    includeBreakfast: true,
    includeLunch: true,
    includeDinner: true,
    includeSnacks: false,
    targetCalories: 2000,
    targetProtein: 150,
    targetCarbs: 200,
    targetFat: 65,
  };

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues,
  });

  // Authentication guard - redirect to sign in if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      toast({
        title: 'Authentication Required',
        description: 'Please sign in to access your preferences.',
        variant: 'destructive',
      });
      navigate('/signin');
      return;
    }
  }, [isAuthenticated, authLoading, navigate, toast]);
  
  const handleAddCustomCuisine = () => {
    const cuisine = customCuisine.trim();
    if (!cuisine) return;
    
      // Get current values from form
    const currentCuisines = form.getValues('favoriteCuisines') || [];
    
    // Check if cuisine already exists (case-insensitive)
    const cuisineExists = currentCuisines.some(
      (c: string) => c.toLowerCase() === cuisine.toLowerCase()
    );
    
    if (!cuisineExists) {
      // Create new array with the added cuisine
      const newCuisines = [...currentCuisines, cuisine];
      
      // Update the form state
      form.setValue('favoriteCuisines', newCuisines as string[], { 
        shouldDirty: true,
        shouldValidate: true
      });
      
      // Clear the input field
      setCustomCuisine('');
      
      // Just update the form state, don't auto-save here
      form.trigger('favoriteCuisines');
    } else {
      // If cuisine already exists, just clear the input
      setCustomCuisine('');
    }
  };
  
  const removeCuisine = (cuisineToRemove: string) => {
    const currentCuisines = form.getValues('favoriteCuisines') || [];
    const newCuisines = currentCuisines.filter(c => c !== cuisineToRemove);
    
    form.setValue('favoriteCuisines', newCuisines as string[], { 
      shouldDirty: true, 
      shouldValidate: true 
    });
    
    // Force form validation and UI update
    setTimeout(() => {
      form.trigger('favoriteCuisines');
    }, 0);
  };

  const handleAddFoodToAvoid = (e: React.FormEvent) => {
    e.preventDefault();
    const food = customFoodToAvoid.trim();
    if (!food) return;
    
    const currentFoods = form.getValues('foodsToAvoid') || [];
    const foodExists = currentFoods.some(
      (f: string) => f.toLowerCase() === food.toLowerCase()
    );
    
    if (!foodExists) {
      const newFoods = [...currentFoods, food];
      form.setValue('foodsToAvoid', newFoods, { 
        shouldDirty: true,
        shouldValidate: true 
      });
      setCustomFoodToAvoid('');
    } else {
      setCustomFoodToAvoid('');
    }
  };
  
  const removeFoodToAvoid = (foodToRemove: string) => {
    const currentFoods = form.getValues('foodsToAvoid') || [];
    const newFoods = currentFoods.filter(f => f !== foodToRemove);
    
    form.setValue('foodsToAvoid', newFoods, { 
      shouldDirty: true, 
      shouldValidate: true 
    });
    
    setTimeout(() => {
      form.trigger('foodsToAvoid');
    }, 0);
  };


  // Load user preferences on mount
  useEffect(() => {
    const loadPreferences = async () => {
      console.log('loadPreferences - Starting to load preferences');
      try {
        const preferences = await loadUserPreferences();
        
        console.log('loadPreferences - Successfully loaded preferences:', preferences);
        
        // Prepare form values with proper defaults
        const formValues: FormValues = {
          // Initialize with defaults and override with saved preferences
          dietaryRestrictions: Array.isArray(preferences.dietaryRestrictions) 
            ? preferences.dietaryRestrictions 
            : [],
          favoriteCuisines: Array.isArray(preferences.favoriteCuisines)
            ? preferences.favoriteCuisines
            : [],
          foodsToAvoid: Array.isArray(preferences.foodsToAvoid)
            ? preferences.foodsToAvoid
            : [],
          healthGoals: Array.isArray(preferences.healthGoals) 
            ? preferences.healthGoals 
            : [],
          favoriteFoods: (() => {
            const foods = Array.isArray(preferences.favoriteFoods) 
              ? preferences.favoriteFoods.filter((f): f is string => typeof f === 'string' && f.trim().length > 0)
              : [];
            // Ensure at least 2 slots for favorite foods
            while (foods.length < 2) {
              foods.push('');
            }
            return foods;
          })(),
          cookingSkillLevel: (preferences.cookingSkillLevel as 'beginner' | 'intermediate' | 'advanced') || 'beginner',
          maxCookingTime: preferences.maxCookingTime || '30 minutes',
          includeBreakfast: preferences.includeBreakfast !== false,
          includeLunch: preferences.includeLunch !== false,
          includeDinner: preferences.includeDinner !== false,
          includeSnacks: !!preferences.includeSnacks,
          targetCalories: preferences.targetCalories || 2000,
          targetProtein: preferences.targetProtein || 150,
          targetCarbs: preferences.targetCarbs || 200,
          targetFat: preferences.targetFat || 65
        };
        
        console.log('Resetting form with values:', formValues);
        form.reset(formValues);
      } catch (error) {
        console.error('Failed to load preferences:', error);
        
        // If it's an authentication error, just use default values
        if (error.message.includes('Authentication required') || error.message.includes('Invalid or expired token')) {
          console.log('Using default preferences due to authentication error');
          // Use default form values
          form.reset();
        } else {
          toast({
            title: 'Error',
            description: 'Failed to load your preferences. Please try again.',
            variant: 'destructive',
          });
        }
      } finally {
        setIsLoading(false);
      }
    };

    // Only load preferences if authenticated
    if (isAuthenticated && !authLoading) {
      console.log('useEffect - Loading preferences (authenticated)');
      loadPreferences();
    } else if (!authLoading) {
      // If not authenticated, just set loading to false
      setIsLoading(false);
    }
  }, [form, toast, isAuthenticated, authLoading]);

  // Type guard to check if a value is a valid cooking skill level
  const isCookingSkillLevel = (value: unknown): value is 'beginner' | 'intermediate' | 'advanced' => {
    return typeof value === 'string' && ['beginner', 'intermediate', 'advanced'].includes(value);
  };

  // Clean and validate form values before submission
  const cleanAndValidateFormValues = (values: FormValues): UserPreferences => {
    // Ensure all required fields have values and are of the correct type
    const cleaned: UserPreferences = {
      dietaryRestrictions: Array.isArray(values.dietaryRestrictions)
        ? [...new Set(values.dietaryRestrictions
            .filter((r): r is string => Boolean(r) && typeof r === 'string')
            .map(r => r.trim())
            .filter(Boolean))]
        : [],

      favoriteCuisines: Array.isArray(values.favoriteCuisines)
        ? [...new Set(values.favoriteCuisines
            .filter((c): c is string => Boolean(c) && typeof c === 'string')
            .map(c => c.trim())
            .filter(Boolean))]
        : [],

      // Keep foodsToAvoid for form display
      foodsToAvoid: Array.isArray(values.foodsToAvoid)
        ? values.foodsToAvoid.filter((f): f is string => Boolean(f) && typeof f === 'string')
        : [],
      // Map foodsToAvoid to allergens for backend compatibility
      allergens: Array.isArray(values.foodsToAvoid)
        ? values.foodsToAvoid.filter((f): f is string => Boolean(f) && typeof f === 'string')
        : [],

      cookingSkillLevel: isCookingSkillLevel(values.cookingSkillLevel)
        ? values.cookingSkillLevel
        : 'beginner',

      // Include non-empty favorite foods (optional)
      favoriteFoods: Array.isArray(values.favoriteFoods)
        ? values.favoriteFoods
            .filter((f): f is string => typeof f === 'string' && f.trim().length > 0)
            .map(f => f.trim())
        : [],

      healthGoals: Array.isArray(values.healthGoals)
        ? values.healthGoals.filter((g): g is string => Boolean(g) && typeof g === 'string')
        : [],

      // Ensure numeric values are within reasonable bounds
      maxCookingTime: typeof values.maxCookingTime === 'string' ? values.maxCookingTime : '30 minutes',
      includeBreakfast: values.includeBreakfast !== false,
      includeLunch: values.includeLunch !== false,
      includeDinner: values.includeDinner !== false,
      includeSnacks: Boolean(values.includeSnacks),
      targetCalories: Math.max(0, Math.min(Number(values.targetCalories) || 2000, 10000)),
      targetProtein: Math.max(0, Math.min(Number(values.targetProtein) || 150, 500)),
      targetCarbs: Math.max(0, Math.min(Number(values.targetCarbs) || 200, 1000)),
      targetFat: Math.max(0, Math.min(Number(values.targetFat) || 65, 300))
    };

    return cleaned;
  };

  // Handle form submission
  const onSubmit = async (values: FormValues) => {
    // Check if user is authenticated before submitting
    if (!isAuthenticated) {
      toast({
        title: 'Authentication Required',
        description: 'Please sign in to save your preferences.',
        variant: 'destructive',
      });
      navigate('/signin');
      return;
    }

    try {
      setIsSaving(true);
      
      // Clean and validate the form values
      const cleanedData = cleanAndValidateFormValues(values);
      console.log('Submitting cleaned preferences:', cleanedData);
      
      // Save with proper structure that backend expects
      await saveUserPreferences(cleanedData, toast);
      
      // Update the form state to reflect the saved values
      form.reset(cleanedData);
      
      toast({
        title: "Success",
        description: "Your preferences have been saved successfully.",
        variant: "default",
      });
    } catch (error) {
      console.error('Error in form submission:', error);
      
      // Handle different types of errors
      if (error instanceof Error) {
        // Authentication errors
        if (error.message.includes('auth') || 
            error.message.includes('token') || 
            error.message.includes('session') ||
            error.message.includes('Authentication required') || 
            error.message.includes('Invalid or expired token')) {
          toast({
            title: 'Authentication Required',
            description: 'Please sign in to save your preferences.',
            variant: 'destructive',
          });
        } else {
          // Other errors
          toast({
            title: "Error",
            description: error.message || "Failed to save preferences. Please try again.",
            variant: "destructive",
          });
        }
      } else {
        // Non-Error objects
        toast({
          title: "Error",
          description: "An unexpected error occurred. Please try again.",
          variant: "destructive",
        });
      }
    } finally {
      setIsSaving(false);
    }
  };

  // Render loading states
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
          <p className="text-gray-500">Checking authentication...</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
          <p className="text-gray-500">Loading your preferences...</p>
        </div>
      </div>
    );
  }

  // Don't render the form if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <main className="pt-24 md:pt-28">
          <div className="max-w-2xl mx-auto px-4 sm:px-6 py-12 text-center">
            <h1 className="text-3xl font-bold mb-4">Authentication Required</h1>
            <p className="text-gray-500 mb-6">Please sign in to access your preferences.</p>
            <button
              onClick={() => navigate('/signin')}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Sign In
            </button>
          </div>
        </main>
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
                <h2 className="text-xl font-medium mb-4">Favorite Foods (Optional)</h2>
                <p className="text-sm text-gray-600 mb-4">Add your favorite foods to get more personalized recommendations</p>
                <div className="space-y-3">
                  {/* Display existing favorite foods */}
                  {form.watch('favoriteFoods')?.map((food, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <Input
                        value={food}
                        onChange={(e) => {
                          const currentFoods = form.watch('favoriteFoods') || [];
                          const newFoods = [...currentFoods];
                          newFoods[index] = e.target.value;
                          // Keep empty strings for validation, but filter them when saving
                          form.setValue('favoriteFoods', newFoods, { shouldDirty: true });
                        }}
                        placeholder={`e.g., pizza, burger, chicken`}
                      />
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          const currentFoods = form.watch('favoriteFoods') || [];
                          // Don't allow removing if we only have 2 slots
                          if (currentFoods.length <= 2) return;
                          const newFoods = currentFoods.filter((_, i) => i !== index);
                          form.setValue('favoriteFoods', newFoods, { shouldDirty: true });
                        }}
                        disabled={form.watch('favoriteFoods')?.length <= 2}
                      >
                        Remove
                      </Button>
                    </div>
                  ))}
                  
                  {/* Add new favorite food button */}
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      const currentFoods = form.watch('favoriteFoods') || [];
                      form.setValue('favoriteFoods', [...currentFoods, ''], { shouldDirty: true });
                    }}
                  >
                    + Add Favorite Food
                  </Button>
                  
                  {/* Show validation error */}
                  {form.formState.errors.favoriteFoods && (
                    <p className="text-sm text-red-600">{form.formState.errors.favoriteFoods.message}</p>
                  )}
                </div>
              </div>

              {/* Dietary Restrictions */}
              <div>
                <h2 className="text-xl font-medium mb-4">Dietary Restrictions</h2>
                <p className="text-sm text-gray-600 mb-4">Select any dietary restrictions you follow</p>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {dietaryOptions.map((option) => (
                  <FormField
                    key={option.id}
                    control={form.control}
                    name="dietaryRestrictions"
                    render={({ field }) => (
                      <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                        <FormControl>
                          <Checkbox
                            checked={field.value?.includes(option.id)}
                            onCheckedChange={(checked) => {
                              return checked
                                ? field.onChange([...field.value, option.id])
                                : field.onChange(
                                    field.value?.filter(
                                      (value: string) => value !== option.id
                                    )
                                  )
                            }}
                          />
                        </FormControl>
                        <div className="space-y-1 leading-none">
                          <FormLabel>{option.label}</FormLabel>
                          <p className="text-sm text-muted-foreground">
                            {option.description}
                          </p>
                        </div>
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
                      render={({ field }) => {
                        const isChecked = field.value?.includes(option.id) || false;
                        return (
                          <FormItem className="flex items-center space-x-3 space-y-0">
                            <FormControl>
                              <Checkbox
                                checked={isChecked}
                                onCheckedChange={(checked) => {
                                  const currentValue = field.value || [];
                                  const newValue = checked
                                    ? [...new Set([...currentValue, option.id])]
                                    : currentValue.filter((value: string) => value !== option.id);
                                  field.onChange(newValue);
                                }}
                              />
                            </FormControl>
                            <FormLabel className="font-normal">
                              {option.label}
                              <p className="text-xs text-gray-500">{option.description}</p>
                            </FormLabel>
                          </FormItem>
                        );
                      }}
                    />
                  ))}
                </div>
                
                {/* Custom Cuisine Input */}
                <div className="mt-4">
                  <div className="flex gap-2">
                    <Input
                      type="text"
                      placeholder="Add a custom cuisine..."
                      value={customCuisine}
                      onChange={(e) => setCustomCuisine(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          handleAddCustomCuisine();
                        }
                      }}
                      className="flex-1"
                    />
                    <Button 
                      type="button"
                      variant="outline"
                      onClick={handleAddCustomCuisine}
                      disabled={!customCuisine.trim()}
                    >
                      Add
                    </Button>
                  </div>
                  
                  {/* Display selected custom cuisines */}
                  <div className="flex flex-wrap gap-2 mt-2">
                    {Array.isArray(form.watch('favoriteCuisines')) && form.watch('favoriteCuisines')
                      .filter(cuisine => 
                        cuisine && 
                        typeof cuisine === 'string' &&
                        !cuisineOptions.some(opt => opt.id.toLowerCase() === cuisine.toLowerCase())
                      )
                      .map((cuisine, index) => (
                      <div 
                        key={cuisine} 
                        className="bg-gray-100 px-3 py-1 rounded-full text-sm flex items-center gap-1"
                      >
                        {cuisine}
                        <button 
                          type="button" 
                          onClick={() => removeCuisine(cuisine)}
                          className="text-gray-500 hover:text-red-500 ml-1"
                        >
                          ×
                        </button>
                      </div>
                      ))
                    }
                  </div>
                </div>
              </div>

              {/* Foods to Avoid */}
              <div>
                <h2 className="text-xl font-medium mb-4">Foods to Avoid</h2>
                <p className="text-sm text-gray-600 mb-4">Select any foods you want to avoid</p>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {[
                    { id: 'nuts', label: 'Nuts' },
                    { id: 'dairy', label: 'Dairy' },
                    { id: 'gluten', label: 'Gluten' },
                    { id: 'shellfish', label: 'Shellfish' },
                    { id: 'eggs', label: 'Eggs' },
                    { id: 'soy', label: 'Soy' },
                    { id: 'fish', label: 'Fish' },
                    { id: 'pork', label: 'Pork' },
                    { id: 'beef', label: 'Beef' },
                    { id: 'poultry', label: 'Poultry' },
                  ].map((option) => (
                    <FormField
                      key={option.id}
                      control={form.control}
                      name="foodsToAvoid"
                      render={({ field }) => (
                        <FormItem className="flex flex-row items-start space-x-3 space-y-0">
                          <FormControl>
                            <Checkbox
                              checked={Array.isArray(field.value) && field.value.includes(option.id)}
                              onCheckedChange={(checked) => {
                                const currentValue = Array.isArray(field.value) ? field.value : [];
                                return checked
                                  ? field.onChange([...currentValue, option.id])
                                  : field.onChange(
                                      currentValue.filter(
                                        (value: string) => value !== option.id
                                      )
                                    )
                              }}
                            />
                          </FormControl>
                          <FormLabel>{option.label}</FormLabel>
                        </FormItem>
                      )}
                    />
                  ))}
                </div>

                {/* Custom Food to Avoid Input */}
                <div className="mt-4">
                  <div className="flex gap-2">
                    <Input
                      type="text"
                      placeholder="Add a custom food to avoid..."
                      value={customFoodToAvoid}
                      onChange={(e) => setCustomFoodToAvoid(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          handleAddFoodToAvoid(e);
                        }
                      }}
                      className="flex-1"
                    />
                    <Button 
                      type="button"
                      variant="outline"
                      onClick={handleAddFoodToAvoid}
                      disabled={!customFoodToAvoid.trim()}
                    >
                      Add
                    </Button>
                  </div>
                  
                  {/* Display selected custom foods to avoid */}
                  <div className="flex flex-wrap gap-2 mt-2">
                    {Array.isArray(form.watch('foodsToAvoid')) && form.watch('foodsToAvoid')
                      .filter(food => 
                        food && 
                        typeof food === 'string' &&
                        ![
                          'nuts', 'dairy', 'gluten', 'shellfish', 'eggs', 
                          'soy', 'fish', 'pork', 'beef', 'poultry'
                        ].includes(food.toLowerCase())
                      )
                      .map((food) => (
                        <div 
                          key={food} 
                          className="bg-gray-100 px-3 py-1 rounded-full text-sm flex items-center gap-1"
                        >
                          {food}
                          <button 
                            type="button" 
                            onClick={() => removeFoodToAvoid(food)}
                            className="text-gray-500 hover:text-red-500 ml-1"
                          >
                            ×
                          </button>
                        </div>
                      ))
                    }
                  </div>
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
