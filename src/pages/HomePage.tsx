import React, { useState, useEffect, useMemo } from 'react';
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
import { useAuth } from '../context/AuthContext';

const HomePage: React.FC = () => {
  const { isAuthenticated, user } = useAuth();

  // Load user preferences separately (since AuthContext User doesn't include preferences)
  const [userPreferences, setUserPreferences] = useState<any>(null);

  // Load user preferences when authenticated
  useEffect(() => {
    console.log('🔍 HomePage useEffect - isAuthenticated:', isAuthenticated);
    
    if (!isAuthenticated) {
      setUserPreferences(null);
      return;
    }

    const loadPreferences = async () => {
      try {
        const token = localStorage.getItem('auth_token');
        console.log('🔑 Loading preferences with token:', token ? 'present' : 'missing');
        
        const response = await fetch('http://localhost:5003/api/preferences', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        console.log('📋 Preferences response status:', response.status);

        if (response.ok) {
          const data = await response.json();
          console.log('✅ Loaded preferences:', data.preferences);
          setUserPreferences(data.preferences);
        } else if (response.status === 404) {
          // No preferences set yet
          console.log('📭 No preferences found (404)');
          setUserPreferences(null);
        } else {
          const errorText = await response.text();
          console.error('❌ Failed to load preferences:', response.status, errorText);
          setUserPreferences(null);
        }
      } catch (error) {
        console.error('💥 Error loading user preferences:', error);
        setUserPreferences(null);
      }
    };

    loadPreferences();
  }, [isAuthenticated]);

  // Load recipes using React Query for better caching - use direct backend endpoint for all recipes
  const { data: backendRecipes = [], isLoading: isLoadingBackend, error: backendError } = useQuery({
    queryKey: ['backend-recipes'],
    queryFn: async () => {
      try {
        const response = await fetch('http://localhost:5003/recipes');
        if (!response.ok) throw new Error('Failed to fetch recipes');
        const data = await response.json();
        return data.results || [];
      } catch (error) {
        console.error('Error fetching backend recipes:', error);
        return [];
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1, // Only retry once on failure
  });

  const { data: manualRecipes = [], isLoading: isLoadingManual, error: manualRecipesError } = useQuery({
    queryKey: ['manual-recipes'],
    queryFn: fetchManualRecipes,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1, // Only retry once on failure
    enabled: false, // Disable this for now to avoid duplication since it calls same endpoint
  });

  // Log any query errors
  useEffect(() => {
    if (backendError) {
      console.warn('Failed to fetch backend recipes:', backendError);
    }
    if (manualRecipesError) {
      console.warn('Failed to fetch manual recipes:', manualRecipesError);
    }
  }, [backendError, manualRecipesError]);

  // Extract the results array from the API response
  const spoonacularRecipes = useMemo(() => {
    if (!backendRecipes) return [];
    if (Array.isArray(backendRecipes)) return backendRecipes;
    if (backendRecipes.results && Array.isArray(backendRecipes.results)) {
      return backendRecipes.results;
    }
    console.warn('Unexpected backend data format:', backendRecipes);
    return [];
  }, [backendRecipes]);

  // Load saved recipes
  const [savedRecipes, setSavedRecipes] = useState<Recipe[]>([]);
  useEffect(() => {
    const loadSavedRecipes = async () => {
      const recipes = await loadRecipes();
      setSavedRecipes(recipes);
    };
    loadSavedRecipes();
  }, []);

  // Combine and organize recipes into different categories
  const organizedRecipes = useMemo(() => {
    // Mark recipes from the main backend endpoint as external type so they route to /external-recipe/ID
    const allCombined = [
      ...spoonacularRecipes.map(recipe => ({ ...recipe, type: 'external' as const })),
      ...manualRecipes.map(recipe => ({ ...recipe, type: 'manual' as const })),
      ...savedRecipes.map(recipe => ({ ...recipe, type: 'saved' as const }))
    ];

    // If user is authenticated and has preferences, filter recommendations accordingly
    let recommendedRecipes = [];
    let popularRecipes = [];
    let newestRecipes = [];
    
    console.log('🍽️ Recipe organization - isAuthenticated:', isAuthenticated, 'userPreferences:', userPreferences);
    console.log('📊 Recipe counts - Backend:', spoonacularRecipes.length, 'Manual:', manualRecipes.length, 'Saved:', savedRecipes.length);
    console.log('🔍 Total recipes to filter:', allCombined.length);
    
    if (isAuthenticated && userPreferences) {
      const { 
        favoriteCuisines = [], 
        dietaryRestrictions = [],
        favoriteFoods = [] 
      } = userPreferences;
      
      console.log('🎯 Applying user preferences:', { 
        favoriteCuisines, 
        dietaryRestrictions, 
        favoriteFoods 
      });
      
      // Filter and score recipes based on user preferences
      recommendedRecipes = allCombined.map(recipe => {
        const recipeCuisines = recipe.cuisines || [];
        const recipeTitle = (recipe.title || recipe.name || '').toLowerCase();
        const recipeIngredients = (recipe.ingredients || []).map(i => i.name?.toLowerCase() || '');
        
        // 1. Check dietary restrictions (MUST PASS)
        let matchesDiet = dietaryRestrictions.length === 0; // If no restrictions, allow all
        if (dietaryRestrictions.length > 0) {
          const recipeDiets = recipe.diets || [];
          matchesDiet = dietaryRestrictions.every(prefDiet => {
            const prefLower = prefDiet.toLowerCase();
            return recipeDiets.some(diet => {
              const dietLower = diet?.toLowerCase() || '';
              // EXACT matching for dietary restrictions
              if (prefLower === 'vegetarian' && dietLower === 'vegetarian') return true;
              if (prefLower === 'vegan' && dietLower === 'vegan') return true;
              if (prefLower === 'gluten-free' && (dietLower === 'gluten-free' || dietLower === 'gluten free')) return true;
              if (prefLower === 'dairy-free' && (dietLower === 'dairy-free' || dietLower === 'dairy free')) return true;
              if (prefLower === 'keto' && (dietLower === 'ketogenic' || dietLower === 'keto')) return true;
              if (prefLower === 'paleo' && (dietLower === 'paleo' || dietLower === 'paleolithic')) return true;
              return false;
            });
          });
        }
        
        // Skip if it doesn't match dietary restrictions
        if (!matchesDiet && dietaryRestrictions.length > 0) {
          return { ...recipe, _matchScore: -1 };
        }
        
        // 2. Calculate match score based on favorite foods (HIGH PRIORITY)
        let foodMatchScore = 0;
        if (favoriteFoods && favoriteFoods.length > 0) {
          foodMatchScore = favoriteFoods.reduce((score, food) => {
            const foodLower = food.toLowerCase();
            // Check if food is in title or ingredients
            if (recipeTitle.includes(foodLower)) return score + 10; // High score for title match
            if (recipeIngredients.some(ing => ing.includes(foodLower))) return score + 5; // Medium score for ingredient match
            return score;
          }, 0);
        }
        
        // 3. Calculate match score based on cuisine (MEDIUM PRIORITY)
        let cuisineMatchScore = 0;
        if (favoriteCuisines && favoriteCuisines.length > 0) {
          cuisineMatchScore = favoriteCuisines.reduce((score, cuisine) => {
            const cuisineLower = cuisine.toLowerCase();
            // Check for exact cuisine match
            if (recipeCuisines.some(c => c?.toLowerCase() === cuisineLower)) {
              return score + 5; // High score for exact match
            }
            // Check for partial match in title
            if (recipeTitle.includes(cuisineLower) && cuisineLower.length > 4) {
              return score + 2; // Lower score for title match
            }
            return score;
          }, 0);
        }
        
        // 4. Bonus for recipes with images and good metadata
        const qualityBonus = (recipe.image && recipe.image !== '/placeholder.svg' ? 1 : 0) +
                           (recipe.readyInMinutes ? 1 : 0) +
                           (recipeTitle.length > 10 ? 1 : 0);
        
        // Calculate total score with weights
        const totalScore = 
          (foodMatchScore * 3) +      // Highest weight to favorite foods
          (cuisineMatchScore * 2) +   // Medium weight to cuisines
          (qualityBonus * 0.5);       // Small bonus for quality
        
        console.log(`🔍 Recipe "${recipeTitle}" scores:`, {
          foodMatchScore,
          cuisineMatchScore,
          qualityBonus,
          totalScore
        });
        
        return { ...recipe, _matchScore: totalScore };
      })
      // Filter out recipes that don't match dietary restrictions
      .filter(recipe => recipe._matchScore >= 0)
      // Sort by total score (descending)
      .sort((a, b) => b._matchScore - a._matchScore)
      // Remove the temporary score property
      .map(({ _matchScore, ...rest }) => rest);
      
      console.log(`🎉 Found ${recommendedRecipes.length} STRICT preference-matched recipes:`, 
        recommendedRecipes.map(r => r.title || r.name));
      
      // The recipes are already sorted by the scoring system above
      // which prioritizes dietary restrictions, then favorite foods, then cuisine
      
      // If we have very few matches, add some broader matches
      if (recommendedRecipes.length < 2) {
        console.log('🔄 Adding broader matches due to limited strict matches');
        const broaderMatches = allCombined
          .filter(recipe => !recommendedRecipes.some(r => r.id === recipe.id)) // Skip already selected
          .filter(recipe => {
            // Only include recipes that match dietary restrictions
            if (dietaryRestrictions.length > 0) {
              const recipeDiets = recipe.diets || [];
              return dietaryRestrictions.every(prefDiet => {
                const prefLower = prefDiet.toLowerCase();
                return recipeDiets.some(diet => {
                  const dietLower = diet?.toLowerCase() || '';
                  if (prefLower === 'vegetarian' && dietLower === 'vegetarian') return true;
                  if (prefLower === 'vegan' && dietLower === 'vegan') return true;
                  if (prefLower === 'gluten-free' && (dietLower === 'gluten-free' || dietLower === 'gluten free')) return true;
                  if (prefLower === 'dairy-free' && (dietLower === 'dairy-free' || dietLower === 'dairy free')) return true;
                  if (prefLower === 'keto' && (dietLower === 'ketogenic' || dietLower === 'keto')) return true;
                  if (prefLower === 'paleo' && (dietLower === 'paleo' || dietLower === 'paleolithic')) return true;
                  return false;
                });
              });
            }
            return true;
          })
          .slice(0, 2); // Add max 2 broader matches
        
        recommendedRecipes = [...recommendedRecipes, ...broaderMatches];
        console.log(`Added ${broaderMatches.length} broader matches`);
      }
      
      // Get remaining recipes for popular/newest sections
      const remainingRecipes = allCombined.filter(recipe => 
        !recommendedRecipes.find(r => (r.id || r._id) === (recipe.id || recipe._id) && r.type === recipe.type)
      );
      
      // Popular recipes = shuffle remaining recipes
      popularRecipes = [...remainingRecipes].sort(() => Math.random() - 0.5);
      
      // Newest recipes = reverse order of remaining
      newestRecipes = [...remainingRecipes].reverse();
      
    } else {
      // For non-authenticated users or users without preferences, show curated selection
      console.log('🔄 No preferences found, showing default recipes');
      const shuffled = [...allCombined].sort(() => Math.random() - 0.5);
      recommendedRecipes = shuffled.slice(0, 4);
      popularRecipes = shuffled.slice(4, 8);
      newestRecipes = shuffled.slice(8, 12);
    }

    return {
      recommended: recommendedRecipes.slice(0, 4),
      popular: popularRecipes.slice(0, 4),
      newest: newestRecipes.slice(0, 4)
    };
  }, [spoonacularRecipes, manualRecipes, savedRecipes, isAuthenticated, userPreferences]);

  const isLoading = isLoadingBackend || isLoadingManual;

  // Welcome message based on authentication status
  const getWelcomeMessage = () => {
    if (isAuthenticated && user) {
      return {
        title: `Welcome back, ${user.full_name || user.email.split('@')[0]}!`,
        subtitle: "Ready to discover new delicious recipes?"
      };
    }
    return {
      title: "Discover Delicious Recipes",
      subtitle: "Your personalized recipe collection awaits"
    };
  };

  const welcomeMessage = getWelcomeMessage();

  // Placeholder handlers for recipe interactions
  const handleDeleteRecipe = () => {
    // Placeholder for delete functionality
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
                {welcomeMessage.title}
              </h1>
              <p className="text-xl text-white/90 mb-8 max-w-3xl mx-auto">
                {welcomeMessage.subtitle}
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link to="/recipes">
                  <Button size="lg" variant="secondary" className="w-full sm:w-auto">
                    <Search className="mr-2 h-4 w-4" />
                    Browse All Recipes
                  </Button>
                </Link>
                {isAuthenticated ? (
                  <Link to="/meal-planner">
                    <Button size="lg" variant="outline" className="w-full sm:w-auto bg-white/10 text-white hover:bg-white/20">
                      <ChefHat className="mr-2 h-4 w-4" />
                      AI Meal Planner
                    </Button>
                  </Link>
                ) : (
                  <Link to="/signup">
                    <Button size="lg" variant="outline" className="w-full sm:w-auto bg-white/10 text-white hover:bg-white/20">
                      <ChefHat className="mr-2 h-4 w-4" />
                      Sign Up for AI Features
                    </Button>
                  </Link>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* Features Section - Authentication Aware */}
        <section className="py-16 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                {isAuthenticated ? "Your Recipe Features" : "Unlock Premium Features"}
              </h2>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                {isAuthenticated 
                  ? "Access all your personalized recipe features and AI-powered tools"
                  : "Sign up to access AI meal planning, personalized recommendations, and more"
                }
              </p>
            </div>
            
            <div className="grid md:grid-cols-3 gap-8">
              <div className="text-center p-6 rounded-lg border">
                <div className="bg-recipe-primary/10 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Search className="h-8 w-8 text-recipe-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Recipe Discovery</h3>
                <p className="text-gray-600 mb-4">
                  Browse thousands of recipes from our curated collection
                </p>
                <p className="text-sm text-green-600 font-medium">✅ Free for everyone</p>
              </div>

              <div className={`text-center p-6 rounded-lg border ${!isAuthenticated ? 'opacity-60' : ''}`}>
                <div className="bg-recipe-primary/10 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <ChefHat className="h-8 w-8 text-recipe-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-2">AI Meal Planning</h3>
                <p className="text-gray-600 mb-4">
                  Get personalized weekly meal plans based on your preferences
                </p>
                {isAuthenticated ? (
                  <Link to="/meal-planner">
                    <Button size="sm">Start Planning</Button>
                  </Link>
                ) : (
                  <p className="text-sm text-orange-600 font-medium">Requires sign up</p>
                )}
              </div>

              <div className={`text-center p-6 rounded-lg border ${!isAuthenticated ? 'opacity-60' : ''}`}>
                <div className="bg-recipe-primary/10 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <TrendingUp className="h-8 w-8 text-recipe-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Smart Preferences</h3>
                <p className="text-gray-600 mb-4">
                  Set dietary restrictions and get tailored recommendations
                </p>
                {isAuthenticated ? (
                  <Link to="/preferences">
                    <Button size="sm">Set Preferences</Button>
                  </Link>
                ) : (
                  <p className="text-sm text-orange-600 font-medium">Requires sign up</p>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* Recipe Sections */}
        <section className="py-16 bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            
            {/* Recommended Recipes - Only for authenticated users */}
            {isAuthenticated && (
              <div className="mb-16">
                <div className="flex justify-between items-center mb-8">
                  <div>
                    <h2 className="text-3xl font-bold text-gray-900 mb-2">Recommended for You</h2>
                    <p className="text-gray-600">Personalized recipe suggestions based on your preferences</p>
                  </div>
                  <Link to="/preferences">
                    <Button variant="outline">
                      <TrendingUp className="mr-2 h-4 w-4" />
                      Update Preferences
                    </Button>
                  </Link>
                </div>

                {isLoading ? (
                  <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {[...Array(4)].map((_, i) => (
                      <div key={i} className="bg-white rounded-lg shadow-md p-4 animate-pulse">
                        <div className="bg-gray-300 h-48 rounded-lg mb-4"></div>
                        <div className="bg-gray-300 h-4 rounded mb-2"></div>
                        <div className="bg-gray-300 h-3 rounded w-2/3"></div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {organizedRecipes.recommended.map((recipe, index) => {
                      if (recipe.type === 'manual') {
                        return <ManualRecipeCard key={`recommended-${recipe.id}-${index}`} recipe={recipe} />;
                      }
                      return (
                        <RecipeCard 
                          key={`recommended-${recipe.id}-${index}`} 
                          recipe={recipe} 
                          onDelete={handleDeleteRecipe}
                        />
                      );
                    })}
                  </div>
                )}

                {!isLoading && organizedRecipes.recommended.length === 0 && (
                  <div className="text-center py-8 bg-white rounded-lg">
                    <p className="text-gray-500">No recommendations yet. Set your preferences to get personalized suggestions!</p>
                    <Link to="/preferences">
                      <Button className="mt-4">Set Preferences</Button>
                    </Link>
                  </div>
                )}
              </div>
            )}

            {/* Popular Recipes */}
            <div className="mb-16">
              <div className="flex justify-between items-center mb-8">
                <div>
                  <h2 className="text-3xl font-bold text-gray-900 mb-2">Popular Recipes</h2>
                  <p className="text-gray-600">Most loved recipes by our community</p>
                </div>
                <Link to="/recipes">
                  <Button variant="outline">
                    <ThumbsUp className="mr-2 h-4 w-4" />
                    View All Popular
                  </Button>
                </Link>
              </div>

              {isLoading ? (
                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="bg-white rounded-lg shadow-md p-4 animate-pulse">
                      <div className="bg-gray-300 h-48 rounded-lg mb-4"></div>
                      <div className="bg-gray-300 h-4 rounded mb-2"></div>
                      <div className="bg-gray-300 h-3 rounded w-2/3"></div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {organizedRecipes.popular.map((recipe, index) => {
                    if (recipe.type === 'manual') {
                      return <ManualRecipeCard key={`popular-${recipe.id}-${index}`} recipe={recipe} />;
                    }
                    return (
                      <RecipeCard 
                        key={`popular-${recipe.id}-${index}`} 
                        recipe={recipe} 
                        onDelete={handleDeleteRecipe}
                      />
                    );
                  })}
                </div>
              )}

              {!isLoading && organizedRecipes.popular.length === 0 && (
                <div className="text-center py-8 bg-white rounded-lg">
                  <p className="text-gray-500">No popular recipes available at the moment.</p>
                </div>
              )}
            </div>

            {/* Newly Added Recipes */}
            <div>
              <div className="flex justify-between items-center mb-8">
                <div>
                  <h2 className="text-3xl font-bold text-gray-900 mb-2">Newly Added</h2>
                  <p className="text-gray-600">Fresh recipes just added to our collection</p>
                </div>
                <Link to="/recipes">
                  <Button variant="outline">
                    <Clock className="mr-2 h-4 w-4" />
                    View All Recent
                  </Button>
                </Link>
              </div>

              {isLoading ? (
                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="bg-white rounded-lg shadow-md p-4 animate-pulse">
                      <div className="bg-gray-300 h-48 rounded-lg mb-4"></div>
                      <div className="bg-gray-300 h-4 rounded mb-2"></div>
                      <div className="bg-gray-300 h-3 rounded w-2/3"></div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                  {organizedRecipes.newest.map((recipe, index) => {
                    if (recipe.type === 'manual') {
                      return <ManualRecipeCard key={`newest-${recipe.id}-${index}`} recipe={recipe} />;
                    }
                    return (
                      <RecipeCard 
                        key={`newest-${recipe.id}-${index}`} 
                        recipe={recipe} 
                        onDelete={handleDeleteRecipe}
                      />
                    );
                  })}
                </div>
              )}

              {!isLoading && organizedRecipes.newest.length === 0 && (
                <div className="text-center py-8 bg-white rounded-lg">
                  <p className="text-gray-500">No new recipes available at the moment.</p>
                </div>
              )}
            </div>

          </div>
        </section>

        {/* Call to Action for Non-Authenticated Users */}
        {!isAuthenticated && (
          <section className="py-16 bg-recipe-primary">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
              <h2 className="text-3xl font-bold text-white mb-4">
                Ready to Unlock AI-Powered Cooking?
              </h2>
              <p className="text-xl text-white/90 mb-8">
                Join thousands of home cooks using AI to plan their meals and discover new recipes
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link to="/signup">
                  <Button size="lg" variant="secondary" className="w-full sm:w-auto">
                    Sign Up Free
                  </Button>
                </Link>
                <Link to="/signin">
                  <Button size="lg" variant="outline" className="w-full sm:w-auto bg-white/10 text-white hover:bg-white/20">
                    Sign In
                  </Button>
                </Link>
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  );
};

export default HomePage;
