
import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { loadRecipes } from '../utils/storage';
import { useAuth } from '../context/AuthContext';
import RecipeCard from './RecipeCard';
import { Recipe } from '../types/recipe';
import { ThumbsUp } from 'lucide-react';

const RecommendedRecipes: React.FC = () => {
  const { user } = useAuth();
  const { data: allRecipes = [], isLoading } = useQuery({
    queryKey: ['localRecipes'],
    queryFn: loadRecipes,
  });

  if (!user?.preferences || !Array.isArray(allRecipes) || allRecipes.length === 0) {
    return null;
  }

  // Filter recipes based on user preferences
  const recommendedRecipes = allRecipes.filter((recipe: Recipe) => {
    // For cuisine preferences - match any of user's favorites
    const hasFavoriteCuisine = user.preferences?.favoriteCuisines?.some(c => 
      recipe.cuisine?.toLowerCase().includes(c.toLowerCase())
    );
    
    // Check for dietary restrictions - if user has restrictions, recipe must match them
    const matchesDietaryNeeds = !user.preferences?.dietaryRestrictions?.length || 
      user.preferences.dietaryRestrictions.some(restriction => 
        recipe.dietaryRestrictions?.includes(restriction as any)
      );
    
    // Check for allergens - don't recommend recipes with user's allergens
    const hasAllergen = user.preferences?.allergens?.some(allergen => 
      recipe.ingredients?.some(ingredient => 
        ingredient?.toLowerCase().includes(allergen.toLowerCase())
      )
    );

    // Consider cooking skill level
    const skillLevelMatch = recipe.difficulty === undefined || 
      (user.preferences?.cookingSkillLevel === 'beginner' && recipe.difficulty !== 'hard') ||
      (user.preferences?.cookingSkillLevel === 'intermediate') ||
      (user.preferences?.cookingSkillLevel === 'advanced');

    // Recipe is recommended if it matches cuisine OR dietary needs, doesn't have allergens, and matches skill level
    return (hasFavoriteCuisine || matchesDietaryNeeds) && !hasAllergen && skillLevelMatch;
  }).slice(0, 3);

  if (recommendedRecipes.length === 0) {
    return (
      <section className="mb-16">
        <h2 className="text-3xl font-bold text-gray-900 flex items-center mb-6">
          <ThumbsUp className="mr-2 h-6 w-6 text-recipe-secondary" />
          Recommended for You
        </h2>
        <div className="text-center p-8 border border-dashed border-gray-300 rounded-lg">
          <p className="text-gray-500">No recommendations match your preferences yet.</p>
          <p className="text-gray-500 mt-2">Try adjusting your preferences or adding more recipes.</p>
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
        <Link to="/recipes" className="text-recipe-primary hover:text-recipe-primary/80">
          View all →
        </Link>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-64 bg-gray-200 animate-pulse rounded-lg"></div>
          ))
        ) : recommendedRecipes.length > 0 ? (
          recommendedRecipes.map((recipe, i) => (
            <RecipeCard 
              key={i}
              recipe={recipe}
              isExternal={false}
              onDelete={handleDeleteRecipe}
            />
          ))
        ) : (
          <div className="col-span-full text-center py-12 border border-dashed border-gray-300 rounded-lg">
            <p className="text-gray-500">No recommended recipes available</p>
          </div>
        )}
      </div>
    </section>
  );
};

export default RecommendedRecipes;
