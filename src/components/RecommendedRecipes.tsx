
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { loadRecipes } from '../utils/storage';
import { fetchRecipes } from '../lib/spoonacular';
import { useAuth } from '../context/AuthContext';
import RecipeCard from './RecipeCard';
import { Recipe } from '../types/recipe';
import { SpoonacularRecipe } from '../types/spoonacular';
import { ThumbsUp, Loader2 } from 'lucide-react';

// Define a type that combines Recipe and SpoonacularRecipe with isExternal flag
type CombinedRecipe = (Recipe & { isExternal?: boolean }) | (SpoonacularRecipe & { isExternal: boolean });

const RecommendedRecipes: React.FC = () => {
  const { user } = useAuth();
  
  // Query for local recipes
  const { data: allRecipes = [], isLoading: isLocalLoading } = useQuery({
    queryKey: ['localRecipes'],
    queryFn: loadRecipes,
  });

  // Build search queries based on user preferences
  const searchQueries = React.useMemo(() => {
    if (!user?.preferences) return [];
    
    const queries = [];
    
    // Add cuisine-based searches
    if (user.preferences.favoriteCuisines?.length > 0) {
      queries.push(...user.preferences.favoriteCuisines.slice(0, 2)); // Limit to avoid too many API calls
    }
    
    // Add dietary restriction searches
    if (user.preferences.dietaryRestrictions?.length > 0) {
      queries.push(...user.preferences.dietaryRestrictions.slice(0, 2));
    }
    
    // If no specific preferences, add some general queries
    if (queries.length === 0) {
      queries.push('quick', 'easy');
    }
    
    return queries.slice(0, 3); // Limit total queries
  }, [user?.preferences]);

  // Query external recipes based on user preferences
  const externalQueries = useQuery({
    queryKey: ['recommendedExternalRecipes', searchQueries],
    queryFn: async () => {
      if (searchQueries.length === 0) return [];
      
      const allExternalRecipes: SpoonacularRecipe[] = [];
      
      // Fetch recipes for each preference-based query
      for (const query of searchQueries) {
        try {
          const response = await fetchRecipes(query, '');
          if (response?.results) {
            allExternalRecipes.push(...response.results.slice(0, 4)); // 4 recipes per query
          }
        } catch (error) {
          console.error(`Error fetching recipes for query "${query}":`, error);
        }
      }
      
      return allExternalRecipes;
    },
    enabled: searchQueries.length > 0,
    staleTime: 300000, // Cache for 5 minutes
  });

  // Filter and combine local and external recipes
  const recommendedRecipes = React.useMemo(() => {
    if (!user?.preferences) return [];

    const combinedRecipes: CombinedRecipe[] = [];

    // Filter local recipes based on preferences
    if (Array.isArray(allRecipes) && allRecipes.length > 0) {
      const filteredLocal = allRecipes.filter((recipe: Recipe) => {
        // Check cuisine preferences
        const hasFavoriteCuisine = !user.preferences?.favoriteCuisines?.length || 
          user.preferences.favoriteCuisines.some(c => 
            recipe.cuisine?.toLowerCase().includes(c.toLowerCase())
          );
        
        // Check dietary restrictions
        const matchesDietaryNeeds = !user.preferences?.dietaryRestrictions?.length || 
          user.preferences.dietaryRestrictions.some(restriction => 
            recipe.dietaryRestrictions?.includes(restriction as any)
          );
        
        // Check for allergens - exclude recipes with user's allergens
        const hasAllergen = user.preferences?.allergens?.some(allergen => 
          recipe.ingredients?.some(ingredient => 
            ingredient?.toLowerCase().includes(allergen.toLowerCase())
          )
        );

        // Consider cooking skill level
        let skillLevelMatch = true;
        if (user.preferences?.cookingSkillLevel && recipe.difficulty) {
          if (user.preferences.cookingSkillLevel === 'beginner') {
            skillLevelMatch = recipe.difficulty !== 'hard';
          }
          // Intermediate and advanced users can handle all recipes
        }

        return (hasFavoriteCuisine || matchesDietaryNeeds) && !hasAllergen && skillLevelMatch;
      }).slice(0, 6);

      combinedRecipes.push(...filteredLocal.map(recipe => ({ ...recipe, isExternal: false })));
    }

    // Add external recipes with preference filtering
    if (externalQueries.data && Array.isArray(externalQueries.data)) {
      const filteredExternal = externalQueries.data.filter((recipe: SpoonacularRecipe) => {
        // Check dietary restrictions for external recipes
        const matchesDietaryNeeds = !user.preferences?.dietaryRestrictions?.length || 
          user.preferences.dietaryRestrictions.some(restriction => 
            recipe.diets?.some(diet => 
              diet?.toLowerCase().includes(restriction.toLowerCase())
            )
          );
        
        // Check cuisine preferences for external recipes
        const hasFavoriteCuisine = !user.preferences?.favoriteCuisines?.length || 
          user.preferences.favoriteCuisines.some(c => 
            recipe.cuisines?.some(cuisine => 
              cuisine?.toLowerCase().includes(c.toLowerCase())
            )
          );

        // Check for allergens in external recipes
        const hasAllergen = user.preferences?.allergens?.some(allergen => 
          recipe.title?.toLowerCase().includes(allergen.toLowerCase()) ||
          recipe.summary?.toLowerCase().includes(allergen.toLowerCase())
        );

        // Consider cooking skill level for external recipes
        let skillLevelMatch = true;
        if (user.preferences?.cookingSkillLevel === 'beginner' && recipe.readyInMinutes) {
          skillLevelMatch = recipe.readyInMinutes <= 45; // Beginner-friendly: under 45 minutes
        }

        return (hasFavoriteCuisine || matchesDietaryNeeds) && !hasAllergen && skillLevelMatch;
      }).slice(0, 6);

      combinedRecipes.push(...filteredExternal.map(recipe => ({ ...recipe, isExternal: true })));
    }

    // Remove duplicates and shuffle for variety
    const uniqueRecipes = combinedRecipes.filter((recipe, index, self) => 
      index === self.findIndex(r => r.id === recipe.id)
    );

    // Sort by relevance and limit to 6 total
    return uniqueRecipes
      .sort(() => Math.random() - 0.5) // Shuffle for variety
      .slice(0, 6);
  }, [allRecipes, externalQueries.data, user?.preferences]);

  if (!user?.preferences) {
    return null;
  }

  const isLoading = isLocalLoading || externalQueries.isLoading;

  if (recommendedRecipes.length === 0 && !isLoading) {
    return (
      <section className="mb-16">
        <h2 className="text-3xl font-bold text-gray-900 flex items-center mb-6">
          <ThumbsUp className="mr-2 h-6 w-6 text-recipe-secondary" />
          Recommended for You
        </h2>
        <div className="text-center p-8 border border-dashed border-gray-300 rounded-lg">
          <p className="text-gray-500">
            We're finding recipes that match your preferences...
          </p>
          <p className="text-gray-500 mt-2">
            Your preferences: {user.preferences.favoriteCuisines?.join(', ')} cuisines, 
            {user.preferences.dietaryRestrictions?.join(', ')} dietary needs
          </p>
          <Link 
            to="/preferences" 
            className="text-recipe-primary hover:text-recipe-primary/80 underline mt-2 inline-block"
          >
            Update your preferences
          </Link>
        </div>
      </section>
    );
  }

  // Skip recipe delete functionality on homepage
  const handleDeleteRecipe = () => {
    // This is intentionally empty as we don't want delete functionality on these cards
  };

  return (
    <section className="mb-16">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-bold text-gray-900 flex items-center">
          <ThumbsUp className="mr-2 h-6 w-6 text-recipe-secondary" />
          Recommended for You
        </h2>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-500">
            Based on your {user.preferences.favoriteCuisines?.length || 0} cuisine preferences
          </span>
          <Link to="/recipes" className="text-recipe-primary hover:text-recipe-primary/80">
            View all →
          </Link>
        </div>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {isLoading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-64 bg-gray-200 animate-pulse rounded-lg flex items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            </div>
          ))
        ) : recommendedRecipes.length > 0 ? (
          recommendedRecipes.map((recipe, i) => (
            <RecipeCard 
              key={`recommended-${recipe.id}-${i}`}
              recipe={recipe}
              isExternal={!!recipe.isExternal}
              onDelete={handleDeleteRecipe}
            />
          ))
        ) : (
          <div className="col-span-full text-center py-12 border border-dashed border-gray-300 rounded-lg">
            <p className="text-gray-500">No recommended recipes available</p>
            <Link 
              to="/preferences" 
              className="text-recipe-primary hover:text-recipe-primary/80 underline mt-2 inline-block"
            >
              Update your preferences to get recommendations
            </Link>
          </div>
        )}
      </div>
    </section>
  );
};

export default RecommendedRecipes;
