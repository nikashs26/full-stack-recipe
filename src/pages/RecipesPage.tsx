import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Search, X, Utensils, ChevronLeft, ChevronRight, ChefHat, Leaf, Clock, Star, Heart, FolderPlus, Share2, Filter, Plus, Minus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { RecipeFilters } from '@/components/RecipeFilters';
import RecipeCard from '@/components/RecipeCard';
import { fetchManualRecipes } from '@/lib/manualRecipes';
import { DietaryRestriction, ExtendedRecipe } from '@/types/recipe';
import { useAuth } from '@/context/AuthContext';
import { useToast } from '@/hooks/use-toast';

// Recipe type definitions
type BaseRecipe = {
  id: string | number;
  title: string;
  description?: string;
  image?: string;
  type: 'saved' | 'manual' | 'spoonacular' | 'external';
  created_at?: string;
  updated_at?: string;
};

type ManualRecipe = BaseRecipe & {
  type: 'manual';
  ready_in_minutes?: number;
  cuisine?: string[];
  cuisines?: string[];
  diets?: string[];
  dietaryRestrictions?: string[];
  vegetarian?: boolean;
  vegan?: boolean;
  ingredients?: Array<{ name: string; amount?: string | number; unit?: string }>;
};

type SpoonacularRecipe = BaseRecipe & {
  type: 'spoonacular';
  readyInMinutes?: number;
  servings?: number;
  sourceUrl?: string;
  summary?: string;
  analyzedInstructions?: any[];
  cuisines?: string[];
  cuisine?: string[];
  diets?: string[];
  dietaryRestrictions?: string[];
  vegetarian?: boolean;
  vegan?: boolean;
  extendedIngredients?: Array<{
    id: number;
    name: string;
    original: string;
    amount: number;
    unit: string;
  }>;
};

type ExternalRecipe = BaseRecipe & {
  type: 'external';
  ready_in_minutes?: number;
  servings?: number;
  cuisines?: string[];
  cuisine?: string[];
  diets?: string[];
  dietaryRestrictions?: string[];
  vegetarian?: boolean;
  vegan?: boolean;
  ingredients?: Array<{ name: string; amount?: string | number; unit?: string }>;
};

type Recipe = ManualRecipe | SpoonacularRecipe | ExternalRecipe;

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
  type: 'saved' | 'manual' | 'spoonacular' | 'external';
};

const RecipesPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [ingredientSearch, setIngredientSearch] = useState('');
  const [selectedCuisines, setSelectedCuisines] = useState<string[]>([]);
  const [selectedDiets, setSelectedDiets] = useState<string[]>([]);
  const [showLoading, setShowLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(() => {
    // Try to restore the current page from localStorage
    const savedPage = localStorage.getItem('recipes-current-page');
    return savedPage ? parseInt(savedPage, 10) : 1;
  });
  const [gotoPage, setGotoPage] = useState<string>("");
  const [totalPages, setTotalPages] = useState(1);
  const [recipesPerPage, setRecipesPerPage] = useState(20); // Show 20 recipes per page
  
  // Remove debounced search - we'll only search on explicit action
  // const debouncedSearchQuery = useDebounce(searchQuery, 500);
  
  // Update current page (localStorage is handled by useEffect)
  const updateCurrentPage = useCallback((page: number) => {
    setCurrentPage(page);
  }, []);

  // Fetch paginated recipes from ChromaDB with search and filters
  const { 
    data: recipesData = { recipes: [], total: 0 }, 
    isLoading: isLoadingRecipes, 
    isFetching 
  } = useQuery<{ recipes: Recipe[], total: number }>({
    queryKey: ['recipes', searchQuery, ingredientSearch, selectedCuisines, selectedDiets],
    enabled: true, // Always enable the query to fetch recipes on mount
    queryFn: async () => {
      try {
        console.log('useQuery triggered with:');
        console.log('- searchQuery:', searchQuery);
        console.log('- ingredientSearch:', ingredientSearch);
        console.log('- selectedCuisines:', selectedCuisines);
        console.log('- selectedDiets:', selectedDiets);
        
        // Always use pagination for consistent behavior
        const result = await fetchManualRecipes(searchQuery, ingredientSearch, {
          page: currentPage,
          pageSize: recipesPerPage, // Use configurable page size
          cuisines: selectedCuisines,
          diets: selectedDiets
        });
        
        console.log('Raw result from fetchManualRecipes:', result);
        console.log('Result keys:', Object.keys(result));
        console.log('Result.recipes:', result.recipes);
        console.log('Result.total:', result.total);
        console.log('Selected cuisines being sent to backend:', selectedCuisines);
        console.log('Selected diets being sent to backend:', selectedDiets);
        
        // Update total pages based on the response
        const totalRecipes = result.total || 0;
        const calculatedTotalPages = Math.ceil(totalRecipes / recipesPerPage);
        console.log(`Pagination Debug: total=${totalRecipes}, pageSize=${recipesPerPage}, calculatedTotalPages=${calculatedTotalPages}, currentPage=${currentPage}`);
        setTotalPages(calculatedTotalPages);
        
        return {
          recipes: result.recipes as unknown as Recipe[],
          total: totalRecipes
        };
      } catch (error) {
        console.error('Error fetching recipes:', error);
        throw error;
      }
    },
    staleTime: 5 * 60 * 1000,
    retry: 1,
    refetchOnWindowFocus: false,
  });

  // Handle recipe name search input change - only update local state, don't trigger search
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
    // Don't update searchQuery here - only update it when search is explicitly triggered
    console.log('Search term changed, but not triggering search yet');
  };

  // Handle ingredient search input change - only update local state, don't trigger search
  const handleIngredientSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setIngredientSearch(e.target.value);
    console.log('Ingredient search changed, but not triggering search yet');
  };

  // Handle search button click or Enter key press
  const handleSearchSubmit = () => {
    console.log('Search submitted - before setting searchQuery');
    console.log('searchTerm:', searchTerm);
    console.log('ingredientSearch:', ingredientSearch);
    setSearchQuery(searchTerm);
    updateCurrentPage(1);
    console.log('Search submitted, triggering search');
    console.log('searchQuery will be set to:', searchTerm);
  };

  // Handle Enter key press in search input
  const handleSearchKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSearchSubmit();
    }
  };

  // Handle Enter key press in ingredient input
  const handleIngredientKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSearchSubmit();
    }
  };

  // Toggle cuisine filter and reset to first page
  const toggleCuisine = (cuisine: string) => {
    setSelectedCuisines(prev => 
      prev.includes(cuisine) 
        ? prev.filter(c => c !== cuisine) 
        : [...prev, cuisine]
    );
    updateCurrentPage(1);
  };

  // Toggle diet filter and reset to first page
  const toggleDiet = (diet: string) => {
    setSelectedDiets(prev => 
      prev.includes(diet) 
        ? prev.filter(d => d !== diet) 
        : [...prev, diet]
    );
    updateCurrentPage(1);
  };

  const clearAllFilters = useCallback(() => {
    setSelectedCuisines([]);
    setSelectedDiets([]);
    setSearchQuery("");
    setSearchTerm("");
    setIngredientSearch("");
    // Reset to page 1 when clearing all filters
    updateCurrentPage(1);
  }, [updateCurrentPage]);

  // Normalize recipes to a common format
  const normalizedRecipes = useMemo<NormalizedRecipe[]>(() => {
    if (!Array.isArray(recipesData.recipes)) return [];
    
    return recipesData.recipes.map(recipe => {
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
        ...(recipe.type === 'spoonacular' && 'diets' in recipe ? normalizeList(recipe.diets) : []),
        ...(recipe.vegetarian ? ['vegetarian'] : []),
        ...(recipe.vegan ? ['vegan'] : [])
      ]
        .map(d => d.trim().toLowerCase())
        .filter((value, index, self) => self.indexOf(value) === index && value.length > 0);

      return {
        id: String(recipe.id || Math.random().toString(36).substr(2, 9)),
        title: recipe.title || 'Untitled Recipe',
        description: recipe.description || '',
        imageUrl: recipe.image || (recipe as any).imageUrl || 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?auto=format&fit=crop&w=400&h=300&q=80',
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
            : recipe.type === 'external' && 'ingredients' in recipe && Array.isArray(recipe.ingredients)
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
  }, [recipesData.recipes]);

  // Use normalized recipes directly since filtering is handled by the server
  const filteredRecipes = useMemo(() => {
    if (!Array.isArray(normalizedRecipes)) {
      console.log('No normalized recipes available');
      return [];
    }
    
    console.log('Displaying normalized recipes:', normalizedRecipes.length);
    return normalizedRecipes;
  }, [normalizedRecipes]);

  // Apply frontend pagination to show only recipes for current page
  const displayRecipes = useMemo(() => {
    if (!Array.isArray(filteredRecipes)) {
      console.log('No recipes to display');
      return [];
    }
    
    // Calculate start and end indices for current page
    const startIndex = (currentPage - 1) * recipesPerPage;
    const endIndex = startIndex + recipesPerPage;
    const paginatedRecipes = filteredRecipes.slice(startIndex, endIndex);
    
    console.log('Displaying paginated recipes:', {
      totalRecipes: filteredRecipes.length,
      currentPage,
      totalPages,
      pageSize: recipesPerPage,
      startIndex,
      endIndex,
      paginatedCount: paginatedRecipes.length,
      recipes: paginatedRecipes.map(r => ({
        title: r?.title || 'Untitled',
        image: r?.imageUrl,
        hasImage: !!r?.imageUrl
      }))
    });
    
    return paginatedRecipes;
  }, [filteredRecipes, currentPage, totalPages, recipesPerPage]);

  // Update total pages based on server response
  useEffect(() => {
    try {
      if (recipesData.total !== undefined) {
        const calculatedTotalPages = Math.max(1, Math.ceil(recipesData.total / recipesPerPage));
        
        console.log('Updating total pages from server:', {
          totalItems: recipesData.total,
          pageSize: recipesPerPage,
          calculatedTotalPages,
          currentPage
        });
        
        setTotalPages(calculatedTotalPages);
      }
    } catch (error) {
      console.error('Error updating total pages:', error);
      setTotalPages(1);
    }
  }, [recipesData.total, recipesPerPage]);

  const handleSearch = useCallback((term: string) => {
    setSearchTerm(term);
    setSearchQuery(term);
    updateCurrentPage(1);
  }, [updateCurrentPage]);

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
  
  // Restore current page from localStorage when component mounts
  useEffect(() => {
    const savedPage = localStorage.getItem('recipes-current-page');
    if (savedPage) {
      const page = parseInt(savedPage, 10);
      if (page > 0) {
        console.log('Restoring saved page from localStorage:', page);
        setCurrentPage(page);
      }
    }
  }, []);
  
  // Save current page to localStorage whenever it changes
  useEffect(() => {
    if (currentPage > 0) {
      console.log('Saving current page to localStorage:', currentPage);
      localStorage.setItem('recipes-current-page', currentPage.toString());
    }
  }, [currentPage]);

  const renderRecipeCard = useCallback((recipe: NormalizedRecipe, index: number) => {
    // Helper function to convert string to DietaryRestriction enum
    const convertToDietaryRestriction = (diet: string): DietaryRestriction | null => {
      const normalized = diet.toLowerCase().replace(/[-\s]/g, '');
      switch (normalized) {
        case 'vegetarian':
          return DietaryRestriction.VEGETARIAN;
        case 'vegan':
          return DietaryRestriction.VEGAN;
        case 'glutenfree':
        case 'gluten-free':
          return DietaryRestriction.GLUTEN_FREE;
        case 'dairyfree':
        case 'dairy-free':
          return DietaryRestriction.DAIRY_FREE;
        case 'nutfree':
        case 'nut-free':
          return DietaryRestriction.NUT_FREE;
        case 'keto':
          return DietaryRestriction.KETO;
        case 'paleo':
          return DietaryRestriction.PALEO;
        case 'lowcarb':
        case 'low-carb':
          return DietaryRestriction.LOW_CARB;
        case 'lowcalorie':
        case 'low-calorie':
          return DietaryRestriction.LOW_CALORIE;
        case 'lowsodium':
        case 'low-sodium':
          return DietaryRestriction.LOW_SODIUM;
        case 'highprotein':
        case 'high-protein':
          return DietaryRestriction.HIGH_PROTEIN;
        case 'pescetarian':
          return DietaryRestriction.PESCETARIAN;
        default:
          return null;
      }
    };

    // Debug logging
    console.log('Processing recipe dietary restrictions:', {
      recipeId: recipe.id,
      recipeTitle: recipe.title,
      originalDietaryRestrictions: recipe.dietaryRestrictions,
      convertedDietaryRestrictions: (recipe.dietaryRestrictions || [])
        .map(convertToDietaryRestriction)
        .filter((d): d is DietaryRestriction => d !== null),
      hasTags: (recipe.dietaryRestrictions || []).length > 0
    });

    const convertedRestrictions = (recipe.dietaryRestrictions || [])
      .map(convertToDietaryRestriction)
      .filter((d): d is DietaryRestriction => d !== null);

    console.log('Final dietary restrictions for card:', {
      recipeTitle: recipe.title,
      convertedRestrictions,
      restrictionCount: convertedRestrictions.length
    });

    const recipeForCard: ExtendedRecipe = {
      id: recipe.id.toString(),
      title: recipe.title,
      name: recipe.title,
      image: recipe.imageUrl || 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?auto=format&fit=crop&w=400&h=300&q=80',
      imageUrl: recipe.imageUrl || 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?auto=format&fit=crop&w=400&h=300&q=80',
      cuisines: Array.isArray(recipe.cuisines) ? recipe.cuisines : [],
      dietaryRestrictions: (recipe.dietaryRestrictions || [])
        .map(convertToDietaryRestriction)
        .filter((d): d is DietaryRestriction => d !== null),
      diets: Array.isArray(recipe.dietaryRestrictions) ? recipe.dietaryRestrictions : [],
      ingredients: Array.isArray(recipe.ingredients) ? recipe.ingredients : [],
      instructions: Array.isArray(recipe.instructions) 
        ? recipe.instructions 
        : recipe.instructions 
          ? [recipe.instructions] 
          : ['No instructions available'],
      description: recipe.description || '',
      cookingTime: recipe.ready_in_minutes ? `${recipe.ready_in_minutes} minutes` : 'Not specified',
      servings: recipe.servings || 4,
      source: recipe.type === 'spoonacular' ? 'spoonacular' : recipe.type === 'external' ? 'backend' : 'local',
      type: (recipe.type === 'saved' ? 'manual' : recipe.type) || 'manual',
      ratings: [],
      comments: [],

      ...(recipe.type === 'spoonacular' && { source: 'spoonacular' }),
      ...(recipe.type === 'external' && { source: 'backend' })
    };
    
    return (
      <div key={`${recipe.type}-${recipe.id}-${index}`} className="h-full">
        <RecipeCard 
          recipe={recipeForCard}
          isExternal={recipe.type === 'spoonacular' || recipe.type === 'external'}
          onClick={() => {
            if (recipe.type === 'spoonacular') {
              navigate(`/external-recipe/${recipe.id}`, { 
                state: { source: 'spoonacular' } 
              });
            } else if (recipe.type === 'external') {
              navigate(`/external-recipe/${recipe.id}`, { 
                state: { source: 'backend' } 
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
    <div className="min-h-screen relative">
      {/* Background Image */}
      <div className="fixed inset-0 -z-10 bg-kitchen"></div>
      
      {/* Content Container */}
      <div className="relative z-10">
        {/* Hero Section with Overlay */}
        <div className="relative h-[500px] w-full bg-black/30">
          <div className="absolute inset-0 flex flex-col items-center justify-center px-4">
            <div className="text-center mb-8">
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-4 drop-shadow-lg">Discover Amazing Recipes</h1>
              <p className="text-xl text-gray-100 max-w-2xl mx-auto drop-shadow-md">Find the perfect recipe for any occasion, ingredient, or cuisine</p>
            </div>
            
            {/* Search Container */}
            <div className="w-full max-w-4xl mx-auto">
              <div className="bg-white/90 backdrop-blur rounded-2xl p-6 shadow-xl border border-white/30">
                <div className="space-y-4 mb-2">
                  {/* Recipe Name Search */}
                  <div className="relative">
                    <label htmlFor="recipe-name-search" className="block text-sm font-medium text-gray-100 mb-2 sr-only">
                      Recipe Name Search
                    </label>
                    <Search className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                    {searchTerm && (
                      <button
                        type="button"
                        onClick={() => handleSearchChange({ target: { value: '' } } as any)}
                        aria-label="Clear name search"
                        className="absolute right-28 top-1/2 -translate-y-1/2 p-1 rounded-full text-gray-400 hover:text-gray-600 hover:bg-gray-100"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    )}
                    <Input
                      id="recipe-name-search"
                      type="text"
                      placeholder="Search recipes by name…"
                      className="h-14 pl-12 pr-32 text-base rounded-full border border-gray-200 bg-white placeholder:text-gray-400 focus-visible:ring-4 focus-visible:ring-blue-100 focus-visible:ring-offset-0 focus-visible:border-blue-500 w-full"
                      value={searchTerm}
                      onChange={handleSearchChange}
                      onKeyPress={handleSearchKeyPress}
                    />
                    <Button
                      onClick={handleSearchSubmit}
                      className="absolute right-2 top-1/2 -translate-y-1/2 px-5 h-10 rounded-full bg-gradient-to-r from-primary to-amber-600 hover:from-primary/90 hover:to-amber-600/90 text-white shadow"
                    >
                      <Search className="mr-2 h-4 w-4" />
                      Find
                    </Button>
                  </div>
                  {/* Ingredient Search */}
                  <div className="relative">
                    <label htmlFor="ingredient-search" className="block text-sm font-medium text-gray-100 mb-2 sr-only">
                      Ingredient Search
                    </label>
                    <Utensils className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                    {ingredientSearch && (
                      <button
                        type="button"
                        onClick={() => handleIngredientSearchChange({ target: { value: '' } } as any)}
                        aria-label="Clear ingredient search"
                        className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded-full text-gray-400 hover:text-gray-600 hover:bg-gray-100"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    )}
                    <Input
                      id="ingredient-search"
                      type="text"
                      placeholder="Filter by ingredients…"
                      className="h-14 pl-12 pr-10 text-base rounded-full border border-gray-200 bg-white placeholder:text-gray-400 focus-visible:ring-4 focus-visible:ring-blue-100 focus-visible:ring-offset-0 focus-visible:border-blue-500 w-full"
                      value={ingredientSearch}
                      onChange={handleIngredientSearchChange}
                      onKeyPress={handleIngredientKeyPress}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <main className="container mx-auto px-4 pb-12 relative z-10 -mt-16">
        <div className="bg-white/95 backdrop-blur-sm rounded-3xl shadow-xl px-6 py-8 border border-white/30">
          {/* Main Content Area */}
          <div className="flex flex-col lg:flex-row gap-8">
            {/* Filters - Left Sidebar */}
            <div className="lg:w-80 flex-shrink-0">
              <div className="sticky top-24">
                <div>
                  <div className="flex justify-between items-center mb-4 w-full">
                    <h2 className="text-lg font-semibold">Filters</h2>
                    {(selectedCuisines.length > 0 || selectedDiets.length > 0) && (
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        onClick={clearAllFilters}
                        className="text-sm text-primary hover:text-primary/80"
                      >
                        Clear all
                      </Button>
                    )}
                  </div>
                  <div className="space-y-6">
                    <RecipeFilters
                      searchQuery={searchQuery}
                      ingredientSearch={ingredientSearch}
                      selectedCuisines={selectedCuisines}
                      selectedDiets={selectedDiets}
                      onSearchChange={setSearchQuery}
                      onIngredientSearchChange={setIngredientSearch}
                      onCuisineToggle={toggleCuisine}
                      onDietToggle={toggleDiet}
                      onClearFilters={clearAllFilters}
                    />
                  </div>
                </div>
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
                    {recipesData.total > 0 ? (
                      (() => {
                        const hasSearchOrFilters = searchTerm || ingredientSearch || selectedCuisines.length > 0 || selectedDiets.length > 0;
                        if (hasSearchOrFilters) {
                          // Show pagination info for search results
                          return `Showing ${((currentPage - 1) * recipesPerPage) + 1}-${Math.min(currentPage * recipesPerPage, recipesData.total)} of ${recipesData.total} ${recipesData.total === 1 ? 'recipe' : 'recipes'}`;
                        } else {
                          // Show total count for all recipes
                          return `Showing all ${recipesData.total} ${recipesData.total === 1 ? 'recipe' : 'recipes'}`;
                        }
                      })()
                    ) : 'No recipes found'}
                  </p>
                </div>

                {isLoadingRecipes ? (
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
                      {displayRecipes.map((recipe, index) => renderRecipeCard(recipe, index))}
                    </div>
                  </>
                ) : (
                  <div className="text-center py-16 bg-white rounded-xl shadow-sm border border-gray-100">
                    <ChefHat className="mx-auto h-16 w-16 text-gray-300" />
                    <h3 className="mt-4 text-xl font-semibold text-gray-700">No recipes found</h3>
                    <p className="mt-2 text-gray-500 max-w-md mx-auto">
                      {searchTerm || ingredientSearch || selectedCuisines.length > 0 || selectedDiets.length > 0
                        ? 'No recipes match your search criteria. Try adjusting your filters.'
                        : 'No recipes available at the moment. Check back later or add your own recipe!'}
                    </p>
                    {(searchTerm || ingredientSearch || selectedCuisines.length > 0 || selectedDiets.length > 0) && (
                      <Button 
                        onClick={clearAllFilters}
                        className="mt-4"
                        variant="outline"
                      >
                        Clear all filters
                      </Button>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

                    {/* Page Size Selector and Pagination Controls */}
          <div className="flex flex-col items-center border-t border-gray-200 bg-white px-4 py-3 sm:px-6">
            {/* Page Size Selector */}
            <div className="mb-3 flex items-center gap-2">
              <label htmlFor="pageSize" className="text-sm text-gray-700">
                Show:
              </label>
              <select
                id="pageSize"
                value={recipesPerPage}
                onChange={(e) => {
                  const newPageSize = parseInt(e.target.value);
                  setRecipesPerPage(newPageSize);
                  updateCurrentPage(1); // Reset to first page when changing page size
                }}
                className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={20}>20</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
                <option value={200}>200</option>
              </select>
              <span className="text-sm text-gray-700">recipes per page</span>
            </div>
            
            {/* Pagination Controls - Only show if there are multiple pages */}
            {totalPages > 1 && (
              <>
                {/* Results Info */}
                <div className="mb-3 text-center">
                  <p className="text-sm text-gray-700">
                    Showing{' '}
                    <span className="font-medium">{((currentPage - 1) * recipesPerPage) + 1}</span>
                    {' '}to{' '}
                    <span className="font-medium">
                      {Math.min(currentPage * recipesPerPage, recipesData.total)}
                    </span>
                    {' '}of{' '}
                    <span className="font-medium">{recipesData.total}</span>
                    {' '}results
                  </p>
                </div>
                
                {/* Mobile Pagination */}
                <div className="flex flex-1 justify-between sm:hidden">
                  <Button
                    onClick={() => {
                      console.log('Previous button clicked, current page:', currentPage);
                      updateCurrentPage(Math.max(1, currentPage - 1));
                    }}
                    disabled={currentPage === 1 || isLoadingRecipes}
                    variant="outline"
                    size="sm"
                  >
                    Previous
                  </Button>
                  <Button
                    onClick={() => {
                      console.log('Next button clicked, current page:', currentPage);
                      updateCurrentPage(Math.min(totalPages, currentPage + 1));
                    }}
                    disabled={currentPage === totalPages || isLoadingRecipes}
                    variant="outline"
                    size="sm"
                  >
                    Next
                  </Button>
                </div>
                
                {/* Desktop Pagination - Centered */}
                <div className="hidden sm:flex sm:items-center sm:justify-center">
                  <div className="flex items-center gap-2">
                    {/* Previous Arrow */}
                    <Button
                      onClick={() => {
                        console.log('Previous button clicked, current page:', currentPage);
                        updateCurrentPage(Math.max(1, currentPage - 1));
                      }}
                      disabled={currentPage === 1 || isLoadingRecipes}
                      variant="outline"
                      size="sm"
                      className="px-3"
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    
                    {/* Page Numbers */}
                    <div className="flex items-center gap-1">
                      {(() => {
                        const items: (number | 'ellipsis')[] = [];
                        const showAllThreshold = 9;
                        if (totalPages <= showAllThreshold) {
                          for (let p = 1; p <= totalPages; p++) items.push(p);
                        } else {
                          // Always show first two
                          items.push(1);
                          if (totalPages >= 2) items.push(2);
                          // Ellipsis before middle window
                          if (currentPage > 4) items.push('ellipsis');
                          // Middle window around current page
                          const start = Math.max(3, Math.min(currentPage - 1, totalPages - 4));
                          const end = Math.min(totalPages - 2, Math.max(currentPage + 1, 5));
                          for (let p = start; p <= end; p++) {
                            if (!items.includes(p)) items.push(p);
                          }
                          // Ellipsis after middle window
                          if (currentPage < totalPages - 3) items.push('ellipsis');
                          // Always show last two
                          if (!items.includes(totalPages - 1)) items.push(totalPages - 1);
                          if (!items.includes(totalPages)) items.push(totalPages);
                        }

                        return (
                          <>
                            {items.map((it, idx) => {
                              if (it === 'ellipsis') {
                                return (
                                  <Button key={`e-${idx}`} variant="outline" size="sm" disabled className="min-w-[40px]">
                                    ...
                                  </Button>
                                );
                              }
                              const pageNum = it as number;
                              return (
                                <Button
                                  key={pageNum}
                                  variant={currentPage === pageNum ? "default" : "outline"}
                                  size="sm"
                                  onClick={() => {
                                    if (currentPage !== pageNum) {
                                      console.log(`Page ${pageNum} clicked, current page:`, currentPage);
                                      updateCurrentPage(pageNum);
                                    }
                                  }}
                                  disabled={isLoadingRecipes}
                                  className={`min-w-[40px] ${currentPage === pageNum ? 'font-bold' : ''}`}
                                  aria-label={`Go to page ${pageNum}`}
                                >
                                  {pageNum}
                                </Button>
                              );
                            })}
                          </>
                        );
                      })()}
                    </div>
                    
                    {/* Go To Page */}
                    <div className="flex items-center gap-1 ml-2">
                      <Input
                        value={gotoPage}
                        onChange={(e) => setGotoPage(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            const n = parseInt(gotoPage || '');
                            if (!isNaN(n)) {
                              const clamped = Math.max(1, Math.min(totalPages, n));
                              updateCurrentPage(clamped);
                            }
                          }
                        }}
                        placeholder="Go to"
                        className="px-2 py-1"
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          const n = parseInt(gotoPage || '');
                          if (!isNaN(n)) {
                            const clamped = Math.max(1, Math.min(totalPages, n));
                            updateCurrentPage(clamped);
                          }
                        }}
                      >
                        Go
                      </Button>
                    </div>
                    
                    {/* Next Arrow */}
                    <Button
                      onClick={() => {
                        console.log('Next button clicked, current page:', currentPage);
                        updateCurrentPage(Math.min(totalPages, currentPage + 1));
                      }}
                      disabled={currentPage === totalPages || isLoadingRecipes}
                      variant="outline"
                      size="sm"
                      className="px-3"
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default RecipesPage;