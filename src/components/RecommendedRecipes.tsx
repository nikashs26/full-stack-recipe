
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { loadRecipes } from '../utils/storage';
import { fetchManualRecipes } from '../lib/manualRecipes';
import { useAuth } from '../context/AuthContext';
import RecipeCard from './RecipeCard';
import ManualRecipeCard from './ManualRecipeCard';
import { Recipe } from '../types/recipe';
import { SpoonacularRecipe } from '../types/spoonacular';
import { UserPreferences } from '../types/auth';
import { ThumbsUp, Loader2 } from 'lucide-react';
import { apiCall } from '../utils/apiUtils';

const RecommendedRecipes: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  
  // Check if user has meaningful preferences (not just empty arrays/strings)
  const hasMeaningfulPreferences = React.useMemo(() => {
    if (!user?.preferences) return false;
    
    const prefs = user.preferences;
    
    // Check if any preference arrays have actual content
    const hasFavoriteFoods = Array.isArray(prefs.favoriteFoods) && 
      prefs.favoriteFoods.some(food => food && food.trim() !== '');
    
    const hasFavoriteCuisines = Array.isArray(prefs.favoriteCuisines) && 
      prefs.favoriteCuisines.some(cuisine => cuisine && cuisine.trim() !== '');
    
    const hasDietaryRestrictions = Array.isArray(prefs.dietaryRestrictions) && 
      prefs.dietaryRestrictions.length > 0;
    
    const hasFoodsToAvoid = Array.isArray(prefs.foodsToAvoid) && 
      prefs.foodsToAvoid.some(food => food && food.trim() !== '');
    
    const hasCookingSkill = prefs.cookingSkillLevel && prefs.cookingSkillLevel !== 'beginner';
    
    const hasHealthGoals = Array.isArray(prefs.healthGoals) && 
      prefs.healthGoals.length > 0;
    
    // Return true if any meaningful preference is set
    return hasFavoriteFoods || hasFavoriteCuisines || hasDietaryRestrictions || 
           hasFoodsToAvoid || hasCookingSkill || hasHealthGoals;
  }, [user?.preferences]);
  
  // Query for local recipes
  const { data: allRecipes = [], isLoading: isLocalLoading } = useQuery({
    queryKey: ['localRecipes'],
    queryFn: loadRecipes,
  });

  // Query for manual recipes - use an empty search term to get all recipes
  const { data: manualRecipes = [], isLoading: isManualLoading } = useQuery({
    queryKey: ['recommendedManualRecipes'],
    queryFn: () => fetchManualRecipes(''), // Empty string to get all recipes
    placeholderData: (previousData) => previousData || [],
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Safely access user preferences with fallback to empty arrays
  const favoriteCuisines = user?.preferences?.favoriteCuisines || [];
  const dietaryRestrictions = user?.preferences?.dietaryRestrictions || [];
  
  console.log('RecommendedRecipes - User preferences:', { favoriteCuisines, dietaryRestrictions });

  // Query backend recommendations API
  const { data: recommendedRecipes = [], isLoading: isRecommendationsLoading } = useQuery({
    queryKey: ['recommendations', user?.preferences, hasMeaningfulPreferences],
    queryFn: async () => {
      if (!isAuthenticated || !user?.preferences) {
        console.log('No user preferences, returning empty recommendations');
        return [];
      }

      // Debug: Log the exact preferences being sent
      console.log('🔍 Sending preferences to recommendation API:', {
        favoriteFoods: user.preferences.favoriteFoods,
        favoriteCuisines: user.preferences.favoriteCuisines,
        dietaryRestrictions: user.preferences.dietaryRestrictions,
        hasMeaningfulPreferences,
        allPreferences: user.preferences
      });

      try {
        console.log('Fetching recommendations from backend with preferences:', user.preferences);
        
        const response = await apiCall('/recommendations?limit=12', {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          console.error('Failed to fetch recommendations:', response.status, response.statusText);
          return [];
        }

        const data = await response.json();
        console.log('Backend recommendations response:', data);
        
        return data.recommendations || [];
      } catch (error) {
        console.error('Error fetching recommendations:', error);
        return [];
      }
    },
    enabled: isAuthenticated && !!user?.preferences && hasMeaningfulPreferences,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Combine all recipes for display
  const allCombined = [
    ...recommendedRecipes.map(recipe => ({ ...recipe, type: 'external' as const })),
    ...manualRecipes.map(recipe => ({ ...recipe, type: 'manual' as const })),
    ...allRecipes.map(recipe => ({ ...recipe, type: 'saved' as const }))
  ];

  console.log(`Found ${allCombined.length} total recipes for recommendations:`, {
    recommended: recommendedRecipes.length,
    manual: manualRecipes.length,
    saved: allRecipes.length
  });

  // Don't show recommendations if no meaningful preferences are set
  if (!isAuthenticated || !user?.preferences || !hasMeaningfulPreferences) {
    console.log('No meaningful preferences found, not showing recommendations');
    return null;
  }

  // Don't show if still loading
  if (isRecommendationsLoading || isManualLoading || isLocalLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-gray-500" />
        <span className="ml-2 text-gray-500">Loading recommendations...</span>
      </div>
    );
  }

  // Don't show if no recipes found
  if (allCombined.length === 0) {
    return (
      <div className="text-center py-8">
        <ThumbsUp className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No recommendations yet</h3>
        <p className="text-gray-500 mb-4">
          Update your preferences to get better recommendations
        </p>
        <Link
          to="/preferences"
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
        >
          Update Preferences
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Recommended for You</h2>
          <p className="text-gray-600 mt-1">
            Based on your preferences
          </p>
        </div>
        <Link
          to="/preferences"
          className="text-sm text-blue-600 hover:text-blue-500"
        >
          Update preferences
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {allCombined.slice(0, 12).map((recipe) => {
          if (recipe.type === 'manual') {
            return (
              <ManualRecipeCard
                key={`manual-${recipe.id}`}
                recipe={recipe as Recipe}
                onDelete={() => {}}
                showDeleteButton={false}
              />
            );
          } else {
            return (
              <RecipeCard
                key={`${recipe.type}-${recipe.id}`}
                recipe={recipe as SpoonacularRecipe}
                type={recipe.type}
              />
            );
          }
        })}
      </div>

      {allCombined.length > 12 && (
        <div className="text-center">
          <Link
            to="/recipes"
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            View all recipes
          </Link>
        </div>
      )}
    </div>
  );
};

export default RecommendedRecipes;
