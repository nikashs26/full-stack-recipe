import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';
import Header from '../components/Header';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Form, FormField, FormItem, FormLabel } from '@/components/ui/form';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Info } from 'lucide-react';

interface UserPreferences {
  dietaryRestrictions: string[];
  favoriteCuisines: string[];
  allergens: string[];
  cookingSkillLevel: 'beginner' | 'intermediate' | 'advanced';
}

const dietaryOptions = [
  { id: 'vegetarian', label: 'Vegetarian', description: 'No meat or fish' },
  { id: 'vegan', label: 'Vegan', description: 'No animal products' },
  { id: 'gluten-free', label: 'Gluten Free', description: 'No wheat, barley, or rye' },
  { id: 'dairy-free', label: 'Dairy Free', description: 'No milk products' },
  { id: 'keto', label: 'Keto', description: 'Low carb, high fat' },
  { id: 'paleo', label: 'Paleo', description: 'No processed foods' }
];

const cuisineOptions = [
  { id: 'italian', label: 'Italian', description: 'Pasta, pizza, Mediterranean' },
  { id: 'mexican', label: 'Mexican', description: 'Spicy, flavorful, corn-based' },
  { id: 'chinese', label: 'Chinese', description: 'Stir-fry, rice, soy-based' },
  { id: 'indian', label: 'Indian', description: 'Curry, spices, rice dishes' },
  { id: 'japanese', label: 'Japanese', description: 'Sushi, clean flavors' },
  { id: 'mediterranean', label: 'Mediterranean', description: 'Olive oil, fresh vegetables' },
  { id: 'american', label: 'American', description: 'Comfort food, grilled items' },
  { id: 'thai', label: 'Thai', description: 'Sweet, sour, spicy balance' }
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
  const navigate = useNavigate();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  const [currentPreferences, setCurrentPreferences] = useState<UserPreferences | null>(null);
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

  // Load current preferences on mount
  useEffect(() => {
    const loadPreferences = async () => {
      try {
        const response = await fetch('http://localhost:5001/api/temp-preferences', {
          credentials: 'include' // Include cookies for session
        });
        if (response.ok) {
          const data = await response.json();
          if (data.preferences) {
            setCurrentPreferences(data.preferences);
            // Update form with loaded preferences
            form.reset({
              dietaryRestrictions: data.preferences.dietaryRestrictions || [],
              favoriteCuisines: data.preferences.favoriteCuisines || [],
              allergens: data.preferences.allergens || [],
              cookingSkillLevel: data.preferences.cookingSkillLevel || 'beginner'
            });
          }
        }
      } catch (error) {
        console.error('Error loading preferences:', error);
      }
    };

    loadPreferences();
  }, [form]);

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
  const preferences = form.watch();

  const savePreferences = async (values: z.infer<typeof formSchema>, showToast: boolean = true) => {
    console.log('🔥 FRONTEND: Starting to save preferences...');
    console.log('🔥 FRONTEND: Values to save:', values);
    
    const preferencesPayload = {
      preferences: {
        dietaryRestrictions: values.dietaryRestrictions,
        favoriteCuisines: values.favoriteCuisines,
        allergens: values.allergens,
        cookingSkillLevel: values.cookingSkillLevel
      }
    };
    
    console.log('🔥 FRONTEND: Payload being sent:', JSON.stringify(preferencesPayload, null, 2));
    
    try {
      const response = await fetch('http://localhost:5001/api/temp-preferences', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Include cookies for session
        body: JSON.stringify(preferencesPayload),
      });

      console.log('🔥 FRONTEND: Response status:', response.status);
      console.log('🔥 FRONTEND: Response headers:', response.headers);
      
      const responseData = await response.json();
      console.log('🔥 FRONTEND: Response data:', responseData);
      
      if (response.ok) {
        console.log('🔥 FRONTEND: Preferences saved successfully!');
        setHasChanges(false);
        if (showToast) {
          toast({
            title: "Preferences saved!",
            description: `Your recipe recommendations will now include ${values.favoriteCuisines.length} cuisine types and respect ${values.dietaryRestrictions.length} dietary restrictions.`,
          });
        }
        return true;
      } else {
        console.log('🔥 FRONTEND: Failed to save preferences - response not ok');
        throw new Error('Failed to save preferences');
      }
    } catch (error) {
      console.error('🔥 FRONTEND: Error saving preferences:', error);
      if (showToast) {
        toast({
          title: "Failed to save preferences",
          description: "Please try again.",
          variant: "destructive"
        });
      }
      return false;
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
                        checked={preferences.dietaryRestrictions.includes(option.id)}
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
                        checked={preferences.favoriteCuisines.includes(option.id)}
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
                        checked={preferences.allergens.includes(option.id)}
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
                  value={preferences.cookingSkillLevel} 
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
                    <li>• {preferences.favoriteCuisines.length} favorite cuisines selected</li>
                    <li>• {preferences.dietaryRestrictions.length} dietary restrictions</li>
                    <li>• {preferences.allergens.length} allergens to avoid</li>
                    <li>• Skill level: {preferences.cookingSkillLevel}</li>
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
