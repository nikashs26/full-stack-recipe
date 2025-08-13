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
import { getHomepagePopularRecipes } from '../services/popularRecipesService';
import { addSampleClicks } from '../utils/testClickTracking';
import { apiCall } from '../utils/apiUtils';

const HomePage: React.FC = () => {
  const { isAuthenticated, user } = useAuth();

  // Load user preferences separately (since AuthContext User doesn't include preferences)
  const [userPreferences, setUserPreferences] = useState<any>(null);
  
  // State for popular recipes toggle
  const [showPersonalPopular, setShowPersonalPopular] = useState(false);

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
        const response = await fetch('http://localhost:5003/get_recipes');
        if (!response.ok) {
          const errorData = await response.text();
          console.error('Backend error response:', errorData);
          throw new Error('Failed to fetch recipes');
        }
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

  // Query for backend recommendations when user has preferences
  const { data: backendRecommendations = [], isLoading: isLoadingRecommendations } = useQuery({
    queryKey: ['backend-recommendations', userPreferences],
    queryFn: async () => {
      if (!userPreferences) {
        console.log('❌ No user preferences available for backend recommendations');
        return [];
      }
      
      console.log('🔍 Fetching backend recommendations with preferences:', userPreferences);
      
      try {
        const token = localStorage.getItem('auth_token');
        if (!token) {
          console.error('❌ No auth token available for backend recommendations');
          return [];
        }
        
        const response = await fetch('http://localhost:5003/recommendations?limit=8', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        console.log('📡 Backend response status:', response.status);
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error('❌ Failed to fetch backend recommendations:', response.status, errorText);
          return [];
        }
        
        const data = await response.json();
        console.log('✅ Backend recommendations response:', data);
        return data.recommendations || [];
      } catch (error) {
        console.error('❌ Error fetching backend recommendations:', error);
        return [];
      }
    },
    enabled: !!userPreferences && isAuthenticated,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });

  const { data: manualRecipes = [], isLoading: isLoadingManual, error: manualRecipesError } = useQuery({
    queryKey: ['manual-recipes'],
    queryFn: () => fetchManualRecipes(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1, // Only retry once on failure
    enabled: false, // Disable this for now to avoid duplication since it calls same endpoint
  });

  // Query for popular recipes based on clicks and reviews
  const { data: popularRecipesData = [], isLoading: isLoadingPopular } = useQuery({
    queryKey: ['popular-recipes', user?.id],
    queryFn: () => getHomepagePopularRecipes(user?.id),
    staleTime: 10 * 60 * 1000, // 10 minutes (popular recipes don't change as frequently)
    retry: 1,
  });

  // Query for personal popular recipes
  const { data: personalPopularRecipesData = [], isLoading: isLoadingPersonalPopular } = useQuery({
    queryKey: ['personal-popular-recipes', user?.id],
    queryFn: () => getHomepagePopularRecipes(user?.id),
    staleTime: 10 * 60 * 1000,
    retry: 1,
    enabled: !!user?.id && showPersonalPopular, // Only fetch when user is logged in and toggle is on
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

    let recommendedRecipes = [];
    let popularRecipes = [];
    let newestRecipes = [];
    
    console.log('🍽️ Recipe organization - isAuthenticated:', isAuthenticated, 'userPreferences:', userPreferences);
    console.log('📊 Recipe counts - Backend:', spoonacularRecipes.length, 'Manual:', manualRecipes.length, 'Saved:', savedRecipes.length);
    console.log('🔍 Total recipes to filter:', allCombined.length);
    
    // Check if user has meaningful preferences (not just empty arrays/strings)
    const hasMeaningfulPreferences = React.useMemo(() => {
      if (!userPreferences) return false;
      
      // Check if any preference arrays have actual content
      const hasFavoriteFoods = Array.isArray(userPreferences.favoriteFoods) && 
        userPreferences.favoriteFoods.some(food => food && food.trim() !== '');
      
      const hasFavoriteCuisines = Array.isArray(userPreferences.favoriteCuisines) && 
        userPreferences.favoriteCuisines.some(cuisine => cuisine && cuisine.trim() !== '');
      
      const hasDietaryRestrictions = Array.isArray(userPreferences.dietaryRestrictions) && 
        userPreferences.dietaryRestrictions.length > 0;
      
      const hasFoodsToAvoid = Array.isArray(userPreferences.foodsToAvoid) && 
        userPreferences.foodsToAvoid.some(food => food && food.trim() !== '');
      
      const hasCookingSkill = userPreferences.cookingSkillLevel && userPreferences.cookingSkillLevel !== 'beginner';
      
      const hasHealthGoals = Array.isArray(userPreferences.healthGoals) && 
        userPreferences.healthGoals.length > 0;
      
      // Return true if any meaningful preference is set
      return hasFavoriteFoods || hasFavoriteCuisines || hasDietaryRestrictions || 
             hasFoodsToAvoid || hasCookingSkill || hasHealthGoals;
    }, [userPreferences]);

    // For authenticated users with preferences, use backend recommendations
    if (isAuthenticated && userPreferences && hasMeaningfulPreferences) {
      console.log('✅ User has meaningful preferences, using backend recommendations');
      console.log('🔍 Backend recommendations state:', {
        data: backendRecommendations,
        length: backendRecommendations?.length,
        isLoading: isLoadingRecommendations,
        userPreferences: userPreferences
      });
      
      // Use backend recommendations if available, otherwise fall back to frontend filtering
      if (backendRecommendations && backendRecommendations.length > 0) {
        console.log('🎯 Using backend recommendations:', backendRecommendations.length);
        console.log('📊 Backend recommendations cuisines:', backendRecommendations.map(r => r.cuisine));
        
        // Ensure even distribution across cuisines from backend recommendations
        // but prioritize favorite-food matches first
        const favoriteFoodsNorm: string[] = (userPreferences?.favoriteFoods || [])
          .map((f: any) => (f || '').toString().trim().toLowerCase())
          .filter(Boolean);

        type AnyRec = any;
        const cuisineGroupsFav: Record<string, AnyRec[]> = {};
        const cuisineGroupsOther: Record<string, AnyRec[]> = {};
        backendRecommendations.forEach((recipe: any) => {
          const cuisine = recipe.cuisine || 'Unknown';
          if (!cuisineGroupsFav[cuisine]) cuisineGroupsFav[cuisine] = [];
          if (!cuisineGroupsOther[cuisine]) cuisineGroupsOther[cuisine] = [];
          const titleLower = ((recipe.title || recipe.name || '') as string).toLowerCase();
          const ingredientsLower = Array.isArray(recipe.ingredients) ? recipe.ingredients.map((i: any) => String(i).toLowerCase()) : [];
          const hasFavFood = favoriteFoodsNorm.length > 0 && favoriteFoodsNorm.some(f => titleLower.includes(f) || ingredientsLower.some(i => i.includes(f)));
          if (hasFavFood) {
            cuisineGroupsFav[cuisine].push(recipe);
          } else {
            cuisineGroupsOther[cuisine].push(recipe);
          }
        });
        const cuisineGroups: Record<string, AnyRec[]> = {};
        Object.keys({...cuisineGroupsFav, ...cuisineGroupsOther}).forEach(c => {
          cuisineGroups[c] = [
            ...(cuisineGroupsFav[c] || []),
            ...(cuisineGroupsOther[c] || [])
          ];
        });
        
        console.log('📊 Cuisine groups from backend:', Object.keys(cuisineGroups).map(c => `${c}: ${cuisineGroups[c].length}`));
        
        // Distribute recipes evenly across cuisines
        const distributedRecipes = [];
        const maxRecipesPerCuisine = Math.ceil(8 / Object.keys(cuisineGroups).length);
        
        // Take recipes from each cuisine in rotation
        for (let i = 0; i < maxRecipesPerCuisine; i++) {
          for (const cuisine in cuisineGroups) {
            if (cuisineGroups[cuisine][i] && distributedRecipes.length < 8) {
              distributedRecipes.push(cuisineGroups[cuisine][i]);
            }
          }
        }
        
        console.log('🎯 Final distributed recommendations:', distributedRecipes.length);
        console.log('📊 Final cuisine distribution:', distributedRecipes.map(r => r.cuisine));
        
        recommendedRecipes = distributedRecipes.map(recipe => ({ ...recipe, type: 'external' as const }));
      } else if (isLoadingRecommendations) {
        console.log('⏳ Backend recommendations still loading...');
        // Don't set recommendedRecipes yet, wait for loading to complete
      } else {
        console.log('🔄 Backend recommendations not available, using fallback filtering');
        console.log('❌ Backend recommendations failed or empty, falling back to frontend filtering');
        
        // Fallback to frontend filtering (simplified version)
        const { 
          favoriteCuisines = [], 
          dietaryRestrictions = [],
          favoriteFoods = [] 
        } = userPreferences;
        
        console.log('🔄 Frontend filtering with cuisines:', favoriteCuisines);
        
        // Simple filtering based on cuisines and dietary restrictions
        let filteredRecipes = allCombined;
        
        if (dietaryRestrictions && dietaryRestrictions.length > 0) {
          filteredRecipes = allCombined.filter(recipe => {
            const recipeDiets = recipe.diets || [];
            return dietaryRestrictions.every(prefDiet => {
              if (!prefDiet) return true;
              const prefLower = prefDiet.toLowerCase().trim();
              return recipeDiets.some(diet => {
                if (!diet) return false;
                const dietLower = diet.toLowerCase().trim();
                if (prefLower === 'vegetarian' && dietLower === 'vegetarian') return true;
                if (prefLower === 'vegan' && dietLower === 'vegan') return true;
                if (prefLower === 'gluten-free' && (dietLower === 'gluten-free' || dietLower === 'gluten free')) return true;
                if (prefLower === 'dairy-free' && (dietLower === 'dairy-free' || dietLower === 'dairy free')) return true;
                if (prefLower === 'keto' && (dietLower === 'ketogenic' || dietLower === 'keto')) return true;
                if (prefLower === 'paleo' && (dietLower === 'paleo' || dietLower === 'paleolithic')) return true;
                return false;
              });
            });
          });
        }
        
        // Simple cuisine filtering
        if (favoriteCuisines && favoriteCuisines.length > 0) {
          console.log('🔄 Filtering recipes for cuisines:', favoriteCuisines);
          console.log('🔄 Total recipes before filtering:', filteredRecipes.length);
          
          filteredRecipes = filteredRecipes.filter(recipe => {
            const recipeCuisines = Array.isArray(recipe.cuisines) ? recipe.cuisines : [];
            const recipeTitle = (recipe.title || recipe.name || '').toLowerCase();
            
            const matches = favoriteCuisines.some(cuisine => {
              if (!cuisine) return false;
              const cuisineLower = cuisine.toLowerCase();
              const cuisineMatch = recipeCuisines.some(c => c?.toLowerCase().includes(cuisineLower)) ||
                     recipeTitle.includes(cuisineLower);
              
              if (cuisineMatch) {
                console.log(`✅ Recipe "${recipe.title || recipe.name}" matches cuisine "${cuisine}"`);
              }
              
              return cuisineMatch;
            });
            
            return matches;
          });
          
          console.log('🔄 Recipes after cuisine filtering:', filteredRecipes.length);
          console.log('🔄 Cuisines found in filtered recipes:', [...new Set(filteredRecipes.map(r => r.cuisines).flat().filter(Boolean))]);
        }
        
        // Evenly distribute filtered results across selected cuisines (round-robin)
        if (favoriteCuisines && favoriteCuisines.length > 1 && filteredRecipes.length > 0) {
          const normalizedSelected = favoriteCuisines.map(c => (c || '').toString().trim().toLowerCase()).filter(Boolean);
          const favoriteFoodsNorm: string[] = (favoriteFoods || []).map((f: any) => (f || '').toString().trim().toLowerCase()).filter(Boolean);

          // Structure: for each selected cuisine, keep two buckets: favorite-food matches and others
          const groupsFav: Record<string, any[]> = {};
          const groupsOther: Record<string, any[]> = {};
          for (const c of normalizedSelected) {
            groupsFav[c] = [];
            groupsOther[c] = [];
          }
          
          // Assign each recipe to the first matching selected cuisine, then bucket by favorite-food match
          for (const recipe of filteredRecipes) {
            const rc = (Array.isArray(recipe.cuisines) ? recipe.cuisines : [])
              .map((c: any) => (c || '').toString().trim().toLowerCase());
            const single = (recipe as any).cuisine ? [(recipe as any).cuisine.toString().toLowerCase()] : [];
            const recipeCuisines = [...rc, ...single];
            const matchCuisine = normalizedSelected.find(sel => recipeCuisines.some(rc2 => rc2.includes(sel)));
            if (!matchCuisine) continue;

            // Determine if recipe matches any favorite food (title or name)
            const titleLower = ((recipe.title || recipe.name || '') as string).toLowerCase();
            const ingredientsLower = Array.isArray((recipe as any).ingredients) ? ((recipe as any).ingredients as any[]).map(i => String(i).toLowerCase()) : [];
            const hasFavFood = favoriteFoodsNorm.length > 0 && favoriteFoodsNorm.some(f => titleLower.includes(f) || ingredientsLower.some(i => i.includes(f)));

            if (hasFavFood) {
              groupsFav[matchCuisine].push(recipe);
            } else {
              groupsOther[matchCuisine].push(recipe);
            }
          }

          // Merge buckets with favorite-food matches first per cuisine
          const groups: Record<string, any[]> = {};
          for (const sel of normalizedSelected) {
            groups[sel] = [...groupsFav[sel], ...groupsOther[sel]];
          }
          
          // Round-robin pick up to 8
          const rr: any[] = [];
          let added = true;
          while (rr.length < 8 && added) {
            added = false;
            for (const sel of normalizedSelected) {
              const arr = groups[sel] || [];
              if (arr.length > 0 && rr.length < 8) {
                rr.push(arr.shift());
                added = true;
              }
            }
          }
          
          if (rr.length > 0) {
            recommendedRecipes = rr;
          } else {
            recommendedRecipes = filteredRecipes.slice(0, 8);
          }
        } else {
          // Single cuisine or no cuisine: prioritize favorite foods first, then fill
          const favoriteFoodsNorm: string[] = (favoriteFoods || []).map((f: any) => (f || '').toString().trim().toLowerCase()).filter(Boolean);
          if (favoriteFoodsNorm.length > 0) {
            const titleMatches = filteredRecipes.filter(r => {
              const t = ((r.title || r.name || '') as string).toLowerCase();
              const ings = Array.isArray((r as any).ingredients) ? ((r as any).ingredients as any[]).map(i => String(i).toLowerCase()) : [];
              return favoriteFoodsNorm.some(f => t.includes(f) || ings.some(i => i.includes(f)));
            });
            const others = filteredRecipes.filter(r => !titleMatches.includes(r));
            recommendedRecipes = [...titleMatches, ...others].slice(0, 8);
          } else {
            recommendedRecipes = filteredRecipes.slice(0, 8);
          }
        }
        console.log('🔄 Final frontend recommendations:', recommendedRecipes.length);
      }
    } else {
      console.log('ℹ️ No user preferences, using default recipe organization');
    }

    // Get remaining recipes for popular/newest sections
    const remainingRecipes = allCombined.filter(recipe => 
      !recommendedRecipes.find(r => (r.id || r._id) === (recipe.id || recipe._id) && r.type === recipe.type)
    );
    
    // Use real popular recipes data if available, otherwise fall back to random selection
    if (showPersonalPopular && isAuthenticated && user?.id) {
      // Use personal popular recipes
      if (personalPopularRecipesData && personalPopularRecipesData.length > 0) {
        console.log('👤 Using personal popular recipes data:', personalPopularRecipesData.length);
        popularRecipes = personalPopularRecipesData.map(recipe => ({ ...recipe, type: 'external' as const }));
      } else {
        console.log('🔄 No personal popular recipes data, using random selection');
        popularRecipes = [...remainingRecipes].sort(() => Math.random() - 0.5);
      }
    } else if (popularRecipesData && popularRecipesData.length > 0) {
      console.log('🎯 Using global popular recipes data:', popularRecipesData.length);
      popularRecipes = popularRecipesData.map(recipe => ({ ...recipe, type: 'external' as const }));
    } else {
      console.log('🔄 No popular recipes data, using random selection');
      popularRecipes = [...remainingRecipes].sort(() => Math.random() - 0.5);
    }
    
    // Newest recipes = reverse order of remaining
    newestRecipes = [...remainingRecipes].reverse();
    
    return {
      recommended: recommendedRecipes.slice(0, 8), // Show 8 recommended recipes
      popular: popularRecipes.slice(0, 4),
      newest: newestRecipes.slice(0, 4)
    };
  }, [spoonacularRecipes, manualRecipes, savedRecipes, popularRecipesData, isAuthenticated, userPreferences, showPersonalPopular, personalPopularRecipesData, backendRecommendations]);

  const isLoading = isLoadingBackend || isLoadingManual || isLoadingPopular || (showPersonalPopular && isLoadingPersonalPopular) || isLoadingRecommendations;

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
                  <h2 className="text-3xl font-bold text-gray-900 mb-2">
                    {showPersonalPopular ? 'Your Popular Recipes' : 'Popular Recipes'}
                  </h2>
                  <p className="text-gray-600">
                    {showPersonalPopular 
                      ? 'Recipes you\'ve clicked and reviewed the most' 
                      : 'Most loved recipes by our community'
                    }
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  {isAuthenticated && (
                    <Button
                      variant={showPersonalPopular ? "default" : "outline"}
                      size="sm"
                      onClick={() => setShowPersonalPopular(!showPersonalPopular)}
                    >
                      {showPersonalPopular ? 'Show Global' : 'Show Personal'}
                    </Button>
                  )}
                  <Link to="/recipes">
                    <Button variant="outline">
                      <ThumbsUp className="mr-2 h-4 w-4" />
                      View All Popular
                    </Button>
                  </Link>
                </div>
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
