
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '@/hooks/use-toast';
import Header from '../components/Header';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Form } from '@/components/ui/form';
import { UserPreferences } from '../types/auth';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

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

const UserPreferencesPage: React.FC = () => {
  const { user, updateUserPreferences } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(false);
  
  const [preferences, setPreferences] = useState<UserPreferences>({
    dietaryRestrictions: user?.preferences?.dietaryRestrictions || [],
    favoriteCuisines: user?.preferences?.favoriteCuisines || [],
    allergens: user?.preferences?.allergens || [],
    cookingSkillLevel: user?.preferences?.cookingSkillLevel || 'beginner'
  });

  const handleDietaryChange = (id: string) => {
    setPreferences(prev => {
      const currentPrefs = [...prev.dietaryRestrictions];
      if (currentPrefs.includes(id)) {
        return {
          ...prev,
          dietaryRestrictions: currentPrefs.filter(item => item !== id)
        };
      } else {
        return {
          ...prev,
          dietaryRestrictions: [...currentPrefs, id]
        };
      }
    });
  };

  const handleCuisineChange = (id: string) => {
    setPreferences(prev => {
      const currentPrefs = [...prev.favoriteCuisines];
      if (currentPrefs.includes(id)) {
        return {
          ...prev,
          favoriteCuisines: currentPrefs.filter(item => item !== id)
        };
      } else {
        return {
          ...prev,
          favoriteCuisines: [...currentPrefs, id]
        };
      }
    });
  };

  const handleAllergenChange = (id: string) => {
    setPreferences(prev => {
      const currentPrefs = [...prev.allergens];
      if (currentPrefs.includes(id)) {
        return {
          ...prev,
          allergens: currentPrefs.filter(item => item !== id)
        };
      } else {
        return {
          ...prev,
          allergens: [...currentPrefs, id]
        };
      }
    });
  };

  const handleSkillLevelChange = (value: string) => {
    setPreferences(prev => ({
      ...prev,
      cookingSkillLevel: value as 'beginner' | 'intermediate' | 'advanced'
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsLoading(true);
      updateUserPreferences(preferences);
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

          <Form>
            <form onSubmit={handleSubmit} className="space-y-8">
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
