import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchManualRecipes } from '../lib/manualRecipes';
import { DietaryRestriction, Recipe as RecipeType } from '../types/recipe';
import { Loader2, Search, Filter, X, ChefHat, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, Utensils } from 'lucide-react';
import Header from '../components/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import RecipeCard from '@/components/RecipeCard';
import { Input } from '@/components/ui/input';
import { RecipeFilters } from '@/components/RecipeFilters';
import { useDebounce } from '../hooks/useDebounce';
import { useMediaQuery } from '../hooks/use-media-query';
import { Drawer, DrawerContent, DrawerTrigger } from '@/components/ui/drawer';

// Recipe type definitions
type BaseRecipe = {
  id: string | number;
  title: string;
  description?: string;
  image?: string;
  type: 'saved' | 'manual' | 'spoonacular';
  created_at?: string;
  updated_at?: string;
};

type ManualRecipe = BaseRecipe & {
  type: 'manual';
  ready_in_minutes?: number;
  cuisine?: string[];
  diets?: string[];
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
  diets?: string[];
  extendedIngredients?: Array<{
    id: number;
    name: string;
    original: string;
    amount: number;
    unit: string;
  }>;
};

type Recipe = ManualRecipe | SpoonacularRecipe;

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
  const [searchTerm, setSearchTerm] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [ingredientSearch, setIngredientSearch] = useState('');
  const [selectedCuisines, setSelectedCuisines] = useState<string[]>([]);
  const [selectedDiets, setSelectedDiets] = useState<string[]>([]);
  const [showMobileFilters, setShowMobileFilters] = useState(false);
  const [showLoading, setShowLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const recipesPerPage = 20;
  
  const isDesktop = useMediaQuery("(min-width: 1024px)");
  const debouncedSearchQuery = useDebounce(searchQuery, 500);

  // Fetch paginated recipes from ChromaDB with search and filters
  const { 
    data: recipesData = { recipes: [], total: 0 }, 
    isLoading: isLoadingRecipes, 
    isFetching 
  } = useQuery<{ recipes: Recipe[], total: number }>({
    queryKey: ['recipes', debouncedSearchQuery, ingredientSearch, selectedCuisines, selectedDiets, currentPage],
    queryFn: async () => {
      try {
        const result = await fetchManualRecipes(debouncedSearchQuery, ingredientSearch, {
          page: currentPage,
          pageSize: recipesPerPage,
          cuisines: selectedCuisines,
          diets: selectedDiets
        });
        
        // Update total pages based on the response
        const totalRecipes = result.total || 0;
        setTotalPages(Math.ceil(totalRecipes / recipesPerPage));
        
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

  // Handle recipe name search input change with debounce and reset to first page
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
    setSearchQuery(e.target.value);
    setCurrentPage(1);
  };

  // Handle ingredient search input change
  const handleIngredientSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setIngredientSearch(e.target.value);
    setCurrentPage(1);
  };

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
        // Add vegetarian/vegan flags if present in the recipe
        ...(recipe.vegetarian ? ['vegetarian'] : []),
        ...(recipe.vegan ? ['vegan'] : [])
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

  // Server handles pagination, so we just use the recipes as-is
  const displayRecipes = useMemo(() => {
    if (!Array.isArray(filteredRecipes)) {
      console.log('No recipes to display');
      return [];
    }
    
    console.log('Displaying recipes:', {
      count: filteredRecipes.length,
      currentPage,
      totalPages,
      recipes: filteredRecipes.map(r => r?.title || 'Untitled')
    });
    
    return filteredRecipes;
  }, [filteredRecipes, currentPage, totalPages]);

  // Update total pages based on server response
  useEffect(() => {
    try {
      if (recipesData.total !== undefined) {
        const calculatedTotalPages = Math.max(1, Math.ceil(recipesData.total / recipesPerPage));
        
        console.log('Updating total pages from server:', {
          totalItems: recipesData.total,
          recipesPerPage,
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
    setCurrentPage(1);
  }, []);

  // Toggle cuisine filter and reset to first page
  const toggleCuisine = (cuisine: string) => {
    setSelectedCuisines(prev => 
      prev.includes(cuisine) 
        ? prev.filter(c => c !== cuisine) 
        : [...prev, cuisine]
    );
    setCurrentPage(1);
  };

  // Toggle diet filter and reset to first page
  const toggleDiet = (diet: string) => {
    setSelectedDiets(prev => 
      prev.includes(diet) 
        ? prev.filter(d => d !== diet) 
        : [...prev, diet]
    );
    setCurrentPage(1);
  };

  const clearAllFilters = useCallback(() => {
    setSelectedCuisines([]);
    setSelectedDiets([]);
    setSearchQuery("");
    setSearchTerm("");
    setIngredientSearch("");
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
        searchQuery={searchQuery}
        selectedCuisines={selectedCuisines}
        selectedDiets={selectedDiets}
        onSearchChange={setSearchQuery}
        onCuisineToggle={toggleCuisine}
        onDietToggle={toggleDiet}
        onClearFilters={clearAllFilters}
      />
    </div>
  ), [searchQuery, selectedCuisines, selectedDiets, toggleCuisine, toggleDiet, clearAllFilters]);

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
    const recipeForCard: RecipeType = {
      id: recipe.id.toString(),
      title: recipe.title,
      name: recipe.title,
      image: recipe.imageUrl || '/placeholder-recipe.jpg',
      imageUrl: recipe.imageUrl || '/placeholder-recipe.jpg',
      cuisines: Array.isArray(recipe.cuisines) ? recipe.cuisines : [],
      cuisine: Array.isArray(recipe.cuisines) && recipe.cuisines.length > 0 ? recipe.cuisines[0] : '',
      dietaryRestrictions: (recipe.dietaryRestrictions || []).filter((d): d is DietaryRestriction => 
        ['vegetarian', 'vegan', 'gluten-free', 'dairy-free', 'keto', 'paleo'].includes(d)
      ),
      diets: (recipe.dietaryRestrictions || []).filter(d => 
        ['vegetarian', 'vegan', 'gluten-free', 'dairy-free', 'keto', 'paleo'].includes(d)
      ),
      ingredients: Array.isArray(recipe.ingredients) ? recipe.ingredients : [],
      instructions: Array.isArray(recipe.instructions) 
        ? recipe.instructions 
        : recipe.instructions 
          ? [recipe.instructions] 
          : ['No instructions available'],
      description: recipe.description || '',
      cookingTime: recipe.ready_in_minutes ? `${recipe.ready_in_minutes} minutes` : 'Not specified',
      servings: recipe.servings || 4,
      source: recipe.type === 'spoonacular' ? 'spoonacular' : 'local',
      type: recipe.type || 'saved',
      ratings: [],
      comments: [],

      ...(recipe.type === 'spoonacular' && { source: 'spoonacular' })
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
    <div className="min-h-screen relative">
      {/* Background Image */}
      <div className="fixed inset-0 -z-10 bg-kitchen"></div>
      
      {/* Content Container */}
      <div className="relative z-10">
        {/* Hero Section with Overlay */}
        <div className="relative h-[500px] w-full bg-black/20">
          <div className="absolute inset-0 flex flex-col items-center justify-center px-4">
            <div className="text-center mb-8">
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-4">Discover Amazing Recipes</h1>
              <p className="text-xl text-gray-100 max-w-2xl mx-auto">Find the perfect recipe for any occasion, ingredient, or cuisine</p>
            </div>
            
            {/* Search Container */}
            <div className="w-full max-w-4xl mx-auto">
              <div className="bg-white/90 backdrop-blur-sm rounded-2xl p-6 shadow-xl border border-white/20">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                    <Input
                      type="text"
                      placeholder="Search recipes by name..."
                      className="pl-10 pr-4 py-6 text-base rounded-xl shadow-sm focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 w-full border-0 bg-white/90 hover:bg-white transition-colors duration-200"
                      value={searchTerm}
                      onChange={handleSearchChange}
                    />
                  </div>
                  <div className="relative">
                    <Utensils className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                    <Input
                      type="text"
                      placeholder="Filter by ingredients..."
                      className="pl-10 pr-4 py-6 text-base rounded-xl shadow-sm focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 w-full border-0 bg-white/90 hover:bg-white transition-colors duration-200"
                      value={ingredientSearch}
                      onChange={handleIngredientSearchChange}
                    />
                  </div>
                </div>
                <div className="flex justify-center">
                  <Button 
                    onClick={() => handleSearchChange({ target: { value: searchTerm } } as React.ChangeEvent<HTMLInputElement>) }
                    className="px-8 py-6 text-lg font-medium rounded-xl bg-gradient-to-r from-primary to-amber-600 hover:from-primary/90 hover:to-amber-600/90 text-white shadow-lg hover:shadow-xl transition-all duration-200 w-full md:w-auto"
                  >
                    <Search className="mr-2 h-5 w-5" />
                    Find Recipes
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <main className="container mx-auto px-4 pb-12 relative z-10 -mt-16">
        <div className="bg-white rounded-3xl shadow-xl px-6 py-8">
          {/* Main Content Area */}
          <div className="flex flex-col lg:flex-row gap-8">
            {/* Filters - Left Sidebar */}
            <div className="lg:w-80 flex-shrink-0">
              <div className="sticky top-24">
                {isDesktop ? (
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
                    {renderFilters()}
                  </div>
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
                    {filteredRecipes && filteredRecipes.length > 0 ? (
                      `Showing ${((currentPage - 1) * recipesPerPage) + 1}-${Math.min(currentPage * recipesPerPage, filteredRecipes.length)} of ${filteredRecipes.length} ${filteredRecipes.length === 1 ? 'recipe' : 'recipes'}`
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
                      {searchTerm || selectedCuisines.length > 0 || selectedDiets.length > 0
                        ? 'No recipes match your search criteria. Try adjusting your filters.'
                        : 'No recipes available at the moment. Check back later or add your own recipe!'}
                    </p>
                    {(searchTerm || selectedCuisines.length > 0 || selectedDiets.length > 0) && (
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

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-8">
              <div className="text-sm text-gray-500 dark:text-gray-400">
                Page {currentPage} of {totalPages}
              </div>
              
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => currentPage !== 1 && setCurrentPage(1)}
                  disabled={currentPage === 1 || isLoadingRecipes}
                >
                  <ChevronsLeft className="h-4 w-4 mr-1" />
                  First
                </Button>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    if (currentPage > 1) {
                      setCurrentPage(prev => Math.max(1, prev - 1));
                    }
                  }}
                  disabled={currentPage === 1 || isLoadingRecipes}
                >
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Previous
                </Button>
                
                <div className="flex items-center gap-1">
                  {(() => {
                    // Calculate which page numbers to show (up to 5 at a time)
                    const maxVisiblePages = 5;
                    const half = Math.floor(maxVisiblePages / 2);
                    let startPage = Math.max(1, currentPage - half);
                    const endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
                    
                    // Adjust startPage if we're near the end
                    if (endPage - startPage + 1 < maxVisiblePages) {
                      startPage = Math.max(1, endPage - maxVisiblePages + 1);
                    }
                    
                    return (
                      <>
                        {Array.from(
                          { length: Math.min(maxVisiblePages, totalPages) },
                          (_, i) => {
                            const pageNum = startPage + i;
                            return (
                              <Button
                                key={pageNum}
                                variant={currentPage === pageNum ? "default" : "outline"}
                                size="sm"
                                onClick={() => {
                                  if (currentPage !== pageNum) {
                                    setCurrentPage(pageNum);
                                  }
                                }}
                                disabled={isLoadingRecipes}
                                className={`min-w-[40px] ${currentPage === pageNum ? 'font-bold' : ''}`}
                                aria-label={`Go to page ${pageNum}`}
                              >
                                {pageNum}
                              </Button>
                            );
                          }
                        )}
                      </>
                    );
                  })()}
                </div>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    if (currentPage < totalPages) {
                      setCurrentPage(prev => Math.min(totalPages, prev + 1));
                    }
                  }}
                  disabled={currentPage === totalPages || isLoadingRecipes}
                  aria-label="Next page"
                >
                  Next
                  <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    if (currentPage !== totalPages) {
                      setCurrentPage(totalPages);
                    }
                  }}
                  disabled={currentPage === totalPages || isLoadingRecipes}
                  aria-label="Last page"
                >
                  Last
                  <ChevronsRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
              
              <div className="text-sm text-gray-500 dark:text-gray-400">
                {recipesData.total} {recipesData.total === 1 ? 'recipe' : 'recipes'} total
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default RecipesPage;
