
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '@/hooks/use-toast';
import Header from '../components/Header';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Form, FormField, FormItem, FormLabel } from '@/components/ui/form';
import { UserPreferences } from '../types/auth';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';

const dietaryOptions = [
  { id: 'vegetarian', label: 'Vegetarian' },
  { id: 'vegan', label: 'Vegan' },
  { id: 'gluten-free', label: 'Gluten Free' },
  { id: 'dairy-free', label: 'Dairy Free' },
  { id: 'keto', label: 'Keto' },
  { id: 'paleo', label: 'Paleo' }
];

const cuisineOptions = [
  { id: 'italian', label: 'Italian' },
  { id: 'mexican', label: 'Mexican' },
  { id: 'chinese', label: 'Chinese' },
  { id: 'indian', label: 'Indian' },
  { id: 'japanese', label: 'Japanese' },
  { id: 'mediterranean', label: 'Mediterranean' },
  { id: 'american', label: 'American' },
  { id: 'thai', label: 'Thai' }
];

const allergenOptions = [
  { id: 'nuts', label: 'Nuts' },
  { id: 'shellfish', label: 'Shellfish' },
  { id: 'dairy', label: 'Dairy' },
  { id: 'eggs', label: 'Eggs' },
  { id: 'soy', label: 'Soy' },
  { id: 'wheat', label: 'Wheat' }
];

// Define schema for form validation
const formSchema = z.object({
  dietaryRestrictions: z.array(z.string()),
  favoriteCuisines: z.array(z.string()),
  allergens: z.array(z.string()),
  cookingSkillLevel: z.enum(['beginner', 'intermediate', 'advanced'])
});

const UserPreferencesPage: React.FC = () => {
  const { user, updateUserPreferences } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  
  // Initialize form with user preferences
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      dietaryRestrictions: user?.preferences?.dietaryRestrictions || [],
      favoriteCuisines: user?.preferences?.favoriteCuisines || [],
      allergens: user?.preferences?.allergens || [],
      cookingSkillLevel: user?.preferences?.cookingSkillLevel || 'beginner'
    }
  });

  // Create a convenience variable for the current form values
  const preferences = form.watch();

  const handleDietaryChange = (id: string) => {
    const currentValues = form.getValues('dietaryRestrictions');
    const newValues = currentValues.includes(id)
      ? currentValues.filter(item => item !== id)
      : [...currentValues, id];
    
    form.setValue('dietaryRestrictions', newValues);
  };

  const handleCuisineChange = (id: string) => {
    const currentValues = form.getValues('favoriteCuisines');
    const newValues = currentValues.includes(id)
      ? currentValues.filter(item => item !== id)
      : [...currentValues, id];
    
    form.setValue('favoriteCuisines', newValues);
  };

  const handleAllergenChange = (id: string) => {
    const currentValues = form.getValues('allergens');
    const newValues = currentValues.includes(id)
      ? currentValues.filter(item => item !== id)
      : [...currentValues, id];
    
    form.setValue('allergens', newValues);
  };

  const handleSkillLevelChange = (value: string) => {
    form.setValue('cookingSkillLevel', value as 'beginner' | 'intermediate' | 'advanced');
  };

  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    try {
      setIsLoading(true);
      // Convert form values to UserPreferences type
      const userPreferences: UserPreferences = {
        dietaryRestrictions: values.dietaryRestrictions,
        favoriteCuisines: values.favoriteCuisines,
        allergens: values.allergens,
        cookingSkillLevel: values.cookingSkillLevel
      };
      
      updateUserPreferences(userPreferences);
      
      toast({
        title: "Preferences saved!",
        description: "Your recipe recommendations are now personalized.",
      });
      navigate('/');
    } catch (error) {
      toast({
        title: "Failed to save preferences",
        description: "Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="pt-24 md:pt-28">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 py-12 bg-white shadow-sm rounded-lg mt-8">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold">Your Recipe Preferences</h1>
            <p className="text-gray-500 mt-2">Tell us what you like, and we'll personalize your experience</p>
          </div>

          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
              <div>
                <h2 className="text-xl font-medium mb-4">Dietary Restrictions</h2>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {dietaryOptions.map((option) => (
                    <div key={option.id} className="flex items-center space-x-2">
                      <Checkbox 
                        id={`dietary-${option.id}`}
                        checked={preferences.dietaryRestrictions.includes(option.id)}
                        onCheckedChange={() => handleDietaryChange(option.id)}
                      />
                      <label 
                        htmlFor={`dietary-${option.id}`}
                        className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                      >
                        {option.label}
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h2 className="text-xl font-medium mb-4">Favorite Cuisines</h2>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {cuisineOptions.map((option) => (
                    <div key={option.id} className="flex items-center space-x-2">
                      <Checkbox 
                        id={`cuisine-${option.id}`}
                        checked={preferences.favoriteCuisines.includes(option.id)}
                        onCheckedChange={() => handleCuisineChange(option.id)}
                      />
                      <label 
                        htmlFor={`cuisine-${option.id}`}
                        className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                      >
                        {option.label}
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h2 className="text-xl font-medium mb-4">Allergens</h2>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {allergenOptions.map((option) => (
                    <div key={option.id} className="flex items-center space-x-2">
                      <Checkbox 
                        id={`allergen-${option.id}`}
                        checked={preferences.allergens.includes(option.id)}
                        onCheckedChange={() => handleAllergenChange(option.id)}
                      />
                      <label 
                        htmlFor={`allergen-${option.id}`}
                        className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                      >
                        {option.label}
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h2 className="text-xl font-medium mb-4">Cooking Skill Level</h2>
                <Select 
                  value={preferences.cookingSkillLevel} 
                  onValueChange={handleSkillLevelChange}
                >
                  <SelectTrigger className="w-full md:w-72">
                    <SelectValue placeholder="Select your cooking skill level" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="beginner">Beginner</SelectItem>
                    <SelectItem value="intermediate">Intermediate</SelectItem>
                    <SelectItem value="advanced">Advanced</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button 
                type="submit" 
                className="w-full md:w-auto"
                disabled={isLoading}
              >
                {isLoading ? "Saving..." : "Save Preferences"}
              </Button>
            </form>
          </Form>
        </div>
      </main>
    </div>
  );
};

export default UserPreferencesPage;
