import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import Header from '../components/Header';
import { loadRecipes } from '../utils/storage';
import { fetchRecipes } from '../lib/spoonacular';
import { fetchManualRecipes } from '../lib/manualRecipes';
import { Recipe } from '../types/recipe';
import { SpoonacularRecipe } from '../types/spoonacular';
import RecipeCard from '../components/RecipeCard'; // Default import
import ManualRecipeCard from '../components/ManualRecipeCard';
import { getAverageRating, getDietaryTags, formatExternalRecipeCuisine } from '../utils/recipeUtils';
import { ChefHat, TrendingUp, Award, Clock, Search, ThumbsUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
// import { useAuth } from '../context/AuthContext'; // Commented out for testing
import { UserPreferences } from '../types/auth'; // Ensure UserPreferences is imported

const HomePage: React.FC = () => {
  // const { isAuthenticated, user } = useAuth(); // Commented out for testing
  // For testing purposes, we'll simulate a user and preferences directly within HomePage.
  // This bypasses AuthContext's logic for fetching/managing user.
  const [userPreferences, setUserPreferences] = useState<UserPreferences | null>(null);
  const testUserId = "test_user_id";

  // Simulate fetching preferences for the test user (from backend)
  useEffect(() => {
    const fetchPreferences = async () => {
      try {
        // Assuming /api/preferences is accessible without auth and returns test user's preferences
        const response = await fetch('/api/preferences'); 
        if (response.ok) {
          const data = await response.json();
          if (data.preferences) {
            setUserPreferences(data.preferences);
            console.log("HomePage: Fetched test user preferences:", data.preferences);
          }
        } else {
          console.error("HomePage: Failed to fetch test user preferences:", response.statusText);
          setUserPreferences({}); // Set to empty object if not found or error, to enable queries
        }
      } catch (error) {
        console.error("HomePage: Error fetching test user preferences:", error);
        setUserPreferences({}); // Set to empty object on error
      }
    };
    fetchPreferences();
  }, []);

  // Query for local recipes
  const { data: localRecipes = [], isLoading: isLocalLoading } = useQuery<Recipe[]>(
    ['localRecipes'],
    loadRecipes,
    { staleTime: 60000 }
  );

  // Query for manual recipes with better error handling
  const { data: manualRecipes = [], isLoading: isManualLoading, error: manualError } = useQuery<any[]>(
    ['manualRecipes'],
    async () => {
      try {
        const recipes = await fetchManualRecipes();
        return recipes;
      } catch (error) {
        console.error("Error fetching manual recipes:", error);
        return [];
      }
    },
    { staleTime: 60000, retry: 2 }
  );

  // Query for recommended external recipes based on user preferences
  const { data: externalRecommendedRecipes = [], isLoading: isRecommendedExternalLoading } = useQuery<SpoonacularRecipe[]>(
    ['externalRecommendedRecipes', userPreferences], // Re-fetch when preferences change
    async () => {
      if (!userPreferences) return []; // Don't fetch if preferences are not loaded yet

      const allExternalRecipes: SpoonacularRecipe[] = [];
      const { favoriteCuisines = [], dietaryRestrictions = [] } = userPreferences;

      try {
        // Fetch recipes for favorite cuisines
        if (favoriteCuisines.length > 0) {
          for (const cuisine of favoriteCuisines.slice(0, 2)) { // Limit to 2 cuisines for speed
            const response = await fetchRecipes('', cuisine);
            if (response?.results && Array.isArray(response.results)) {
              const realRecipes = response.results.filter(recipe =>
                recipe.id > 1000 &&
                recipe.title &&
                !recipe.title.toLowerCase().includes('fallback') &&
                recipe.image &&
                recipe.image.includes('http')
              );
              allExternalRecipes.push(...realRecipes.slice(0, 4)); // Get top 4 from each
            }
          }
        }

        // Fetch recipes for dietary restrictions
        if (dietaryRestrictions.length > 0) {
          for (const diet of dietaryRestrictions.slice(0, 2)) { // Limit to 2 diets for speed
            const response = await fetchRecipes(diet, '');
            if (response?.results && Array.isArray(response.results)) {
              const realRecipes = response.results.filter(recipe =>
                recipe.id > 1000 &&
                recipe.title &&
                !recipe.title.toLowerCase().includes('fallback') &&
                recipe.image &&
                recipe.image.includes('http')
              );
              allExternalRecipes.push(...realRecipes.slice(0, 3)); // Get top 3 from each
            }
          }
        }

        // Remove duplicates by id
        const seenIds = new Set();
        const uniqueRecommended = allExternalRecipes.filter(recipe => {
          if (seenIds.has(recipe.id)) return false;
          seenIds.add(recipe.id);
          return true;
        });

        return uniqueRecommended.slice(0, 8); // Limit total recommendations
      } catch (e) {
        console.error("Error fetching recommended external recipes:", e);
        return [];
      }
    },
    // Only run this query if preferences are loaded (even if empty) and a 'user' exists (simulated)
    enabled: userPreferences !== null, // Enable if preferences are fetched
    staleTime: 300000,
    cacheTime: 3600000 // Cache for 1 hour
  );

  // Query for featured external recipes (always fetch)
  const { data: featuredExternalRecipes = [], isLoading: isFeaturedExternalLoading } = useQuery<SpoonacularRecipe[]>(
    ['featuredExternalRecipes'],
    async () => {
      try {
        const [pastaResult, chickenResult, vegetarianResult] = await Promise.all([
          fetchRecipes('pasta', 'Italian').catch(() => ({ results: [] })),
          fetchRecipes('chicken', '').catch(() => ({ results: [] })),
          fetchRecipes('vegetarian', '').catch(() => ({ results: [] }))
        ]);
        
        const allRecipes = [
          ...(pastaResult?.results || []),
          ...(chickenResult?.results || []),
          ...(vegetarianResult?.results || []),
        ];
        
        const seenIds = new Set();
        const uniqueRecipes = allRecipes
          .filter(recipe => {
            if (!recipe || !recipe.id || seenIds.has(recipe.id)) return false;
            seenIds.add(recipe.id);
            return recipe.title && 
                   !recipe.title.toLowerCase().includes('fallback') &&
                   recipe.image;
          });
        
        return uniqueRecipes.slice(0, 12); // Limit number of featured recipes
      } catch (error) {
        console.error('Featured recipes failed:', error);
        return [];
      }
    },
    { staleTime: 300000 }
  );

  // Global deduplication system for displaying recipes on HomePage
  const processedRecipes = useMemo(() => {
    const globalSeenTitles = new Set<string>();
    const globalSeenIds = new Set<string | number>();

    const normalizeTitle = (title: string) => {
      return title.toLowerCase().trim().replace(/[^a-z0-9\s]/g, '').replace(/\s+/g, ' ');
    };
    
    const isRecipeSeen = (recipe: any, type: string) => {
      const normalizedTitle = normalizeTitle(recipe.title || recipe.name || '');
      const recipeId = `${type}-${recipe.id}`;
      
      if (!normalizedTitle || globalSeenTitles.has(normalizedTitle) || globalSeenIds.has(recipeId)) {
        return true;
      }
      
      globalSeenTitles.add(normalizedTitle);
      globalSeenIds.add(recipeId);
      return false;
    };

    const popularRecipes: any[] = [];
    if (Array.isArray(manualRecipes) && manualRecipes.length > 0) {
      for (const recipe of manualRecipes) {
        if (popularRecipes.length >= 8) break;
        if (!isRecipeSeen(recipe, 'manual')) {
          popularRecipes.push({
            ...recipe,
            image: recipe.image || '/placeholder.svg'
          });
        }
      }
    }

    const featuredRecipes: SpoonacularRecipe[] = [];
    if (Array.isArray(featuredExternalRecipes) && featuredExternalRecipes.length > 0) {
      for (const recipe of featuredExternalRecipes) {
        if (featuredRecipes.length >= 8) break;
        if (!isRecipeSeen(recipe, 'external')) {
          featuredRecipes.push({
            ...recipe,
            image: recipe.image || '/placeholder.svg',
            isExternal: true
          });
        }
      }
    }

    const topRatedRecipes: Recipe[] = [];
    if (Array.isArray(localRecipes) && localRecipes.length > 0) {
      const sortedByRating = [...localRecipes]
        .filter(recipe => recipe?.ratings?.length)
        .sort((a, b) => {
          const ratingA = getAverageRating(a.ratings || []);
          const ratingB = getAverageRating(b.ratings || []);
          return ratingB - ratingA;
        });

      for (const recipe of sortedByRating) {
        if (topRatedRecipes.length >= 8) break;
        if (!isRecipeSeen(recipe, 'local')) {
          topRatedRecipes.push(recipe);
        }
      }
    }

    const recentRecipes: Recipe[] = [];
    if (Array.isArray(localRecipes) && localRecipes.length > 0) {
      const sortedByDate = [...localRecipes]
        .sort((a, b) => {
          const dateA = a.createdAt ? new Date(a.createdAt).getTime() : 0;
          const dateB = b.createdAt ? new Date(b.createdAt).getTime() : 0;
          return dateB - dateA;
        });

      for (const recipe of sortedByDate) {
        if (recentRecipes.length >= 8) break;
        if (!isRecipeSeen(recipe, 'local-recent')) {
          recentRecipes.push(recipe);
        }
      }
    }

    return {
      popularRecipes,
      featuredRecipes,
      topRatedRecipes,
      recentRecipes,
      recommendedRecipes: externalRecommendedRecipes // Add recommended from external
    };
  }, [localRecipes, manualRecipes, featuredExternalRecipes, externalRecommendedRecipes]);

  const handleDeleteRecipe = (id: string) => {
    console.log(`Delete recipe not implemented for ID: ${id}`);
    // This will typically trigger a toast or modal for confirmation in a full app.
  };

  const handleToggleFavorite = (recipe: Recipe) => {
    console.log(`Toggle favorite not implemented for recipe: ${recipe.name}`);
    // This would typically dispatch an action to update favorite status.
  };

  const isLoading = isLocalLoading || isManualLoading || isRecommendedExternalLoading || isFeaturedExternalLoading;
  const error = manualError; // Propagate manual error to display generic error if needed

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="pt-24 md:pt-28">
        {/* Hero Section */}
        <section className="relative bg-gradient-to-r from-recipe-accent to-recipe-primary py-16 md:py-24">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
                Discover Delicious Recipes
              </h1>
              <p className="text-xl text-white/90 mb-8 max-w-3xl mx-auto">
                Your personalized recipe collection awaits
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link to="/recipes">
                  <Button size="lg" variant="secondary" className="w-full sm:w-auto">
                    <Search className="mr-2 h-4 w-4" />
                    Browse All Recipes
                  </Button>
                </Link>
                {/* Removed isAuthenticated conditional rendering for Preferences, Sign In, Sign Up */}
                <Link to="/preferences">
                  <Button size="lg" variant="outline" className="w-full sm:w-auto bg-white/10 text-white hover:bg-white/20">
                    <ChefHat className="mr-2 h-4 w-4" />
                    Update Preferences
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </section>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          {/* Recommended Recipes Section - Always show, based on simulated preferences */}
          <section className="mb-16">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-3xl font-bold text-gray-900 flex items-center">
                <ThumbsUp className="mr-2 h-6 w-6 text-recipe-secondary" />
                Recommended for You
              </h2>
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-500">
                  Based on your preferences
                </span>
                <Link to="/recipes" className="text-recipe-primary hover:text-recipe-primary/80">
                  View all →
                </Link>
              </div>
              
              {isLoading ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                  {Array.from({ length: 8 }).map((_, i) => (
                    <div key={i} className="h-64 bg-gray-200 animate-pulse rounded-lg"></div>
                  ))}
                </div>
              ) : processedRecipes.recommendedRecipes.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                  {processedRecipes.recommendedRecipes.map((recipe, i) => (
                    <RecipeCard 
                      key={`recommended-${recipe.id}-${i}`}
                      recipe={recipe}
                      isExternal={true}
                      onDelete={handleDeleteRecipe}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 border border-dashed border-gray-300 rounded-lg">
                  <p className="text-gray-500 mb-2">No recommendations available right now</p>
                  <p className="text-sm text-gray-400">Check back soon for new recipes based on your preferences!</p>
                </div>
              )}
            </section>
          
          {/* Popular Manual Recipes - Always show */}
          <section className="mb-16">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-3xl font-bold text-gray-900 flex items-center">
                <Award className="mr-2 h-6 w-6 text-recipe-secondary" />
                Popular Recipes
              </h2>
              <Link to="/recipes" className="text-recipe-primary hover:text-recipe-primary/80">
                View all →
              </Link>
            </div>
            
            {isManualLoading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} className="h-64 bg-gray-200 animate-pulse rounded-lg"></div>
                ))}
              </div>
            ) : error ? (
              <div className="text-center py-12 border border-dashed border-gray-300 rounded-lg">
                <p className="text-gray-500 mb-2">Unable to load popular recipes</p>
                <p className="text-sm text-gray-400">Please try refreshing the page</p>
              </div>
            ) : processedRecipes.popularRecipes.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {processedRecipes.popularRecipes.map((recipe, i) => (
                  <ManualRecipeCard key={`popular-${recipe.id}-${i}`} recipe={recipe} />
                ))}
              </div>
            ) : (
              <div className="text-center py-12 border border-dashed border-gray-300 rounded-lg">
                <p className="text-gray-500 mb-2">No popular recipes available yet</p>
                <p className="text-sm text-gray-400">Check back soon for new recipes!</p>
              </div>
            )}
          </section>

          {/* Featured External Recipes */}
          <section className="mb-16">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-3xl font-bold text-gray-900 flex items-center">
                <ChefHat className="mr-2 h-6 w-6 text-recipe-secondary" />
                Newly Added Recipes
              </h2>
              <Link to="/recipes" className="text-recipe-primary hover:text-recipe-primary/80">
                View all →
              </Link>
            </div>
            
            {isFeaturedExternalLoading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} className="h-64 bg-gray-200 animate-pulse rounded-lg"></div>
                ))}
              </div>
            ) : processedRecipes.featuredRecipes.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {processedRecipes.featuredRecipes.map((recipe, i) => (
                  <RecipeCard 
                    key={`featured-${recipe.id}-${i}`}
                    recipe={recipe}
                    isExternal={true}
                    onDelete={handleDeleteRecipe}
                  />
                ))}
              </div>
            ) : (
              <div className="text-center py-12 border border-dashed border-gray-300 rounded-lg">
                <p className="text-gray-500">Loading featured recipes...</p>
              </div>
            )}
          </section>

          {/* Top Rated Section */}
          {processedRecipes.topRatedRecipes.length > 0 && (
            <section className="mb-16">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-3xl font-bold text-gray-900 flex items-center">
                  <TrendingUp className="mr-2 h-6 w-6 text-recipe-secondary" />
                  Top Rated Recipes
                </h2>
                <Link to="/recipes" className="text-recipe-primary hover:text-recipe-primary/80">
                  View all →
                </Link>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {processedRecipes.topRatedRecipes.map((recipe, i) => (
                  <RecipeCard 
                    key={`top-rated-${recipe.id}-${i}`}
                    recipe={recipe}
                    isExternal={false}
                    onDelete={handleDeleteRecipe}
                    onToggleFavorite={handleToggleFavorite}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Recently Added Section */}
          {processedRecipes.recentRecipes.length > 0 && (
            <section className="mb-8">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-3xl font-bold text-gray-900 flex items-center">
                  <Clock className="mr-2 h-6 w-6 text-recipe-secondary" />
                  Recently Added
                </h2>
                <Link to="/recipes" className="text-recipe-primary hover:text-recipe-primary/80">
                  View all →
                </Link>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {processedRecipes.recentRecipes.map((recipe, i) => (
                  <RecipeCard 
                    key={`recent-${recipe.id}-${i}`}
                    recipe={recipe}
                    isExternal={false}
                    onDelete={handleDeleteRecipe}
                    onToggleFavorite={handleToggleFavorite}
                  />
                ))}
              </div>
            </section>
          )}
        </main>
      </div>
    </div>
  );
};

export default HomePage; 