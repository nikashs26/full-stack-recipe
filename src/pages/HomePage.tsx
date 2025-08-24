import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Search, ChefHat, ThumbsUp, Award, TrendingUp, Clock, Star, Users, Zap, Loader2, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Header from '../components/Header';
import RecipeCard from '../components/RecipeCard';
import { Recipe } from '../types/recipe';
import { SpoonacularRecipe } from '../types/spoonacular';

import { fetchManualRecipes } from '../lib/manualRecipes';
import { useAuth } from '../context/AuthContext';
import { getHomepagePopularRecipes } from '../services/popularRecipesService';
import { getQualityBasedRecipes } from '../services/popularRecipesService';
import { addSampleClicks } from '../utils/testClickTracking';
import { apiCall } from '../utils/apiUtils';
import { updateRecipe } from '../utils/storage';
import { useToast } from '@/hooks/use-toast';

const HomePage: React.FC = () => {
  const { isAuthenticated, user } = useAuth();
  const { toast } = useToast();

  // Load user preferences separately (since AuthContext User doesn't include preferences)
  const [userPreferences, setUserPreferences] = useState<any>(null);
  
  // State for popular recipes toggle
  const [showPersonalPopular, setShowPersonalPopular] = useState(false);
  
    // State for refresh feedback
  const [refreshFeedback, setRefreshFeedback] = useState<string>('');
  
  // State for refresh counter to force new data
  const [refreshCounter, setRefreshCounter] = useState<number>(0);
  
  // Get query client for invalidation
  const queryClient = useQueryClient();
  
  // Handle refresh recommendations with feedback
  const handleRefreshRecommendations = async () => {
    setRefreshFeedback('Refreshing recommendations...');
    try {
      // Increment refresh counter to force new data
      setRefreshCounter(prev => prev + 1);
      
      // Invalidate and refetch to ensure fresh data
      await queryClient.invalidateQueries({ queryKey: ['backend-recipes'] });
      await refetchBackendRecipes();
      
      console.log('🔄 Refresh triggered - new batch requested (counter:', refreshCounter + 1, ')');
      setRefreshFeedback('Recommendations refreshed with new recipes!');
      
      // Clear feedback after 3 seconds
      setTimeout(() => setRefreshFeedback(''), 3000);
    } catch (error) {
      console.error('Error refreshing recommendations:', error);
      setRefreshFeedback('Failed to refresh recommendations');
      // Clear error feedback after 3 seconds
      setTimeout(() => setRefreshFeedback(''), 3000);
    }
  };

  // Load user preferences when authenticated
  useEffect(() => {
    console.log('🔍 HomePage useEffect - isAuthenticated:', isAuthenticated);
    
    if (!isAuthenticated) {
      setUserPreferences(null);
      return;
    }

    const loadPreferences = async () => {
      try {
        console.log('🔑 Loading preferences using apiCall utility');
        
        const response = await apiCall('/api/preferences', {
          method: 'GET',
          headers: {
            'Accept': 'application/json'
          }
        });

        console.log('📋 Preferences response status:', response.status);

        if (response.ok) {
          const data = await response.json();
          console.log('✅ Loaded preferences:', data.preferences);
          console.log('🔍 Preferences breakdown:', {
            favoriteFoods: data.preferences?.favoriteFoods,
            favoriteCuisines: data.preferences?.favoriteCuisines,
            dietaryRestrictions: data.preferences?.dietaryRestrictions,
            foodsToAvoid: data.preferences?.foodsToAvoid,
            cookingSkillLevel: data.preferences?.cookingSkillLevel,
            healthGoals: data.preferences?.healthGoals
          });
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

  // Load recipes using React Query for better caching
  // Use the same fetchManualRecipes function as search page for consistent data structure
  const { data: backendRecipes = [], isLoading: isLoadingBackend, error: backendError, refetch: refetchBackendRecipes } = useQuery({
    queryKey: ['backend-recipes', isAuthenticated, userPreferences, refreshCounter], // Include refreshCounter to force new data
    queryFn: async () => {
      try {
        // Use the same function as the search page for consistent data structure
        console.log('🔍 Using fetchManualRecipes for consistent data across homepage and search');
        
        // Build query parameters based on user preferences
        let cuisines: string[] = [];
        let diets: string[] = [];
        
        if (isAuthenticated && userPreferences) {
          // Add user preferences as filters
          if (userPreferences.favoriteCuisines?.length) {
            cuisines = userPreferences.favoriteCuisines;
          }
          if (userPreferences.dietaryRestrictions?.length) {
            diets = userPreferences.dietaryRestrictions;
          }
        }
        
        // Use fetchManualRecipes with larger page size for homepage variety
        const pageSize = isAuthenticated && userPreferences ? 150 : 100;
        const result = await fetchManualRecipes('', '', {
          page: 1,
          pageSize: pageSize,
          cuisines: cuisines,
          diets: diets
        });
        
        console.log('🔍 HomePage fetchManualRecipes response:', {
          total: result.total,
          recipes: result.recipes?.length || 0,
          firstRecipe: result.recipes?.[0]?.title
        });
        
        return result.recipes || [];
      } catch (error) {
        console.error('Error fetching backend recipes:', error);
        return [];
      }
    },
    staleTime: 10 * 60 * 1000, // 10 minutes - same as search page
    gcTime: 10 * 60 * 1000, // 10 minutes
    refetchOnWindowFocus: false, // Don't refetch when window regains focus
    refetchOnMount: true, // Refetch when component mounts for fresh data
    refetchOnReconnect: false, // Don't refetch when reconnecting to network
    retry: 1, // Only retry once on failure
    enabled: true, // Always enabled
  });

  // Remove the separate recommendations query since we're now using the same endpoint
  // This ensures homepage and search page show the same data
  const backendRecommendations = backendRecipes; // Use the same data
  const isLoadingRecommendations = isLoadingBackend; // Use the same loading state
  
  // Debug logging for backend data changes
  useEffect(() => {
    console.log('🔄 Backend recipes data changed:', {
      length: backendRecipes?.length,
      firstRecipe: backendRecipes?.[0]?.title,
      timestamp: new Date().toISOString()
    });
  }, [backendRecipes]);

  // No longer needed - we use backendRecipes directly now

  // Query for popular recipes based on clicks and reviews
  const { data: popularRecipesData = [], isLoading: isLoadingPopular } = useQuery({
    queryKey: ['popular-recipes', user?.user_id],
    queryFn: () => getHomepagePopularRecipes(user?.user_id),
    staleTime: 10 * 60 * 1000, // 10 minutes (popular recipes don't change as frequently)
    retry: 1,
  });

  // Query for personal popular recipes
  const { data: personalPopularRecipesData = [], isLoading: isLoadingPersonalPopular } = useQuery({
    queryKey: ['personal-popular-recipes', user?.user_id],
    queryFn: () => getHomepagePopularRecipes(user?.user_id),
    staleTime: 10 * 60 * 1000,
    retry: 1,
    enabled: !!user?.user_id && showPersonalPopular, // Only fetch when user is logged in and toggle is on
  });

  // Log any query errors
  useEffect(() => {
    if (backendError) {
      console.warn('Failed to fetch backend recipes:', backendError);
    }
  }, [backendError]);

  // No longer needed - we use backendRecipes directly now
  // This ensures we have the same data structure as the search page

  // No longer needed - we use backendRecipes directly now

  // Helper function to select quality-based recipes from available recipes
  const selectQualityBasedRecipes = (recipes: Recipe[], limit: number): Recipe[] => {
    if (recipes.length === 0) return [];
    
    console.log('🔍 Quality-based selection starting with', recipes.length, 'recipes');
    
    // Score recipes based on quality indicators
    const scoredRecipes = recipes.map(recipe => {
      let score = 0;
      
      // Recipe completeness score (0-30 points)
      if (recipe.title || recipe.name) score += 10;
      if (recipe.description && recipe.description.length > 50) score += 5;
      if (recipe.ingredients && recipe.ingredients.length >= 5) score += 10;
      if (recipe.instructions && recipe.instructions.length > 100) score += 5;
      
      // Image quality score (0-20 points)
      if (recipe.image && recipe.image !== 'placeholder') score += 20;
      
      // Recipe type diversity bonus (0-15 points)
              if (recipe.cuisine && recipe.cuisine !== 'Unknown') {
          const cuisineValue = Array.isArray(recipe.cuisine) ? recipe.cuisine[0] : recipe.cuisine;
          if (cuisineValue !== 'Unknown') score += 10;
        }
      if (recipe.dietaryRestrictions && recipe.dietaryRestrictions.length > 0) score += 5;
      
      // User engagement indicators (0-10 points)
      if (recipe.ratings && Array.isArray(recipe.ratings) && recipe.ratings.length > 0) {
        const avgRating = recipe.ratings.reduce((sum: number, r: any) => sum + (r.score || 0), 0) / recipe.ratings.length;
        score += Math.min(10, avgRating * 2); // Max 10 points for 5-star rating
      }
      
      // Additional diversity bonus for different recipe types
      if (recipe.type === 'manual') score += 5; // Prefer user-created recipes
      if (recipe.type === 'spoonacular') score += 3; // Good for variety
      
      return { ...recipe, qualityScore: score };
    });
    
    // Sort by quality score
    const sortedByQuality = scoredRecipes.sort((a, b) => (b as any).qualityScore - (a as any).qualityScore);
    
    console.log('📊 Top 10 recipes by quality score:', sortedByQuality.slice(0, 10).map(r => ({
      title: r.title || r.name,
      score: (r as any).qualityScore,
      cuisine: r.cuisine,
      type: r.type
    })));
    
    // Select diverse recipes with smart distribution
    const selectedRecipes: Recipe[] = [];
    const selectedCuisines = new Set<string>();
    const selectedTypes = new Set<string>();
    
    // First pass: select highest quality recipes ensuring diversity
    for (const recipe of sortedByQuality) {
      if (selectedRecipes.length >= limit) break;
      
      // Categorize by cuisine - use cuisines array if available, fallback to cuisine field
      let cuisine = 'Unknown';
      
      if (Array.isArray(recipe.cuisines) && recipe.cuisines.length > 0) {
        // Use the first cuisine from the array
        cuisine = recipe.cuisines[0];
      } else if (recipe.cuisine) {
        // Handle both string and string[] types for cuisine field
        cuisine = Array.isArray(recipe.cuisine) ? recipe.cuisine[0] || 'Unknown' : recipe.cuisine;
      }
      const recipeType = recipe.type || 'unknown';
      
      // Always include the highest scoring recipe
      if (selectedRecipes.length === 0) {
        selectedRecipes.push(recipe);
        selectedCuisines.add(cuisine);
        selectedTypes.add(recipeType);
        continue;
      }
      
      // Prefer diversity in cuisines and types
      const hasCuisineDiversity = !selectedCuisines.has(cuisine);
      const hasTypeDiversity = !selectedTypes.has(recipeType);
      
      // If we have room for diversity, prioritize it
      if (selectedRecipes.length < limit / 2) {
        if (hasCuisineDiversity || hasTypeDiversity) {
          selectedRecipes.push(recipe);
          selectedCuisines.add(cuisine);
          selectedTypes.add(recipeType);
        }
      } else {
        // Fill remaining slots with high-quality recipes
        selectedRecipes.push(recipe);
        selectedCuisines.add(cuisine);
        selectedTypes.add(recipeType);
      }
    }
    
    // If we still need more recipes, fill with remaining high-quality ones
    if (selectedRecipes.length < limit) {
      for (const recipe of sortedByQuality) {
        if (selectedRecipes.length >= limit) break;
        if (!selectedRecipes.find(r => r.id === recipe.id)) {
          selectedRecipes.push(recipe);
        }
      }
    }
    
    console.log('🎯 Quality-based recipe selection completed:', {
      total: recipes.length,
      selected: selectedRecipes.length,
      cuisines: Array.from(selectedCuisines),
      types: Array.from(selectedTypes),
      avgQualityScore: selectedRecipes.reduce((sum, r) => sum + ((r as any).qualityScore || 0), 0) / selectedRecipes.length,
      selectedTitles: selectedRecipes.map(r => r.title || r.name)
    });
    
    return selectedRecipes;
  };

  // Combine and organize recipes into different categories
  const organizedRecipes = useMemo(() => {
    console.log('🔄 organizedRecipes useMemo recalculating...', {
      backendRecipesLength: backendRecipes?.length,
      backendRecommendationsLength: backendRecommendations?.length,
      timestamp: new Date().toISOString()
    });
    
    // Use the same data source as search page - only backendRecipes from fetchManualRecipes
    // This ensures we have the same complete data structure (macros, reviews, etc.)
    const allCombined = backendRecipes ? 
      backendRecipes.map(recipe => ({ ...recipe, type: 'external' as const })) : [];

    let recommendedRecipes = [];
    let popularRecipes = [];
    
    console.log('🍽️ Recipe organization - isAuthenticated:', isAuthenticated, 'userPreferences:', userPreferences);
    console.log('📊 Recipe counts - Backend:', backendRecipes?.length || 0, 'Using same source as search page');
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
      
      const hasAnyPreference = hasFavoriteFoods || hasFavoriteCuisines || hasDietaryRestrictions || 
                               hasFoodsToAvoid || hasCookingSkill || hasHealthGoals;
      
      console.log('🔍 Preference check:', {
        hasFavoriteFoods,
        hasFavoriteCuisines,
        hasDietaryRestrictions,
        hasFoodsToAvoid,
        hasCookingSkill,
        hasHealthGoals,
        hasAnyPreference
      });
      
      // Return true if any meaningful preference is set
      return hasAnyPreference;
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
        
        // Count initial cuisine distribution from backend
        const initialCuisineCounts: Record<string, number> = {};
        backendRecommendations.forEach(recipe => {
          let cuisine = 'Unknown';
          if (Array.isArray(recipe.cuisines) && recipe.cuisines.length > 0) {
            cuisine = recipe.cuisines[0];
          } else if (recipe.cuisine) {
            // Handle both string and string[] types for cuisine field
            cuisine = Array.isArray(recipe.cuisine) ? recipe.cuisine[0] || 'Unknown' : recipe.cuisine;
          }
          
          // If we still don't have a cuisine, try to detect it from the recipe data
          if (!cuisine || cuisine === 'Unknown') {
            if (recipe.cuisines && Array.isArray(recipe.cuisines) && recipe.cuisines.length > 0) {
              cuisine = recipe.cuisines[0];
            } else if (recipe.cuisine) {
              // Handle both string and string[] types for cuisine field
              cuisine = Array.isArray(recipe.cuisine) ? recipe.cuisine[0] || 'Unknown' : recipe.cuisine;
            }
          }
          
          // Normalize to lowercase for consistent counting
          cuisine = cuisine.toLowerCase();
          initialCuisineCounts[cuisine] = (initialCuisineCounts[cuisine] || 0) + 1;
        });
        console.log('🔍 Initial cuisine distribution from backend:', initialCuisineCounts);
        console.log('🔍 Total recipes from backend:', backendRecommendations.length);
        
        // ADDITIONAL DEBUG: Show cuisines field distribution (this is where the actual cuisine data is)
        const cuisinesFieldCounts: Record<string, number> = {};
        backendRecommendations.forEach(recipe => {
          const cuisines = Array.isArray((recipe as any).cuisines) ? (recipe as any).cuisines : [];
          cuisines.forEach((cuisine: string) => {
            if (cuisine && typeof cuisine === 'string') {
              // Normalize to lowercase for consistent counting
              const normalizedCuisine = cuisine.toLowerCase();
              cuisinesFieldCounts[normalizedCuisine] = (cuisinesFieldCounts[normalizedCuisine] || 0) + 1;
            }
          });
        });
        console.log('🔍 Cuisines field distribution from backend:', cuisinesFieldCounts);
        
        // Check if we're missing any user-selected cuisines in the backend data
        const userCuisines = userPreferences?.favoriteCuisines || [];
        const missingCuisinesInBackend = userCuisines.filter(userCuisine => 
          !Object.keys(cuisinesFieldCounts).some(backendCuisine => 
            backendCuisine.toLowerCase().includes(userCuisine.toLowerCase()) ||
            userCuisine.toLowerCase().includes(backendCuisine.toLowerCase())
          )
        );
        
        if (missingCuisinesInBackend.length > 0) {
          console.log('⚠️ WARNING: Missing cuisines in backend data:', missingCuisinesInBackend);
          console.log('🔍 This suggests the backend cuisine filtering is not working correctly');
        }

        // IMPROVED BALANCED DISTRIBUTION: Ensure fair cuisine distribution and guaranteed favorite foods
        const favoriteFoodsNorm: string[] = (userPreferences?.favoriteFoods || [])
          .map((f: any) => (f || '').toString().trim().toLowerCase())
          .filter(Boolean);

        console.log('🍔 Backend recommendations - prioritizing favorite foods:', favoriteFoodsNorm);

        // Step 1: Categorize all recipes by type and cuisine
        const favoriteFoodRecipes: any[] = [];
        const cuisineRecipes: Record<string, any[]> = {};
        const otherRecipes: any[] = [];
        
        backendRecommendations.forEach((recipe: any) => {
          const titleLower = ((recipe.title || recipe.name || '') as string).toLowerCase();
          const ingredientsLower = Array.isArray(recipe.ingredients) ? recipe.ingredients.map((i: any) => String(i).toLowerCase()) : [];
          const hasFavFood = favoriteFoodsNorm.length > 0 && favoriteFoodsNorm.some(f => titleLower.includes(f) || ingredientsLower.some(i => i.includes(f)));
          
          if (hasFavFood) {
            favoriteFoodRecipes.push(recipe);
          } else {
            // Categorize by cuisine - use cuisines array if available, fallback to cuisine field
            let cuisine = 'Unknown';
            if (Array.isArray(recipe.cuisines) && recipe.cuisines.length > 0) {
              // Use the first cuisine from the array
              cuisine = recipe.cuisines[0];
            } else if (recipe.cuisine) {
              // Handle both string and string[] types for cuisine field
              cuisine = Array.isArray(recipe.cuisine) ? recipe.cuisine[0] || 'Unknown' : recipe.cuisine;
            }
            
            // If we still don't have a cuisine, try to detect it from the recipe data
            if (!cuisine || cuisine === 'Unknown') {
              // Check if there's any cuisine information in the recipe
              if (recipe.cuisines && Array.isArray(recipe.cuisines) && recipe.cuisines.length > 0) {
                cuisine = recipe.cuisines[0];
              } else if (recipe.cuisine) {
                // Handle both string and string[] types for cuisine field
                cuisine = Array.isArray(recipe.cuisine) ? recipe.cuisine[0] || 'Unknown' : recipe.cuisine;
              }
            }
            
            // Normalize cuisine to lowercase to handle case sensitivity
            cuisine = cuisine.toLowerCase();
            
            if (!cuisineRecipes[cuisine]) {
              cuisineRecipes[cuisine] = [];
            }
            cuisineRecipes[cuisine].push(recipe);
          }
        });
        
        console.log('🍔 Categorization results:');
        console.log('  - Favorite food recipes:', favoriteFoodRecipes.length);
        console.log('  - Cuisine recipes:', Object.keys(cuisineRecipes).map(c => `${c}: ${cuisineRecipes[c].length}`));
        
        // Step 2: Build balanced recommendations
        const finalRecommendations: any[] = [];
        const targetCount = 8;
        
        // Priority 1: Guarantee at least 1-2 favorite foods (but not too many)
        const maxFavoriteFoods = Math.min(2, favoriteFoodRecipes.length);
        if (maxFavoriteFoods > 0) {
          finalRecommendations.push(...favoriteFoodRecipes.slice(0, maxFavoriteFoods));
          console.log(`🍔 Added ${maxFavoriteFoods} favorite foods (guaranteed)`);
        }
        
        // Priority 2: Fill remaining slots with balanced cuisine distribution
        const remainingSlots = targetCount - finalRecommendations.length;
        if (remainingSlots > 0) {
          const cuisines = Object.keys(cuisineRecipes);
          console.log(`🌍 Filling ${remainingSlots} slots with balanced cuisine distribution from ${cuisines.length} cuisines`);
          
          if (cuisines.length > 0) {
            // FIXED: Use proper round-robin distribution to ensure fair balance across cuisines
            // This prevents one cuisine from dominating the recommendations
            let added = true;
            let round = 0;
            
            while (finalRecommendations.length < targetCount && added) {
              added = false;
              
              // Go through each cuisine in order for this round
              for (let i = 0; i < cuisines.length && finalRecommendations.length < targetCount; i++) {
                const cuisine = cuisines[i];
                const recipes = cuisineRecipes[cuisine];
                
                if (recipes && recipes.length > 0) {
                  const recipe = recipes.shift()!;
                  finalRecommendations.push(recipe);
                  added = true;
                  console.log(`🌍 Round ${round + 1}: Added ${cuisine} recipe: ${recipe.title || recipe.name}`);
                }
              }
              
              round++;
            }
            
            // Debug: Show final distribution
            const finalCuisineCounts: Record<string, number> = {};
            finalRecommendations.forEach(r => {
              const cuisine = Array.isArray(r.cuisine) ? r.cuisine[0] : r.cuisine;
              const cuisineValue = (cuisine || 'Unknown').toLowerCase();
              finalCuisineCounts[cuisineValue] = (finalCuisineCounts[cuisineValue] || 0) + 1;
            });
            
            console.log('📊 Final cuisine distribution:', finalCuisineCounts);
          }
        }
        
        console.log('🎯 Final balanced recommendations:', finalRecommendations.length);
        console.log('📊 Final cuisine distribution:', finalRecommendations.map(r => {
          const cuisine = Array.isArray(r.cuisine) ? r.cuisine[0] : r.cuisine;
          return cuisine || 'Unknown';
        }));
        
        // Verify we have at least 1 favorite food
        const finalFavFoods = finalRecommendations.filter(r => {
          const titleLower = (r.title || r.name || '').toLowerCase();
          const ingredientsLower = Array.isArray(r.ingredients) ? r.ingredients.map((i: any) => String(i).toLowerCase()) : [];
          return favoriteFoodsNorm.some(f => titleLower.includes(f) || ingredientsLower.some(i => i.includes(f)));
        });
        
        console.log('🍔 Final favorite foods count:', finalFavFoods.length);
        if (finalFavFoods.length === 0 && favoriteFoodRecipes.length > 0) {
          console.log('⚠️ WARNING: No favorite foods in final recommendations despite having favorites available!');
          // Force add at least 1 favorite food
          finalRecommendations[0] = favoriteFoodRecipes[0];
          console.log('🔄 Forced addition of favorite food to first position');
        }
        
        // Final distribution summary
        const cuisineCounts: Record<string, number> = {};
        finalRecommendations.forEach(r => {
          const cuisine = Array.isArray(r.cuisine) ? r.cuisine[0] : r.cuisine;
          const cuisineValue = (cuisine || 'Unknown').toLowerCase();
          cuisineCounts[cuisineValue] = (cuisineCounts[cuisineValue] || 0) + 1;
        });
        
        console.log('📊 Final balanced distribution:', {
          totalRecipes: finalRecommendations.length,
          favoriteFoods: finalFavFoods.length,
          cuisineBreakdown: cuisineCounts,
          isBalanced: Object.values(cuisineCounts).every(count => count <= Math.ceil(targetCount / Object.keys(cuisineCounts).length) + 1)
        });
        
        recommendedRecipes = finalRecommendations.map(recipe => ({ ...recipe, type: 'external' as const }));
        
        // Debug: Check recipe data after processing
        console.log('🔍 First recipe after processing:', recommendedRecipes[0] ? {
          id: recommendedRecipes[0].id,
          title: recommendedRecipes[0].title,
          name: recommendedRecipes[0].name,
          cuisine: Array.isArray(recommendedRecipes[0].cuisine) ? recommendedRecipes[0].cuisine[0] : recommendedRecipes[0].cuisine
        } : 'No recipes');
      } else if (isLoadingRecommendations) {
        console.log('⏳ Backend recommendations still loading...');
        // Don't set recommendedRecipes yet, wait for loading to complete
      } else {
        console.log('🔄 Backend recommendations not available, using fallback filtering');
        console.log('❌ Backend recommendations failed or empty, falling back to frontend filtering');
        console.log('🔍 This is why you might not see favorite foods - using frontend fallback!');
        
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
          console.log('🥗 Filtering recipes for dietary restrictions:', dietaryRestrictions);
          filteredRecipes = allCombined.filter(recipe => {
            // Check both diets and dietaryRestrictions fields
            const recipeDiets = recipe.diets || [];
            const recipeDietaryRestrictions = (recipe as any).dietaryRestrictions || [];
            const allRecipeDietaryInfo = [...recipeDiets, ...recipeDietaryRestrictions];
            
            // For each user preference, check if the recipe satisfies it
            return dietaryRestrictions.every(prefDiet => {
              if (!prefDiet) return true;
              const prefLower = prefDiet.toLowerCase().trim();
              
              // Check if any recipe dietary info matches this preference
              return allRecipeDietaryInfo.some(diet => {
                if (!diet) return false;
                const dietLower = String(diet).toLowerCase().trim();
                
                // Handle various ways dietary restrictions might be expressed
                if (prefLower === 'vegetarian' && (dietLower === 'vegetarian' || dietLower === 'veg')) return true;
                if (prefLower === 'vegan' && dietLower === 'vegan') return true;
                if (prefLower === 'gluten-free' && (dietLower === 'gluten-free' || dietLower === 'gluten free' || dietLower === 'glutenfree')) return true;
                if (prefLower === 'dairy-free' && (dietLower === 'dairy-free' || dietLower === 'dairy free' || dietLower === 'dairyfree')) return true;
                if (prefLower === 'keto' && (dietLower === 'ketogenic' || dietLower === 'keto')) return true;
                if (prefLower === 'paleo' && (dietLower === 'paleo' || dietLower === 'paleolithic')) return true;
                if (prefLower === 'low-carb' && (dietLower === 'low-carb' || dietLower === 'low carb' || dietLower === 'lowcarb')) return true;
                if (prefLower === 'low-calorie' && (dietLower === 'low-calorie' || dietLower === 'low calorie' || dietLower === 'lowcalorie')) return true;
                if (prefLower === 'high-protein' && (dietLower === 'high-protein' || dietLower === 'high protein' || dietLower === 'highprotein')) return true;
                
                return false;
              });
            });
          });
          
          console.log('🥗 Recipes after dietary restriction filtering:', filteredRecipes.length);
        }
        
        // Smart recommendation logic: prioritize favorite foods first, then cuisine preferences
        const favoriteFoodsNorm: string[] = (favoriteFoods || []).map((f: any) => (f || '').toString().trim().toLowerCase()).filter(Boolean);
        
        // Step 1: Find ALL favorite food recipes and categorize them by cuisine overlap
        let favoriteFoodsInPreferredCuisines: any[] = [];
        let favoriteFoodsInOtherCuisines: any[] = [];
        
        if (favoriteFoodsNorm.length > 0) {
          console.log('🔍 Searching for favorite foods:', favoriteFoodsNorm);
          console.log('🔍 Available recipes to search:', filteredRecipes.length);
          
          // Debug: Show some sample recipe titles to see what we're working with
          console.log('🔍 Sample recipe titles:', filteredRecipes.slice(0, 5).map(r => ({
            title: r.title || (r as any).name,
            cuisines: (r as any).cuisines || [],
            cuisine: (r as any).cuisine
          })));
          
          const allFavoriteFoodRecipes = filteredRecipes.filter(recipe => {
            // Check if it's a favorite food
            const titleLower = ((recipe.title || (recipe as any).name || '') as string).toLowerCase();
            const ingredients = (recipe as any).ingredients || [];
            const ingredientsLower = Array.isArray(ingredients) ? 
              ingredients.map((i: any) => String(i).toLowerCase()) : [];
            
            // Debug: Log what we're checking
            const isFavoriteFood = favoriteFoodsNorm.some(food => {
              const titleMatch = titleLower.includes(food);
              const ingredientMatch = ingredientsLower.some((ing: string) => ing.includes(food));
              if (titleMatch || ingredientMatch) {
                console.log(`🍔 Found favorite food '${food}' in recipe: ${recipe.title || (recipe as any).name}`);
                console.log(`   Title match: ${titleMatch}, Ingredient match: ${ingredientMatch}`);
              }
              return titleMatch || ingredientMatch;
            });
            
            return isFavoriteFood;
          });
          
          console.log('🍔 Total favorite food recipes found:', allFavoriteFoodRecipes.length);
          
          // Categorize favorite foods by whether they're in preferred cuisines
          allFavoriteFoodRecipes.forEach(recipe => {
            const recipeCuisines = Array.isArray((recipe as any).cuisines) ? (recipe as any).cuisines : [];
            const recipeTitle = (recipe.title || (recipe as any).name || '').toLowerCase();
            
            const isInPreferredCuisine = favoriteCuisines && favoriteCuisines.length > 0 && favoriteCuisines.some(cuisine => {
              if (!cuisine) return false;
              const cuisineLower = cuisine.toLowerCase();
              return recipeCuisines.some((c: any) => c?.toLowerCase().includes(cuisineLower)) ||
                     recipeTitle.includes(cuisineLower);
            });
            
            if (isInPreferredCuisine) {
              favoriteFoodsInPreferredCuisines.push(recipe);
              console.log(`🍔 Favorite food in preferred cuisine: ${recipe.title || (recipe as any).name} (${recipeCuisines.join(', ')})`);
            } else {
              favoriteFoodsInOtherCuisines.push(recipe);
              console.log(`🍔 Favorite food in other cuisine: ${recipe.title || (recipe as any).name} (${recipeCuisines.join(', ')})`);
            }
          });
          
          console.log('🍔 Found favorite food recipes in preferred cuisines:', favoriteFoodsInPreferredCuisines.length);
          console.log('🍔 Found favorite food recipes in other cuisines:', favoriteFoodsInOtherCuisines.length);
        }
        
        // Step 2: Find recipes that match favorite cuisines (but aren't favorite foods)
        let cuisineMatchedRecipes: any[] = [];
        if (favoriteCuisines && favoriteCuisines.length > 0) {
          cuisineMatchedRecipes = filteredRecipes.filter(recipe => {
            // IMPROVED: More flexible cuisine matching logic
            // Check both cuisine and cuisines fields for better coverage
            const recipeCuisines = Array.isArray((recipe as any).cuisines) ? (recipe as any).cuisines : [];
            const singleCuisine = (recipe as any).cuisine ? [(recipe as any).cuisine] : [];
            const allRecipeCuisines = [...recipeCuisines, ...singleCuisine];
            
            // Normalize recipe cuisines for comparison
            const normalizedRecipeCuisines = allRecipeCuisines
              .filter(c => c && typeof c === 'string')
              .map(c => c.toLowerCase().trim());
            
            // Check if recipe matches ANY of the preferred cuisines
            const isInPreferredCuisine = favoriteCuisines.some(cuisine => {
              if (!cuisine) return false;
              const cuisineLower = cuisine.toLowerCase().trim();
              
              // Check for exact match or partial match
              return normalizedRecipeCuisines.some(recipeCuisine => 
                recipeCuisine === cuisineLower || 
                recipeCuisine.includes(cuisineLower) || 
                cuisineLower.includes(recipeCuisine)
              );
            });
            
            if (!isInPreferredCuisine) return false;
            
            // Check that it's NOT already a favorite food (to avoid duplicates)
            const titleLower = ((recipe.title || (recipe as any).name || '') as string).toLowerCase();
            const ingredients = (recipe as any).ingredients || [];
            const ingredientsLower = Array.isArray(ingredients) ? 
              ingredients.map((i: any) => String(i).toLowerCase()) : [];
            const isFavoriteFood = favoriteFoodsNorm.some(food => 
              titleLower.includes(food) || 
              ingredientsLower.some((ing: string) => ing.includes(food))
            );
            
            return !isFavoriteFood;
          });
          
          console.log('🌍 Found cuisine-matched recipes (excluding favorite foods):', cuisineMatchedRecipes.length);
          
          // IMPROVED: Better cuisine breakdown logging that shows actual cuisines from cuisines field
          const cuisineBreakdown: Record<string, number> = {};
          cuisineMatchedRecipes.forEach(recipe => {
            // Check both cuisine and cuisines fields for accurate breakdown
            const recipeCuisines = Array.isArray((recipe as any).cuisines) ? (recipe as any).cuisines : [];
            const singleCuisine = (recipe as any).cuisine ? [(recipe as any).cuisine] : [];
            const allCuisines = [...recipeCuisines, ...singleCuisine];
            
            // Use the first available cuisine for breakdown
            const primaryCuisine = allCuisines.find(c => c && typeof c === 'string') || 'Unknown';
            cuisineBreakdown[primaryCuisine] = (cuisineBreakdown[primaryCuisine] || 0) + 1;
          });
          console.log('🌍 Cuisine breakdown of matched recipes:', cuisineBreakdown);
          
          // ADDITIONAL DEBUG: Show what cuisines the user selected vs what we found
          console.log('🔍 User selected cuisines:', favoriteCuisines);
          console.log('🔍 Available cuisines in matched recipes:', Object.keys(cuisineBreakdown));
          
          // Check if we're missing any user-selected cuisines
          const missingCuisines = favoriteCuisines.filter(userCuisine => 
            !Object.keys(cuisineBreakdown).some(foundCuisine => 
              foundCuisine.toLowerCase().includes(userCuisine.toLowerCase()) ||
              userCuisine.toLowerCase().includes(foundCuisine.toLowerCase())
            )
          );
          
          if (missingCuisines.length > 0) {
            console.log('⚠️ WARNING: Missing cuisines from user selection:', missingCuisines);
            console.log('🔍 This suggests the cuisine matching logic is too restrictive');
          }
        }
        
        // Step 3: Build recommendations with intelligent favorite food distribution
        let finalRecommendations: any[] = [];
        
        // IMPROVED STRATEGY: Guarantee favorite foods while maintaining cuisine balance
        // - Favorite foods get 2-3 slots (25-37.5%) for personalization
        // - Cuisine preferences get 5-6 slots (62.5-75%) for variety
        // - This ensures users see their favorite foods while getting culinary diversity
        
        // Priority 1: Add favorite foods that are in preferred cuisines (with smart distribution)
        if (favoriteFoodsInPreferredCuisines.length > 0) {
          // Group favorite foods by cuisine for smart distribution
          const favFoodsByCuisine: Record<string, any[]> = {};
          
          favoriteFoodsInPreferredCuisines.forEach(recipe => {
            const recipeCuisines = Array.isArray((recipe as any).cuisines) ? (recipe as any).cuisines : [];
            const single = (recipe as any).cuisine ? [(recipe as any).cuisine.toString().toLowerCase()] : [];
            const allRecipeCuisines = [...recipeCuisines, ...single];
            
            // Find which preferred cuisine this recipe belongs to
            const matchCuisine = favoriteCuisines.find(sel => {
              if (!sel) return false;
              const selLower = sel.toLowerCase();
              return allRecipeCuisines.some(rc => rc?.toLowerCase().includes(selLower));
            });
            
            if (matchCuisine) {
              const cuisineKey = matchCuisine.toLowerCase();
              if (!favFoodsByCuisine[cuisineKey]) {
                favFoodsByCuisine[cuisineKey] = [];
              }
              favFoodsByCuisine[cuisineKey].push(recipe);
            }
          });
          
          // Smart distribution: Limit favorite foods per cuisine for better balance
          const maxFavFoodsPerCuisine = Math.min(1, Math.ceil(3 / Math.max(1, favoriteCuisines.length)));
          console.log('🍔 Frontend - Max favorite foods per cuisine:', maxFavFoodsPerCuisine);
          console.log('🍔 Frontend - Total favorite foods in preferred cuisines:', favoriteFoodsInPreferredCuisines.length);
          
          Object.entries(favFoodsByCuisine).forEach(([cuisine, recipes]) => {
            const recipesToAdd = Math.min(maxFavFoodsPerCuisine, recipes.length);
            finalRecommendations.push(...recipes.slice(0, recipesToAdd));
            console.log(`🍔 Added ${recipesToAdd} favorite foods from ${cuisine} cuisine (balanced approach)`);
          });
          
          console.log('🍔 Frontend - After adding preferred cuisine favorites:', finalRecommendations.length, 'recipes');
        }
        
        // Priority 2: Add favorite foods from other cuisines (limited for balance)
        if (favoriteFoodsInOtherCuisines.length > 0) {
          const remainingSlots = 8 - finalRecommendations.length;
          // Limit favorite foods from other cuisines to 1 slot for better balance
          const maxOtherCuisineFavs = Math.min(1, Math.min(remainingSlots, favoriteFoodsInOtherCuisines.length));
          
          if (maxOtherCuisineFavs > 0) {
            const otherFavsToAdd = Math.min(maxOtherCuisineFavs, favoriteFoodsInOtherCuisines.length);
            finalRecommendations.push(...favoriteFoodsInOtherCuisines.slice(0, otherFavsToAdd));
            console.log(`🍔 Added ${otherFavsToAdd} favorite foods from other cuisines (balanced approach)`);
          }
        }
        
        // Priority 3: Fill remaining slots with balanced cuisine recommendations
        if (cuisineMatchedRecipes.length > 0) {
          const remainingSlots = Math.max(0, 8 - finalRecommendations.length);
          
          if (remainingSlots > 0) {
            console.log(`🌍 Filling ${remainingSlots} remaining slots with balanced cuisine recommendations`);
            
            // Filter out recipes we already added as favorite foods
            const uniqueCuisineRecipes = cuisineMatchedRecipes.filter(recipe => 
              !finalRecommendations.some(fav => fav.id === recipe.id)
            );
            
            if (uniqueCuisineRecipes.length > 0) {
              // Group recipes by cuisine for balanced distribution
              const normalizedSelected = favoriteCuisines.map(c => (c || '').toString().trim().toLowerCase()).filter(Boolean);
              const groupsByCuisine: Record<string, any[]> = {};
              
              for (const c of normalizedSelected) {
                groupsByCuisine[c] = [];
              }
              
              // Assign recipes to their matching cuisines
              for (const recipe of uniqueCuisineRecipes) {
                const recipeCuisines = Array.isArray((recipe as any).cuisines) ? (recipe as any).cuisines : [];
                const single = (recipe as any).cuisine ? [(recipe as any).cuisine.toString().toLowerCase()] : [];
                const allRecipeCuisines = [...recipeCuisines, ...single];
                
                const matchCuisine = normalizedSelected.find(sel => 
                  allRecipeCuisines.some(rc => rc?.toLowerCase().includes(sel))
                );
                
                if (matchCuisine) {
                  groupsByCuisine[matchCuisine].push(recipe);
                }
              }
              
              // FIXED: Round-robin pick from each cuisine to fill remaining slots with better balance
              let added = true;
              let round = 0;
              
              while (finalRecommendations.length < 8 && added) {
                added = false;
                
                // Go through each cuisine in order for this round
                for (let i = 0; i < normalizedSelected.length && finalRecommendations.length < 8; i++) {
                  const cuisine = normalizedSelected[i];
                  const cuisineRecipes = groupsByCuisine[cuisine] || [];
                  
                  if (cuisineRecipes.length > 0) {
                    const recipe = cuisineRecipes.shift()!;
                    finalRecommendations.push(recipe);
                    added = true;
                    console.log(`🌍 Round ${round + 1}: Added ${cuisine} recipe: ${recipe.title || recipe.name}`);
                  }
                }
                
                round++;
              }
              
              console.log(`🌍 Added ${8 - finalRecommendations.length} cuisine-balanced recipes to fill recommendations`);
            }
          }
        }
        
        // GUARANTEE: Ensure we have at least 1 favorite food if available
        if (finalRecommendations.length > 0) {
          const finalFavFoods = finalRecommendations.filter(r => {
            const titleLower = (r.title || (r as any).name || '').toLowerCase();
            const ingredients = (r as any).ingredients || [];
            const ingredientsLower = Array.isArray(ingredients) ? ingredients.map((i: any) => String(i).toLowerCase()) : [];
            return favoriteFoodsNorm.some(food => titleLower.includes(food) || ingredientsLower.some(i => i.includes(food)));
          });
          
          console.log('🍔 Frontend fallback - Favorite foods in final recommendations:', finalFavFoods.length);
          
          // If no favorite foods in recommendations but we have favorites available, force add one
          if (finalFavFoods.length === 0 && (favoriteFoodsInPreferredCuisines.length > 0 || favoriteFoodsInOtherCuisines.length > 0)) {
            console.log('⚠️ WARNING: No favorite foods in frontend recommendations despite having favorites available!');
            
            // Find the best favorite food to add
            const bestFavoriteFood = favoriteFoodsInPreferredCuisines[0] || favoriteFoodsInOtherCuisines[0];
            if (bestFavoriteFood) {
              // Replace the first recipe with a favorite food
              finalRecommendations[0] = bestFavoriteFood;
              console.log('🔄 Forced addition of favorite food to first position:', bestFavoriteFood.title || bestFavoriteFood.name);
            }
          }
        }
        
        recommendedRecipes = finalRecommendations.slice(0, 16);  // Increased from 8 to 16 for better cuisine distribution
        console.log('🔄 Final frontend recommendations:', recommendedRecipes.length);
        
        // Debug: Show breakdown of final recommendations
        const finalFavFoods = recommendedRecipes.filter(r => {
          const titleLower = (r.title || (r as any).name || '').toLowerCase();
          const ingredients = (r as any).ingredients || [];
          const ingredientsLower = Array.isArray(ingredients) ? ingredients.map((i: any) => String(i).toLowerCase()) : [];
          return favoriteFoodsNorm.some(food => titleLower.includes(food) || ingredientsLower.some(i => i.includes(food)));
        });
        
        console.log('🍔 Frontend fallback - Favorite foods in final recommendations:', finalFavFoods.length);
        console.log('🍔 Frontend fallback - Favorite foods found:', finalFavFoods.map(r => r.title || (r as any).name));
        
        // Final distribution summary with cuisine balance check
        const cuisineCounts: Record<string, number> = {};
        recommendedRecipes.forEach(r => {
          const cuisines = (r as any).cuisines || [];
          const single = (r as any).cuisine ? [(r as any).cuisine.toString().toLowerCase()] : [];
          const allCuisines = [...cuisines, ...single];
          
          if (allCuisines.length > 0) {
            const primaryCuisine = allCuisines[0];
            cuisineCounts[primaryCuisine] = (cuisineCounts[primaryCuisine] || 0) + 1;
          } else {
            cuisineCounts['Unknown'] = (cuisineCounts['Unknown'] || 0) + 1;
          }
        });
        
        console.log('📊 Final frontend distribution summary:', {
          totalRecipes: recommendedRecipes.length,
          favoriteFoods: finalFavFoods.length,
          cuisineBreakdown: cuisineCounts,
          isBalanced: Object.values(cuisineCounts).every(count => count <= Math.ceil(8 / Object.keys(cuisineCounts).length) + 1)
        });
      }
    } else {
      console.log('ℹ️ No user preferences, using default recipe organization');
    }

    // Get remaining recipes for popular/newest sections
    const remainingRecipes = allCombined.filter(recipe => 
      !recommendedRecipes.find(r => (r.id || (r as any)._id) === (recipe.id || (recipe as any)._id) && r.type === recipe.type)
    );
    
    // Use real popular recipes data if available, otherwise fall back to quality-based selection
    if (showPersonalPopular && isAuthenticated && user?.user_id) {
      // Use personal popular recipes
      if (personalPopularRecipesData && personalPopularRecipesData.length > 0) {
        console.log('👤 Using personal popular recipes data:', personalPopularRecipesData.length);
        popularRecipes = personalPopularRecipesData.map(recipe => ({ ...recipe, type: 'external' as const }));
      } else {
        console.log('🔄 No personal popular recipes data, using quality-based selection instead of random');
        // Use quality-based selection from remaining recipes
        popularRecipes = selectQualityBasedRecipes(remainingRecipes as any[], 8);
      }
    } else if (popularRecipesData && Array.isArray(popularRecipesData) && popularRecipesData.length > 0) {
      console.log('🎯 Using global popular recipes data:', popularRecipesData.length);
      popularRecipes = popularRecipesData.map(recipe => ({ ...recipe, type: 'external' as const }));
    } else {
      console.log('🔄 No popular recipes data, using quality-based selection instead of random');
              // Use quality-based selection from remaining recipes
        popularRecipes = selectQualityBasedRecipes(remainingRecipes as any[], 8);
    }
    
    return {
      recommended: recommendedRecipes.slice(0, 8), // Show 16 recommended recipes for better cuisine distribution
      popular: popularRecipes.slice(0, 8)
    };
  }, [backendRecipes, popularRecipesData, isAuthenticated, userPreferences, showPersonalPopular, personalPopularRecipesData, backendRecommendations]);

  // Debug logging for organizedRecipes
  console.log('🔍 Organized recipes debug:', {
    popular: organizedRecipes.popular.map(r => ({ id: r.id, type: r.type, title: r.title || r.name })),
    recommended: organizedRecipes.recommended.map(r => ({ id: r.id, type: r.type, title: r.title || r.name }))
  });

  const isLoading = isLoadingBackend || isLoadingPopular || (showPersonalPopular && isLoadingPersonalPopular) || isLoadingRecommendations;

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



  // Handle favorite toggle for recipes
  const handleToggleFavorite = async (recipe: any) => {
    console.log('🎯 HomePage: Toggling favorite for recipe:', {
      id: recipe.id,
      title: recipe.title || recipe.name,
      currentFavorite: recipe.isFavorite,
      type: recipe.type
    });
    
    const updatedRecipe = {
      ...recipe,
      isFavorite: !recipe.isFavorite
    };
    
    // Update the recipe in storage
    updateRecipe(updatedRecipe);
    
    console.log('✅ HomePage: Recipe favorite updated in storage:', {
      id: updatedRecipe.id,
      newFavorite: updatedRecipe.isFavorite
    });
    
    // Update query cache data directly without invalidating (prevents refresh)
    queryClient.setQueryData(['backend-recipes', isAuthenticated, userPreferences, refreshCounter], (oldData: any) => {
      if (!oldData) return oldData;
      return oldData.map((r: any) => r.id === updatedRecipe.id ? updatedRecipe : r);
    });
    
    queryClient.setQueryData(['popular-recipes', user?.user_id], (oldData: any) => {
      if (!oldData) return oldData;
      return oldData.map((r: any) => r.id === updatedRecipe.id ? updatedRecipe : r);
    });
    
    queryClient.setQueryData(['personal-popular-recipes', user?.user_id], (oldData: any) => {
      if (!oldData) return oldData;
      return oldData.map((r: any) => r.id === updatedRecipe.id ? updatedRecipe : r);
    });
    
    // Only invalidate the local recipes query for favorites page updates
    queryClient.invalidateQueries({ queryKey: ['recipes'] });
    
    // Show toast notification
    toast({
      title: updatedRecipe.isFavorite ? "Added to favorites" : "Removed from favorites",
      description: `"${recipe.title || recipe.name}" has been ${updatedRecipe.isFavorite ? 'added to' : 'removed from'} your favorites.`,
    });
    
    console.log('🔄 HomePage: Cache updated directly without refresh');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <Header />
      
      <div className="pt-20">
        {/* Hero Section */}
        <section className="relative overflow-hidden bg-gradient-to-br from-recipe-primary via-recipe-primary/90 to-recipe-accent py-20 md:py-32">
          <div className="absolute inset-0 bg-black/10"></div>
          <div className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-20" style={{ backgroundImage: 'url(https://t4.ftcdn.net/jpg/04/43/37/07/360_F_443370711_sqHRnSIQovW6uyQ5ZwDpd4kjCG8Q6swm.jpg)' }}></div>
          
          <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <div className="max-w-4xl mx-auto">
              <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight title-gradient-flow">
                {welcomeMessage.title}
              </h1>
              <p className="text-xl md:text-2xl text-white/90 mb-10 max-w-3xl mx-auto leading-relaxed">
                {welcomeMessage.subtitle}
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                <Link to="/recipes">
                  <Button size="lg" variant="secondary" className="w-full sm:w-auto text-lg px-8 py-4 h-auto">
                    <Search className="mr-3 h-5 w-5" />
                    Browse All Recipes
                  </Button>
                </Link>
                {isAuthenticated ? (
                  <Link to="/meal-planner">
                    <Button size="lg" variant="outline" className="w-full sm:w-auto text-lg px-8 py-4 h-auto bg-white/20 text-white hover:bg-white/30 border-white/30">
                      <ChefHat className="mr-3 h-5 w-5" />
                      AI Meal Planner
                    </Button>
                  </Link>
                ) : (
                  <Link to="/signup">
                    <Button size="lg" variant="outline" className="w-full sm:w-auto text-lg px-8 py-4 h-auto bg-white/20 text-white hover:bg-white/30 border-white/30">
                      <Zap className="mr-3 h-5 w-5" />
                      Sign Up for AI Features
                    </Button>
                  </Link>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <section className="py-16 bg-white/40 border-b border-white/60 backdrop-blur">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 md:gap-8">
              {/* Stat 1 */}
              <div className="relative group rounded-2xl p-6 bg-white/70 backdrop-blur border border-white/60 shadow-sm hover:shadow-lg transition-transform duration-300 hover:-translate-y-1">
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-green-500/10 to-amber-500/10 opacity-0 group-hover:opacity-100 transition-opacity" aria-hidden></div>
                <div className="relative flex flex-col items-center text-center">
                  <div className="mb-4">
                    <div className="p-[2px] rounded-full bg-gradient-to-br from-green-500 to-amber-500">
                      <div className="rounded-full bg-white p-3">
                        <Award className="h-6 w-6 text-amber-600" />
                      </div>
                    </div>
                  </div>
                  <div className="text-3xl md:text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-green-600 to-amber-500 mb-1">
                    1000+
                  </div>
                  <div className="text-sm md:text-base text-gray-700 font-medium">Recipes Available</div>
                </div>
              </div>

              {/* Stat 2 */}
              <div className="relative group rounded-2xl p-6 bg-white/70 backdrop-blur border border-white/60 shadow-sm hover:shadow-lg transition-transform duration-300 hover:-translate-y-1">
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-green-500/10 to-amber-500/10 opacity-0 group-hover:opacity-100 transition-opacity" aria-hidden></div>
                <div className="relative flex flex-col items-center text-center">
                  <div className="mb-4">
                    <div className="p-[2px] rounded-full bg-gradient-to-br from-green-500 to-amber-500">
                      <div className="rounded-full bg-white p-3">
                        <ChefHat className="h-6 w-6 text-green-600" />
                      </div>
                    </div>
                  </div>
                  <div className="text-3xl md:text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-green-600 to-amber-500 mb-1">
                    AI-Powered
                  </div>
                  <div className="text-sm md:text-base text-gray-700 font-medium">Meal Planning</div>
                </div>
              </div>

              {/* Stat 3 */}
              <div className="relative group rounded-2xl p-6 bg-white/70 backdrop-blur border border-white/60 shadow-sm hover:shadow-lg transition-transform duration-300 hover:-translate-y-1">
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-green-500/10 to-amber-500/10 opacity-0 group-hover:opacity-100 transition-opacity" aria-hidden></div>
                <div className="relative flex flex-col items-center text-center">
                  <div className="mb-4">
                    <div className="p-[2px] rounded-full bg-gradient-to-br from-green-500 to-amber-500">
                      <div className="rounded-full bg-white p-3">
                        <Users className="h-6 w-6 text-emerald-600" />
                      </div>
                    </div>
                  </div>
                  <div className="text-3xl md:text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-green-600 to-amber-500 mb-1">
                    Personalized
                  </div>
                  <div className="text-sm md:text-base text-gray-700 font-medium">Recommendations</div>
                </div>
              </div>

              {/* Stat 4 */}
              <div className="relative group rounded-2xl p-6 bg-white/70 backdrop-blur border border-white/60 shadow-sm hover:shadow-lg transition-transform duration-300 hover:-translate-y-1">
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-green-500/10 to-amber-500/10 opacity-0 group-hover:opacity-100 transition-opacity" aria-hidden></div>
                <div className="relative flex flex-col items-center text-center">
                  <div className="mb-4">
                    <div className="p-[2px] rounded-full bg-gradient-to-br from-green-500 to-amber-500">
                      <div className="rounded-full bg-white p-3">
                        <Zap className="h-6 w-6 text-amber-600" />
                      </div>
                    </div>
                  </div>
                  <div className="text-3xl md:text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-green-600 to-amber-500 mb-1">
                    Unlimited
                  </div>
                  <div className="text-sm md:text-base text-gray-700 font-medium">Access</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Recipe Sections */}
        <section className="py-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            
            {/* Recommended Recipes - Only for authenticated users */}
            {isAuthenticated && (
              <div className="mb-16">
                <div className="flex justify-between items-center mb-8">
                  <div>
                    <h2 className="text-3xl font-bold text-gray-900 mb-2">Recommended for You</h2>
                    <p className="text-gray-600">Personalized recipe suggestions based on your preferences</p>
                  </div>
                  <div className="flex items-center space-x-3">
                    <Button
                      onClick={handleRefreshRecommendations}
                      disabled={isLoadingRecommendations}
                      variant="outline"
                      size="sm"
                    >
                      {isLoadingRecommendations ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <RefreshCw className="mr-2 h-4 w-4" />
                      )}
                      Refresh
                    </Button>
                    <Link to="/preferences">
                      <Button variant="outline">
                        <TrendingUp className="mr-2 h-4 w-4" />
                        Update Preferences
                      </Button>
                    </Link>
                  </div>
                </div>
                
                {/* Refresh feedback and counter */}
                <div className="flex items-center justify-between mb-4">
                  {refreshFeedback && (
                    <div className={`text-sm font-medium px-4 py-2 rounded-md ${
                      refreshFeedback.includes('Failed') 
                        ? 'bg-red-100 text-red-700 border border-red-200' 
                        : refreshFeedback.includes('Refreshing')
                        ? 'bg-blue-100 text-blue-700 border border-blue-200'
                        : 'bg-green-100 text-green-700 border border-green-200'
                    }`}>
                      {refreshFeedback}
                    </div>
                  )}
                  
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
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-4 gap-6">
                    {organizedRecipes.recommended.map((recipe, index) => {
                      console.log('Recommended recipe:', { id: recipe.id, type: recipe.type, isExternal: recipe.type === 'external' });
                      return (
                        <RecipeCard 
                          key={`recommended-${recipe.id}-${index}`} 
                          recipe={recipe} 
                          isExternal={recipe.type === 'external'}
                          onToggleFavorite={handleToggleFavorite}
                        />
                      );
                    })}
                  </div>
                )}

                {!isLoading && organizedRecipes.recommended.length === 0 && (
                  <div className="text-center py-16 bg-white rounded-2xl shadow-lg">
                    <div className="w-20 h-20 bg-recipe-primary/10 rounded-full flex items-center justify-center mx-auto mb-6">
                      <TrendingUp className="h-10 w-10 text-recipe-primary" />
                    </div>
                    <h3 className="text-2xl font-semibold text-gray-900 mb-3">No Recommendations Yet</h3>
                    <p className="text-gray-600 mb-6 max-w-md mx-auto">
                      {userPreferences 
                        ? "We're working on finding the perfect recipes for you. Try updating your preferences for better matches!"
                        : "Set your food preferences, dietary restrictions, and favorite cuisines to unlock personalized recipe suggestions!"
                      }
                    </p>
                    <div className="space-y-3">
                      <Link to="/preferences">
                        <Button size="lg">
                          <TrendingUp className="mr-2 h-4 w-4" />
                          {userPreferences ? 'Update Preferences' : 'Set Preferences Now'}
                        </Button>
                      </Link>
                      {!userPreferences && (
                        <div className="text-sm text-gray-500">
                          <p>💡 <strong>Pro tip:</strong> The more preferences you set, the better your recommendations will be!</p>
                        </div>
                      )}
                    </div>
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
                  {[...Array(8)].map((_, i) => (
                    <div key={i} className="bg-white rounded-lg shadow-md p-4 animate-pulse">
                      <div className="bg-gray-300 h-48 rounded-lg mb-4"></div>
                      <div className="bg-gray-300 h-4 rounded mb-2"></div>
                      <div className="bg-gray-300 h-3 rounded w-2/3"></div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-4 gap-6">
                  {organizedRecipes.popular.map((recipe, index) => {
                    console.log('Popular recipe:', { id: recipe.id, type: recipe.type, isExternal: recipe.type === 'external' });
                    return (
                      <RecipeCard 
                        key={`popular-${recipe.id}-${index}`} 
                        recipe={recipe} 
                        isExternal={recipe.type === 'external'}
                        onToggleFavorite={handleToggleFavorite}
                      />
                    );
                  })}
                </div>
              )}

              {!isLoading && organizedRecipes.popular.length === 0 && (
                <div className="text-center py-16 bg-white rounded-2xl shadow-lg">
                  <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
                    <ThumbsUp className="h-10 w-10 text-gray-400" />
                  </div>
                  <h3 className="text-2xl font-semibold text-gray-900 mb-3">No Popular Recipes Yet</h3>
                  <p className="text-gray-600">Check back soon for trending recipes!</p>
                </div>
              )}
            </div>



          </div>
        </section>

        {/* Call to Action for Non-Authenticated Users */}
        {!isAuthenticated && (
          <section className="py-20 bg-gradient-to-r from-recipe-primary to-recipe-accent">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
              <div className="w-20 h-20 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-8">
                <Zap className="h-10 w-10 text-white" />
              </div>
              <h2 className="text-4xl font-bold text-white mb-6">
                Ready to Unlock AI-Powered Cooking?
              </h2>
              <p className="text-xl text-white/90 mb-8 max-w-2xl mx-auto leading-relaxed">
                Join thousands of home cooks using AI to plan their meals and discover new recipes. 
                Get personalized recommendations, smart meal planning, and more.
              </p>
              
              {/* Preference Setup Guide */}
              <div className="bg-white/10 rounded-2xl p-6 mb-8 max-w-3xl mx-auto">
                <h3 className="text-2xl font-semibold text-white mb-4">🚀 Quick Setup Guide</h3>
                <div className="grid md:grid-cols-3 gap-4 text-left">
                  <div className="text-center">
                    <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-3">
                      <span className="text-white font-bold text-lg">1</span>
                    </div>
                    <p className="text-white/90 text-sm">Sign up for your free account</p>
                  </div>
                  <div className="text-center">
                    <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-3">
                      <span className="text-white font-bold text-lg">2</span>
                    </div>
                    <p className="text-white/90 text-sm">Set your food preferences & dietary needs</p>
                  </div>
                  <div className="text-center">
                    <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-3">
                      <span className="text-white font-bold text-lg">3</span>
                    </div>
                    <p className="text-white/90 text-sm">Get personalized recipe recommendations!</p>
                  </div>
                </div>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link to="/signup">
                  <Button size="lg" variant="secondary" className="w-full sm:w-auto text-lg px-8 py-4 h-auto">
                    <Zap className="mr-2 h-4 w-4" />
                    Sign Up Free
                  </Button>
                </Link>
                <Link to="/signin">
                  <Button size="lg" variant="outline" className="w-full sm:w-auto text-lg px-8 py-4 h-auto bg-white/20 text-white hover:bg-white/30 border-white/30">
                    Sign In
                  </Button>
                </Link>
              </div>
            </div>
          </section>
        )}

        {/* Preference Setup Reminder for Authenticated Users */}
        {isAuthenticated && !userPreferences && (
          <section className="py-16 bg-gradient-to-r from-orange-500 to-orange-600">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
              <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-6">
                <TrendingUp className="h-8 w-8 text-white" />
              </div>
              <h2 className="text-3xl font-bold text-white mb-4">
                Complete Your Profile for Personalized Recommendations!
              </h2>
              <p className="text-lg text-white/90 mb-6 max-w-2xl mx-auto">
                Set your food preferences, dietary restrictions, and favorite cuisines to unlock 
                AI-powered recipe suggestions tailored just for you.
              </p>
              <Link to="/preferences">
                <Button size="lg" variant="secondary" className="text-lg px-8 py-4 h-auto">
                  <TrendingUp className="mr-2 h-4 w-4" />
                  Set Your Preferences Now
                </Button>
              </Link>
            </div>
          </section>
        )}
      </div>
    </div>
  );
};

export default HomePage;

