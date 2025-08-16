
import React, { useState } from 'react';
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
  console.log('🔍 RecommendedRecipes component rendered');
  
  const { user, isAuthenticated } = useAuth();
  
  // State for refresh feedback
  const [refreshFeedback, setRefreshFeedback] = useState<string>('');
  
  console.log('🔍 Component - isAuthenticated:', isAuthenticated);
  console.log('🔍 Component - user:', user);
  console.log('🔍 Component - user?.preferences:', user?.preferences);
  
  // Check if user has meaningful preferences (not just empty arrays/strings)
  const hasMeaningfulPreferences = React.useMemo(() => {
    if (!user?.preferences) {
      console.log('🔍 No user preferences found');
      return false;
    }
    
    const prefs = user.preferences;
    console.log('🔍 Checking preferences:', prefs);
    console.log('🔍 Preferences type:', typeof prefs);
    console.log('🔍 Preferences keys:', Object.keys(prefs));
    
    // For now, let's be more lenient - if user has any preferences object, show recommendations
    // This will help us debug what's actually happening
    const hasAnyPreferences = prefs && typeof prefs === 'object';
    
    console.log('🔍 Has any preferences:', hasAnyPreferences);
    return hasAnyPreferences;
  }, [user?.preferences]);
  
  // Query for local recipes
  const { data: allRecipes = [], isLoading: isLocalLoading } = useQuery({
    queryKey: ['localRecipes'],
    queryFn: loadRecipes,
  });

  // Query for manual recipes - use an empty search term to get all recipes
  const { data: manualRecipesData, isLoading: isManualLoading } = useQuery({
    queryKey: ['recommendedManualRecipes'],
    queryFn: async () => {
      const result = await fetchManualRecipes(''); // Empty string to get all recipes
      return result.recipes || []; // Extract just the recipes array
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const manualRecipes = manualRecipesData || [];
  
  // Safely access user preferences with fallback to empty arrays
  const favoriteCuisines = React.useMemo(() => user?.preferences?.favoriteCuisines || [], [user?.preferences?.favoriteCuisines]);
  const dietaryRestrictions = React.useMemo(() => user?.preferences?.dietaryRestrictions || [], [user?.preferences?.dietaryRestrictions]);
  
  console.log('RecommendedRecipes - User preferences:', { favoriteCuisines, dietaryRestrictions });

  // Handle refresh recommendations with feedback
  const handleRefreshRecommendations = async () => {
    setRefreshFeedback('Refreshing recommendations...');
    try {
      // Use React Query's refetch function to get fresh recommendations
      await refetchRecommendations();
      setRefreshFeedback('Recommendations refreshed!');
      // Clear feedback after 3 seconds
      setTimeout(() => setRefreshFeedback(''), 3000);
    } catch (error) {
      setRefreshFeedback('Failed to refresh recommendations');
      // Clear error feedback after 3 seconds
      setTimeout(() => setRefreshFeedback(''), 3000);
    }
  };

  // Query for backend recommendations
  const { data: recommendedRecipes = [], isLoading: isRecommendationsLoading, refetch: refetchRecommendations } = useQuery({
    queryKey: ['recommendations', user?.preferences?.favoriteCuisines?.join(','), user?.preferences?.favoriteFoods?.join(',')], // Stable key based on preferences
    queryFn: async () => {
      try {
        console.log('🔍 Fetching recommendations from backend...');
        
        const response = await fetch('/api/smart-features/recommendations', {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          }
        });

        console.log('🔍 API response status:', response.status);
        console.log('🔍 API response ok:', response.ok);

        if (!response.ok) {
          console.error('❌ Failed to fetch recommendations:', response.status, response.statusText);
          return [];
        }

        const data = await response.json();
        console.log('✅ Backend recommendations response:', data);
        console.log('✅ Backend recommendations array:', data.recommendations);
        
        // Analyze the recommendations for balance
        if (data.recommendations && Array.isArray(data.recommendations)) {
          const cuisineCounts: Record<string, number> = {};
          const favoriteFoodMatches: string[] = [];
          
          data.recommendations.forEach((recipe: any) => {
            const cuisine = recipe.cuisine || 'Unknown';
            cuisineCounts[cuisine] = (cuisineCounts[cuisine] || 0) + 1;
            
            // Check for favorite food matches
            if (user?.preferences?.favoriteFoods) {
              const recipeText = `${recipe.title || recipe.name || ''} ${recipe.description || ''}`.toLowerCase();
              const hasFavoriteFood = user.preferences.favoriteFoods.some((food: string) => 
                recipeText.includes(food.toLowerCase())
              );
              if (hasFavoriteFood) {
                favoriteFoodMatches.push(recipe.title || recipe.name || 'Unknown');
              }
            }
          });
          
          console.log('📊 Recommendation Analysis:');
          console.log('   • Total recipes:', data.recommendations.length);
          console.log('   • Cuisine distribution:', cuisineCounts);
          console.log('   • Favorite food matches:', favoriteFoodMatches.length);
          
          // Check balance
          const counts = Object.values(cuisineCounts);
          if (counts.length > 1) {
            const maxCount = Math.max(...counts);
            const minCount = Math.min(...counts);
            const balanceRatio = maxCount / minCount;
            
            console.log('   • Balance ratio:', balanceRatio.toFixed(2));
            if (balanceRatio > 3) {
              console.warn('   ⚠️ Recommendations may be imbalanced');
            } else if (balanceRatio > 2) {
              console.log('   ⚠️ Moderate imbalance detected');
            } else {
              console.log('   ✅ Good balance');
            }
          }
        }
        
        console.log('✅ First recipe details:', data.recommendations?.[0] ? {
          id: data.recommendations[0].id,
          title: data.recommendations[0].title,
          name: data.recommendations[0].name,
          cuisine: data.recommendations[0].cuisine
        } : 'No recipes');
        
        return data.recommendations || [];
      } catch (error) {
        console.error('❌ Error fetching recommendations:', error);
        return [];
      }
    },
    enabled: isAuthenticated && !!user?.preferences,
    staleTime: Infinity, // Never consider data stale - only refresh manually
    gcTime: Infinity, // Keep in cache indefinitely
    refetchOnWindowFocus: false, // Don't refetch when window regains focus
    refetchOnMount: false, // Don't refetch when component mounts
    refetchOnReconnect: false, // Don't refetch when reconnecting to network
  });

  console.log('🔍 Query enabled:', isAuthenticated && !!user?.preferences);
  console.log('🔍 isAuthenticated:', isAuthenticated);
  console.log('🔍 user?.preferences:', user?.preferences);

  // Memoize the combined recipes to prevent unnecessary re-computations
  const allCombined = React.useMemo(() => {
    const combined = [
      ...recommendedRecipes.map(recipe => ({ 
        ...recipe, 
        type: 'external' as const,
        priority: 1
      })),
      ...manualRecipes.map(recipe => ({ 
        ...recipe, 
        type: 'manual' as const,
        priority: 2
      })),
      ...allRecipes.map(recipe => ({ 
        ...recipe, 
        type: 'saved' as const,
        priority: 3
      }))
    ];
    
    // Sort by priority to ensure backend recommendations come first
    combined.sort((a, b) => (a.priority || 3) - (b.priority || 3));
    
    return combined;
  }, [recommendedRecipes, manualRecipes, allRecipes]);

  // Debug: Log what each source is providing
  console.log('🔍 Recipe sources debug:');
  console.log('Backend recommendations:', recommendedRecipes.slice(0, 2).map(r => ({ id: r.id, title: r.title, name: r.name, type: 'external' })));
  console.log('Manual recipes:', manualRecipes.slice(0, 2).map(r => ({ id: r.id, title: r.title, name: (r as any).name, type: 'manual' })));
  console.log('Local recipes:', allRecipes.slice(0, 2).map(r => ({ id: r.id, title: r.title, name: (r as any).name, type: 'saved' })));
  console.log('Combined result:', allCombined.slice(0, 3).map(r => ({ id: r.id, title: r.title, name: (r as any).name, type: r.type })));

  console.log(`Found ${allCombined.length} total recipes for recommendations:`, {
    recommended: recommendedRecipes.length,
    manual: manualRecipes.length,
    saved: allRecipes.length
  });

  // Don't show recommendations if no meaningful preferences are set
  if (!isAuthenticated || !user?.preferences) { // Temporarily removed hasMeaningfulPreferences check
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
        <div className="flex items-center space-x-4">
          <button
            onClick={handleRefreshRecommendations}
            disabled={isRecommendationsLoading}
            className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isRecommendationsLoading ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            )}
            Refresh
          </button>
          <Link
            to="/preferences"
            className="text-sm text-blue-600 hover:text-blue-500"
          >
            Update preferences
          </Link>
        </div>
      </div>
      
      {/* Refresh feedback */}
      {refreshFeedback && (
        <div className={`text-sm font-medium mb-4 px-4 py-2 rounded-md ${
          refreshFeedback.includes('Failed') 
            ? 'bg-red-100 text-red-700 border border-red-200' 
            : refreshFeedback.includes('Refreshing')
            ? 'bg-blue-100 text-blue-700 border border-blue-200'
            : 'bg-green-100 text-green-700 border border-green-200'
        }`}>
          {refreshFeedback}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {allCombined.slice(0, 12).map((recipe) => {
                      if (recipe.type === 'manual') {
              return (
                <ManualRecipeCard
                  key={`manual-${recipe.id}`}
                  recipe={recipe as Recipe}
                />
              );
            } else {
              return (
                <RecipeCard
                  key={`${recipe.type}-${recipe.id}`}
                  recipe={recipe as Recipe}
                  isExternal={recipe.type === 'external'}
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
