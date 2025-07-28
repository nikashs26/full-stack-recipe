import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchManualRecipes } from '../lib/manualRecipes';
import { DietaryRestriction } from '../types/recipe';

// Helper function to convert string array to DietaryRestriction array
const toDietaryRestrictions = (restrictions?: string[]): DietaryRestriction[] => {
  if (!restrictions) return [];
  return restrictions.filter((d): d is DietaryRestriction => 
    ['vegetarian', 'vegan', 'gluten-free', 'dairy-free', 'keto', 'paleo'].includes(d)
  );
};
import { Loader2, Search, Filter, X, ChefHat } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import RecipeCard from '@/components/RecipeCard';
import { Input } from '@/components/ui/input';
import { RecipeFilters } from '@/components/RecipeFilters';
import { useDebounce } from '../hooks/useDebounce';
import { useMediaQuery } from '../hooks/use-media-query';
import { Drawer, DrawerContent, DrawerTrigger } from '@/components/ui/drawer';
import Header from '../components/Header';

// Base recipe type that includes all possible fields from different sources
type Recipe = {
  // Core fields
  id: string | number;
  name: string;
  title?: string;
  description?: string;
  image?: string;
  imageUrl?: string;
  
  // Cuisine and categories
  cuisine: string;
  cuisines?: string[];
  
  // Dietary information
  dietaryRestrictions: DietaryRestriction[];
  diets?: DietaryRestriction[];
  
  // Ingredients and instructions
  ingredients: Array<{
    id?: number | string;
    name: string;
    original?: string;
    amount?: string | number;
    unit?: string;
  }>;
  
  instructions: string | string[];
  analyzedInstructions?: any[];
  
  // Timing and servings
  prepTime?: number;
  cookTime?: number;
  totalTime?: number;
  readyInMinutes?: number;
  ready_in_minutes?: number;
  cookingTime?: string;
  servings?: number;
  
  // Difficulty and ratings
  difficulty?: 'easy' | 'medium' | 'hard';
  ratings: Array<{ score: number; count: number }> | number[];
  averageRating?: number;
  
  // Source and metadata
  source?: string;
  sourceUrl?: string;
  summary?: string;
  
  // Internal fields
  type?: 'manual' | 'spoonacular' | 'saved';
  isFavorite?: boolean;
  comments?: any[];
  createdAt?: string;
  updatedAt?: string;
};

type NormalizedRecipe = {
  id: string;
  title: string;
  description: string;
  imageUrl?: string;
  ready_in_minutes?: number;
  servings?: number;
  sourceUrl?: string;
  summary?: string;
  instructions?: string | string[];
  analyzedInstructions?: any[];
  ingredients: Array<{ name: string; amount?: string; unit?: string }>;
  cuisines: string[];
  dietaryRestrictions: string[];
  type: 'saved' | 'manual' | 'spoonacular';
};

const RecipesPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [ingredientTerm, setIngredientTerm] = useState("");
  const [ingredientQuery, setIngredientQuery] = useState("");
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [selectedCuisines, setSelectedCuisines] = useState<string[]>([]);
  const [selectedDiets, setSelectedDiets] = useState<string[]>([]);
  const [favoriteFoods, setFavoriteFoods] = useState<string[]>([]);
  const [showMobileFilters, setShowMobileFilters] = useState(false);
  const [showLoading, setShowLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const recipesPerPage = 20;
  
  const isDesktop = useMediaQuery("(min-width: 1024px)");
  const debouncedSearchQuery = useDebounce(searchQuery, 500);
  
  // Reset to first page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, ingredientQuery, selectedCuisines, selectedDiets]);

  // Fetch user preferences to get favorite foods
  const { data: userPreferences } = useQuery({
    queryKey: ['userPreferences'],
    queryFn: async () => {
      try {
        const response = await fetch('http://localhost:5003/api/user/preferences', {
          credentials: 'include',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        if (!response.ok) throw new Error('Failed to fetch user preferences');
        return await response.json();
      } catch (error) {
        console.error('Error fetching user preferences:', error);
        return null;
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
    enabled: !!localStorage.getItem('token'), // Only fetch if user is logged in
  });

  // Update favorite foods when user preferences change
  useEffect(() => {
    if (userPreferences?.favoriteFoods) {
      setFavoriteFoods(userPreferences.favoriteFoods);
    }
  }, [userPreferences]);

  // Fetch all recipes from ChromaDB with search and filters
  const { 
    data: recipes = [], 
    isLoading: isLoadingRecipes, 
    isFetching 
  } = useQuery<Recipe[]>({
    queryKey: ['recipes', debouncedSearchQuery, ingredientQuery, selectedCuisines, selectedDiets, favoriteFoods],
    queryFn: async () => {
      try {
        const result = await fetchManualRecipes(
          debouncedSearchQuery, 
          ingredientQuery, 
          {
            page: 1,
            pageSize: 1000,
            cuisines: selectedCuisines,
            diets: selectedDiets,
            favoriteFoods: favoriteFoods
          }
        );
        return result as unknown as Recipe[];
      } catch (error) {
        console.error('Error fetching recipes:', error);
        throw error;
      }
    },
    staleTime: 5 * 60 * 1000,
    retry: 1,
    refetchOnWindowFocus: false,
  });

  // Debounce search inputs
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearchQuery(searchTerm);
    }, 500);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Debounce ingredient search
  const debouncedIngredientQuery = useDebounce(ingredientTerm, 500);
  
  useEffect(() => {
    setIngredientQuery(debouncedIngredientQuery);
  }, [debouncedIngredientQuery]);

  // Normalize recipes to a common format
  const normalizedRecipes = useMemo<NormalizedRecipe[]>(() => {
    console.log('Raw recipes from API:', recipes?.length, recipes);
    if (!Array.isArray(recipes)) return [];
    
    return recipes.map(recipe => {
      // Helper to ensure we always return an array of strings
      const normalizeList = (items: any): string[] => {
        if (!items) return [];
        if (Array.isArray(items)) {
          return items
            .map(item => String(item).trim())
            .filter(item => item.length > 0);
        }
        if (typeof items === 'string') {
          return items.split(',')
            .map(item => item.trim())
            .filter(item => item.length > 0);
        }
        return [String(items)].filter(Boolean);
      };

      // Extract cuisines from various possible fields
      const cuisines = [
        ...normalizeList(recipe.cuisines),
        ...normalizeList(recipe.cuisine),
        ...(recipe.type === 'manual' && 'cuisine' in recipe ? normalizeList(recipe.cuisine) : []),
        ...(recipe.type === 'spoonacular' && 'cuisines' in recipe ? normalizeList(recipe.cuisines) : [])
      ].filter((value, index, self) => self.indexOf(value) === index); // Remove duplicates

      // Extract dietary restrictions from various possible fields
      const dietaryRestrictions = [
        ...normalizeList(recipe.diets),
        ...normalizeList(recipe.dietaryRestrictions),
        ...(recipe.type === 'manual' && 'diets' in recipe ? normalizeList(recipe.diets) : []),
        ...(recipe.type === 'spoonacular' && 'diets' in recipe ? normalizeList(recipe.diets) : [])
      ].filter((value, index, self) => self.indexOf(value) === index); // Remove duplicates

      return {
        id: String(recipe.id || Math.random().toString(36).substr(2, 9)),
        title: recipe.title || 'Untitled Recipe',
        description: recipe.description || '',
        imageUrl: recipe.image || '/placeholder-recipe.jpg',
        type: recipe.type || 'manual',
        cuisines,
        dietaryRestrictions,
        ready_in_minutes: recipe.type === 'manual' 
          ? (recipe as ManualRecipe).ready_in_minutes 
          : (recipe as SpoonacularRecipe).readyInMinutes,
        ingredients: recipe.type === 'spoonacular' && 'extendedIngredients' in recipe && recipe.extendedIngredients
          ? recipe.extendedIngredients.map(ing => ({
              name: ing.name,
              amount: ing.amount.toString(),
              unit: ing.unit || ''
            }))
          : recipe.type === 'manual' && 'ingredients' in recipe && Array.isArray(recipe.ingredients)
            ? recipe.ingredients.map(ing => ({
                name: ing.name,
                amount: ing.amount?.toString(),
                unit: ing.unit || ''
              }))
            : [],
        servings: recipe.type === 'spoonacular' ? (recipe as SpoonacularRecipe).servings : 4,
        sourceUrl: recipe.type === 'spoonacular' ? (recipe as SpoonacularRecipe).sourceUrl : '',
        summary: recipe.type === 'spoonacular' ? (recipe as SpoonacularRecipe).summary : '',
        analyzedInstructions: recipe.type === 'spoonacular' 
          ? (recipe as SpoonacularRecipe).analyzedInstructions 
          : []
      };
    });
  }, [recipes]);

  // Debug effect to track recipe counts
  useEffect(() => {
    console.log('Current recipe count:', normalizedRecipes.length);
    console.log('Sample recipe IDs:', normalizedRecipes.slice(0, 5).map(r => r.id));
  }, [normalizedRecipes]);

  // Filter and sort recipes - only show recipes that exist in local cache
  const filteredRecipes = useMemo(() => {
    // Filter out any recipes with negative IDs (Spoonacular recipes)
    return normalizedRecipes.filter(recipe => {
      // Only include recipes with positive numeric IDs or string IDs that don't start with 'recipe_'
      const id = recipe.id.toString();
      return !id.startsWith('recipe_') || !/^recipe_-?\d+$/.test(id);
    });
  }, [normalizedRecipes]);

  // Get current recipes for the current page
  const indexOfLastRecipe = currentPage * recipesPerPage;
  const indexOfFirstRecipe = indexOfLastRecipe - recipesPerPage;
  const currentRecipes = filteredRecipes.slice(indexOfFirstRecipe, indexOfLastRecipe);
  const totalPages = Math.ceil(filteredRecipes.length / recipesPerPage);

  const handleSearch = useCallback((term: string) => {
    setSearchTerm(term);
    
    // Scroll to results after a short delay to allow re-render
    const timer = setTimeout(() => {
      const resultsSection = document.getElementById('recipe-results');
      if (resultsSection) {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }, 100);
    
    return () => clearTimeout(timer);
  }, []);

  const handleCuisineToggle = useCallback((cuisine: string) => {
    setSelectedCuisines(prev => 
      prev.includes(cuisine)
        ? prev.filter(c => c !== cuisine)
        : [...prev, cuisine]
    );
  }, []);

  const handleDietToggle = useCallback((diet: string) => {
    setSelectedDiets(prev => 
      prev.includes(diet)
        ? prev.filter(d => d !== diet)
        : [...prev, diet]
    );
  }, []);

  const clearAllFilters = useCallback(() => {
    setSelectedCuisines([]);
    setSelectedDiets([]);
    setSearchQuery("");
    setSearchTerm("");
    setIngredientQuery("");
    setIngredientTerm("");
  }, []);

  // Show loading state only when we have a search query and data is being fetched
  const isLoading = useMemo(() => 
    (isLoadingRecipes || isFetching) && searchQuery !== '', 
    [isLoadingRecipes, isFetching, searchQuery]
  );
  
  useEffect(() => {
    if (isLoading) {
      const timer = setTimeout(() => setShowLoading(true), 200);
      return () => clearTimeout(timer);
    } else {
      setShowLoading(false);
    }
  }, [isLoading]);

  const renderFilters = useCallback(() => (
    <div className="space-y-6">
      <RecipeFilters
        searchQuery={searchTerm}
        ingredientQuery={ingredientTerm}
        selectedCuisines={selectedCuisines}
        selectedDiets={selectedDiets}
        onSearchChange={setSearchTerm}
        onIngredientChange={setIngredientTerm}
        onCuisineToggle={handleCuisineToggle}
        onDietToggle={handleDietToggle}
        onClearFilters={clearAllFilters}
      />
    </div>
  ), [searchQuery, selectedCuisines, selectedDiets, handleCuisineToggle, handleDietToggle, clearAllFilters]);

  const renderMobileFilters = useCallback(() => (
    <Drawer open={showMobileFilters} onOpenChange={setShowMobileFilters}>
      <div className="fixed bottom-6 right-6 z-10 lg:hidden">
        <Button
          onClick={() => setShowMobileFilters(true)}
          className="rounded-full w-14 h-14 shadow-lg"
          size="icon"
          aria-label="Open filters"
        >
          <Filter className="h-6 w-6" />
        </Button>
      </div>
      <DrawerContent className="h-[90vh] px-4 pb-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">Filters</h2>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setShowMobileFilters(false)}
            aria-label="Close filters"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>
        {renderFilters()}
      </DrawerContent>
    </Drawer>
  ), [showMobileFilters, renderFilters]);

  const renderRecipeCard = useCallback((recipe: NormalizedRecipe, index: number) => {
    // Convert ingredients to the expected format
    const normalizedIngredients = (recipe.ingredients || []).map(ing => ({
      name: typeof ing === 'string' ? ing : ing.name,
      amount: typeof ing === 'string' ? undefined : ing.amount?.toString()
    }));

    // Convert dietary restrictions to the correct type
    const normalizedDietaryRestrictions = toDietaryRestrictions(recipe.dietaryRestrictions);

    // Create the base recipe object
    const recipeObj: Recipe = {
      id: recipe.id.toString(),
      title: recipe.title,
      description: recipe.description || '',
      image: recipe.imageUrl || '/placeholder-recipe.jpg',
      type: recipe.type === 'spoonacular' ? 'spoonacular' : 'manual',
      cuisines: recipe.cuisines || [],
      cuisine: recipe.cuisines?.[0] || '',
      dietaryRestrictions: normalizedDietaryRestrictions,
      diets: normalizedDietaryRestrictions, // Use the same restrictions for diets
      instructions: Array.isArray(recipe.instructions) 
        ? recipe.instructions 
        : recipe.instructions 
          ? [recipe.instructions] 
          : ['No instructions available'],
      servings: recipe.servings || 4,
      cookingTime: recipe.ready_in_minutes ? `${recipe.ready_in_minutes} minutes` : 'Not specified',
      difficulty: 'medium',
      ratings: [],
      comments: [],
      ingredients: normalizedIngredients,
      // Handle both timing formats
      ...(recipe.ready_in_minutes && { ready_in_minutes: recipe.ready_in_minutes }),
      ...(recipe.ready_in_minutes && { readyInMinutes: recipe.ready_in_minutes }),
      // Spoonacular specific
      ...(recipe.type === 'spoonacular' && {
        sourceUrl: recipe.sourceUrl,
        summary: recipe.summary,
        analyzedInstructions: recipe.analyzedInstructions || []
      })
    };

    // Create the card data with additional UI-specific properties
    const recipeForCard: Recipe = {
      ...recipeObj,
      id: recipeObj.id,
      name: recipe.title,
      image: recipeObj.image || '/placeholder-recipe.jpg',
      imageUrl: recipe.imageUrl || '/placeholder-recipe.jpg',
      source: recipe.type === 'spoonacular' ? 'spoonacular' : 'local',
      cookingTime: recipeObj.cookingTime || recipeObj.cookTime?.toString() || 'Not specified',
      difficulty: 'medium',
      ratings: [],
      comments: [],
      instructions: Array.isArray(recipeObj.instructions) 
        ? recipeObj.instructions 
        : [recipeObj.instructions || 'No instructions available'],
      dietaryRestrictions: normalizedDietaryRestrictions,
      diets: normalizedDietaryRestrictions,
      ingredients: normalizedIngredients
    };
    
    return (
      <div key={`${recipe.type}-${recipe.id}-${index}`} className="h-full">
        <RecipeCard 
          recipe={recipeForCard}
          isExternal={recipe.type === 'spoonacular'}
          onClick={() => {
            if (recipe.type === 'spoonacular') {
              navigate(`/external-recipe/${recipe.id}`, { 
                state: { source: 'spoonacular' } 
              });
            } else {
              navigate(`/recipe/${recipe.id}`);
            }
          }}
        />
      </div>
    );
  }, [navigate]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100">
      <Header />
      <main className="container mx-auto px-4 py-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-primary to-amber-600 bg-clip-text text-transparent">
            Discover Culinary Delights
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Search through thousands of recipes to find your next favorite meal. Filter by cuisine, dietary needs, or ingredients.
          </p>
        </div>

        {/* Search Bar */}
        <Card className="mx-auto max-w-3xl shadow-lg border-0 bg-white/80 backdrop-blur-sm">
          <CardHeader>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <Input
                type="text"
                placeholder="Search for recipes..."
                className="pl-10 py-6 text-base border-0 shadow-sm focus-visible:ring-2 focus-visible:ring-primary/50"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}

                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleSearch(searchTerm);
                  }
                }}
                aria-label="Search recipes"
              />
              <Button 
                className="absolute right-2 top-1/2 transform -translate-y-1/2 h-10"
                onClick={() => handleSearch(searchTerm)}
                aria-label="Search"
              >
                Search
              </Button>
            </div>
          </CardHeader>
        </Card>

        {/* Main Content Area */}
        <div className="flex flex-col lg:flex-row gap-8 mt-8">
          {/* Filters - Left Sidebar */}
          <div className="lg:w-80 flex-shrink-0">
            <div className="sticky top-24">
              {isDesktop ? (
                <>
                  <div className="flex justify-between items-center mb-4">
                    <h2 className="text-lg font-semibold">Filters</h2>
                    {(selectedCuisines.length > 0 || selectedDiets.length > 0) && (
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        onClick={clearAllFilters}
                        className="text-sm"
                      >
                        Clear all
                      </Button>
                    )}
                  </div>
                  {renderFilters()}
                </>
              ) : (
                renderMobileFilters()
              )}
            </div>
          </div>

          {/* Recipe Results - Main Content */}
          <div className="flex-1 min-w-0">
            <div id="recipe-results" className="pb-8">
              <div className="mb-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-1">
                  {searchTerm ? `Search Results for "${searchTerm}"` : 'All Recipes'}
                </h2>
                <p className="text-gray-600">
                  {filteredRecipes.length} {filteredRecipes.length === 1 ? 'recipe' : 'recipes'} found
                </p>
              </div>

              {showLoading ? (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                  {[...Array(8)].map((_, i) => (
                    <div key={i} className="bg-white rounded-lg shadow-md p-4 animate-pulse">
                      <div className="bg-gray-200 h-48 rounded-lg mb-4"></div>
                      <div className="bg-gray-200 h-4 rounded mb-2"></div>
                      <div className="bg-gray-200 h-3 rounded w-2/3"></div>
                    </div>
                  ))}
                </div>
              ) : filteredRecipes.length > 0 ? (
                <>
                  <div className="grid md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-6">
                    {currentRecipes.map((recipe, index) => renderRecipeCard(recipe, index))}
                  </div>
                  
                  {/* Pagination Controls */}
                  {totalPages > 1 && (
                    <div className="mt-8 flex items-center justify-center space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                        disabled={currentPage === 1}
                        className="h-9 w-9 p-0"
                      >
                        <span className="sr-only">Previous page</span>
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                        </svg>
                      </Button>
                      
                      <div className="flex items-center space-x-1">
                        {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                          // Show first page, last page, current page, and pages around current
                          let pageNum;
                          if (totalPages <= 5) {
                            pageNum = i + 1;
                          } else if (currentPage <= 3) {
                            pageNum = i + 1;
                          } else if (currentPage >= totalPages - 2) {
                            pageNum = totalPages - 4 + i;
                          } else {
                            pageNum = currentPage - 2 + i;
                          }
                          
                          return (
                            <Button
                              key={pageNum}
                              variant={currentPage === pageNum ? "default" : "outline"}
                              size="sm"
                              className={`h-9 w-9 p-0 ${currentPage === pageNum ? 'font-bold' : ''}`}
                              onClick={() => setCurrentPage(pageNum)}
                            >
                              {pageNum}
                            </Button>
                          );
                        })}
                        
                        {totalPages > 5 && currentPage < totalPages - 2 && (
                          <span className="px-2 text-sm text-muted-foreground">...</span>
                        )}
                        
                        {totalPages > 5 && currentPage < totalPages - 2 && (
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-9 w-9 p-0"
                            onClick={() => setCurrentPage(totalPages)}
                          >
                            {totalPages}
                          </Button>
                        )}
                      </div>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                        disabled={currentPage === totalPages}
                        className="h-9 w-9 p-0"
                      >
                        <span className="sr-only">Next page</span>
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </Button>
                      
                      <div className="text-sm text-muted-foreground ml-2">
                        Page {currentPage} of {totalPages}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-16 bg-white rounded-xl shadow-sm border border-gray-100">
                  <ChefHat className="mx-auto h-16 w-16 text-gray-300" />
                  <h3 className="mt-4 text-xl font-semibold text-gray-700">No recipes found</h3>
                  <p className="mt-2 text-gray-500 max-w-md mx-auto">
                    {searchTerm
                      ? 'No recipes match your search. Try adjusting your search term.'
                      : 'No recipes available at the moment. Check back later or add your own recipe!'}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Showing pagination info */}
        {filteredRecipes.length > 0 && (
          <div className="text-center text-sm text-muted-foreground mt-4">
            Showing {Math.min(indexOfFirstRecipe + 1, filteredRecipes.length)}-{Math.min(indexOfLastRecipe, filteredRecipes.length)} of {filteredRecipes.length} {filteredRecipes.length === 1 ? 'recipe' : 'recipes'}
          </div>
        )}
      </main>
    </div>
  );
};

export default RecipesPage;
