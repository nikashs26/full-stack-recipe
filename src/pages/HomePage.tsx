import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Search, ChefHat, ThumbsUp, Award, TrendingUp, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Header from '../components/Header';
import RecipeCard from '../components/RecipeCard';
import ManualRecipeCard from '../components/ManualRecipeCard';
import { Recipe } from '../types/recipe';
import { SpoonacularRecipe } from '../types/spoonacular';
import { loadRecipes } from '../utils/storage';
import { fetchManualRecipes } from '../lib/manualRecipes';
import { fetchRecipes } from '../lib/spoonacular';

const HomePage: React.FC = () => {
  // Remove authentication dependency - work without auth
  const [userPreferences, setUserPreferences] = useState<any>(null);

  // Load user preferences on mount
  useEffect(() => {
    const loadPreferences = async () => {
      try {
        const response = await fetch('/api/temp-preferences');
        if (response.ok) {
          const data = await response.json();
          if (data.preferences) {
            setUserPreferences(data.preferences);
          }
        }
      } catch (error) {
        console.error('Error loading preferences:', error);
      }
    };

    loadPreferences();
  }, []);

  // Query for local recipes
  const { data: localRecipes = [], isLoading: isLocalLoading } = useQuery({
    queryKey: ['localRecipes'],
    queryFn: loadRecipes,
    staleTime: 60000
  });

  // Query for manual recipes with better error handling
  const { data: manualRecipes = [], isLoading: isManualLoading, error: manualError } = useQuery({
    queryKey: ['manualRecipes'],
    queryFn: async () => {
      try {
        const recipes = await fetchManualRecipes();
        return recipes;
      } catch (error) {
        return [];
      }
    },
    staleTime: 60000,
    retry: 2
  });

  // Query for recommended recipes based on user preferences
  const { data: recommendedRecipes = [], isLoading: isRecommendedLoading } = useQuery({
    queryKey: ['recommendedRecipes', userPreferences],
    queryFn: async () => {
      if (!userPreferences) return [];

      const allRecommendedRecipes: SpoonacularRecipe[] = [];
      const { favoriteCuisines = [], dietaryRestrictions = [] } = userPreferences;

             // Get recommendations based on favorite cuisines
       for (const cuisine of favoriteCuisines.slice(0, 2)) {
         try {
           const results = await fetchRecipes(cuisine, '');
           if (results?.results) {
             allRecommendedRecipes.push(...results.results.slice(0, 6));
           }
         } catch (error) {
           console.error(`Error fetching ${cuisine} recipes:`, error);
         }
       }

       // Get recommendations based on dietary restrictions
       for (const diet of dietaryRestrictions.slice(0, 2)) {
         try {
           const results = await fetchRecipes(diet, '');
           if (results?.results) {
             allRecommendedRecipes.push(...results.results.slice(0, 6));
           }
         } catch (error) {
           console.error(`Error fetching ${diet} recipes:`, error);
         }
       }

      // Remove duplicates and limit results
      const uniqueRecipes = allRecommendedRecipes.filter((recipe, index, self) => 
        index === self.findIndex(r => r.id === recipe.id)
      );

      return uniqueRecipes.slice(0, 12);
    },
    staleTime: 300000,
    enabled: !!userPreferences
  });

  // Query for featured recipes
  const { data: featuredRecipes = [], isLoading: isFeaturedLoading } = useQuery({
    queryKey: ['featuredRecipes'],
         queryFn: async () => {
       try {
         const results = await fetchRecipes('healthy', '');
         return results?.results || [];
       } catch (error) {
         console.error('Error fetching featured recipes:', error);
         return [];
       }
     },
    staleTime: 300000
  });

     // Process recipes for different sections
   const processedRecipes = {
     popularRecipes: manualRecipes.slice(0, 8),
     featuredRecipes: featuredRecipes.slice(0, 8),
     topRatedRecipes: localRecipes.filter(recipe => recipe.ratings && recipe.ratings.length > 0).slice(0, 8),
     recentRecipes: localRecipes.slice(0, 8)
   };

  // Track seen recipes to avoid duplicates
  const [seenRecipes, setSeenRecipes] = useState<Set<string>>(new Set());

  useEffect(() => {
    const allRecipeIds = new Set<string>();
    
    // Add recommended recipe IDs
    recommendedRecipes.forEach(recipe => {
      allRecipeIds.add(`recommended-${recipe.id}`);
    });
    
    // Add other recipe IDs
    processedRecipes.popularRecipes.forEach(recipe => {
      allRecipeIds.add(`popular-${recipe.id}`);
    });
    
    processedRecipes.featuredRecipes.forEach(recipe => {
      allRecipeIds.add(`featured-${recipe.id}`);
    });
    
    processedRecipes.topRatedRecipes.forEach(recipe => {
      allRecipeIds.add(`top-rated-${recipe.id}`);
    });
    
    processedRecipes.recentRecipes.forEach(recipe => {
      allRecipeIds.add(`recent-${recipe.id}`);
    });
    
    setSeenRecipes(allRecipeIds);
  }, [recommendedRecipes, processedRecipes]);

  const normalizeTitle = (title: string) => {
    return title.toLowerCase().replace(/[^a-z0-9]/g, '');
  };

  const isRecipeSeen = (recipe: any, type: string) => {
    const recipeKey = `${type}-${recipe.id}`;
    const normalizedTitle = normalizeTitle(recipe.name || recipe.title || '');
    
    for (const seenKey of seenRecipes) {
      if (seenKey === recipeKey) continue;
      
      const [, seenId] = seenKey.split('-', 2);
      if (seenId === String(recipe.id)) {
        return true;
      }
    }
    
    return false;
  };

  const handleDeleteRecipe = () => {
    // Placeholder for delete functionality
  };

  const handleToggleFavorite = (recipe: Recipe) => {
    // Placeholder for favorite functionality
  };

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
                <Link to="/preferences">
                  <Button size="lg" variant="outline" className="w-full sm:w-auto bg-white/10 text-white hover:bg-white/20">
                    <ChefHat className="mr-2 h-4 w-4" />
                    Set Your Preferences
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </section>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          {/* Recommended Recipes Section - Show when preferences are set */}
          {userPreferences && (
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
              </div>
              
              {isRecommendedLoading ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                  {Array.from({ length: 8 }).map((_, i) => (
                    <div key={i} className="h-64 bg-gray-200 animate-pulse rounded-lg"></div>
                  ))}
                </div>
              ) : recommendedRecipes.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                  {recommendedRecipes.map((recipe, i) => (
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
          )}

          {/* Show message when no preferences are set */}
          {!userPreferences && (
            <section className="mb-16">
              <div className="text-center py-12 border border-dashed border-gray-300 rounded-lg">
                <ThumbsUp className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Get Personalized Recommendations</h3>
                <p className="text-gray-500 mb-4">Set your preferences to see recipes tailored just for you!</p>
                <Link to="/preferences">
                  <Button>Set Your Preferences</Button>
                </Link>
              </div>
            </section>
          )}

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
            ) : manualError ? (
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
            
            {isFeaturedLoading ? (
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
