import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Search, Filter, SlidersHorizontal, Grid, List, Clock, Star } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { RecipeFilters } from '@/components/RecipeFilters';
import Header from '@/components/Header';
import { Recipe } from '@/types/recipe';
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";

interface SearchResults {
  recipes: Recipe[];
  totalCount: number;
  currentPage: number;
  totalPages: number;
}

const RECIPES_PER_PAGE = 20;

// Simple Recipe Card component for search page
const SimpleRecipeCard = ({ recipe, onClick }: { recipe: Recipe; onClick: () => void }) => {
  const getImageUrl = () => {
    if (recipe.image) return recipe.image;
    if ('imageUrl' in recipe && recipe.imageUrl) return recipe.imageUrl;
    return '/placeholder.svg';
  };

  const getTitle = () => {
    if (recipe.title) return recipe.title;
    if ('name' in recipe && recipe.name) return recipe.name;
    return 'Untitled Recipe';
  };

  const getCookTime = () => {
    if ('ready_in_minutes' in recipe && recipe.ready_in_minutes) return recipe.ready_in_minutes;
    if ('readyInMinutes' in recipe && recipe.readyInMinutes) return recipe.readyInMinutes;
    return null;
  };

  const getCuisines = () => {
    if ('cuisine' in recipe && Array.isArray(recipe.cuisine)) return recipe.cuisine;
    if ('cuisines' in recipe && Array.isArray(recipe.cuisines)) return recipe.cuisines;
    if ('cuisine' in recipe && typeof recipe.cuisine === 'string') return [recipe.cuisine];
    return [];
  };

  return (
    <div 
      className="bg-white rounded-lg shadow-sm border overflow-hidden hover:shadow-md transition-shadow duration-200 cursor-pointer"
      onClick={onClick}
    >
      <div className="relative h-48">
        <img
          src={getImageUrl()}
          alt={getTitle()}
          className="w-full h-full object-cover"
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.src = '/placeholder.svg';
          }}
        />
      </div>
      
      <div className="p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
          {getTitle()}
        </h3>
        
        <div className="flex items-center justify-between text-sm text-gray-500 mb-3">
          {getCookTime() && (
            <div className="flex items-center">
              <Clock className="w-4 h-4 mr-1" />
              <span>{getCookTime()} min</span>
            </div>
          )}
          <div className="flex items-center">
            <Star className="w-4 h-4 mr-1 text-yellow-400" />
            <span>4.5</span>
          </div>
        </div>
        
        <div className="flex flex-wrap gap-1">
          {getCuisines().slice(0, 2).map((cuisine, index) => (
            <span
              key={index}
              className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full"
            >
              {cuisine}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

const SearchPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  
  // Search and filter state
  const [searchQuery, setSearchQuery] = useState(searchParams.get('q') || '');
  const [selectedCuisines, setSelectedCuisines] = useState<string[]>([]);
  const [selectedDiets, setSelectedDiets] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState('relevance');
  const [currentPage, setCurrentPage] = useState(1);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showFilters, setShowFilters] = useState(false);
  
  // Data state
  const [searchResults, setSearchResults] = useState<SearchResults>({
    recipes: [],
    totalCount: 0,
    currentPage: 1,
    totalPages: 0
  });
  const [isLoading, setIsLoading] = useState(false);

  // Mock search function for development
  const searchRecipes = async (page: number = 1) => {
    setIsLoading(true);
    try {
      // Mock data for development
      const mockRecipes: Recipe[] = [
        {
          id: '1',
          title: 'Spaghetti Carbonara',
          image: '/placeholder.svg',
          ready_in_minutes: 30,
          cuisine: ['Italian'],
          diets: [],
          ingredients: [],
          instructions: '',
          ratings: []
        },
        {
          id: '2', 
          title: 'Chicken Tikka Masala',
          image: '/placeholder.svg',
          ready_in_minutes: 45,
          cuisine: ['Indian'],
          diets: [],
          ingredients: [],
          instructions: '',
          ratings: []
        }
      ];

      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 500));

      const filteredRecipes = mockRecipes.filter(recipe => {
        if (searchQuery && !recipe.title.toLowerCase().includes(searchQuery.toLowerCase())) {
          return false;
        }
        if (selectedCuisines.length > 0 && !selectedCuisines.some(c => recipe.cuisine?.includes(c))) {
          return false;
        }
        return true;
      });

      setSearchResults({
        recipes: filteredRecipes,
        totalCount: filteredRecipes.length,
        currentPage: page,
        totalPages: Math.ceil(filteredRecipes.length / RECIPES_PER_PAGE)
      });
      setCurrentPage(page);
      
      // Update URL params
      const newParams = new URLSearchParams();
      if (searchQuery.trim()) newParams.set('q', searchQuery);
      if (page > 1) newParams.set('page', page.toString());
      setSearchParams(newParams);
    } catch (error) {
      console.error('Error searching recipes:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle search submission
  const handleSearch = (e?: React.FormEvent) => {
    e?.preventDefault();
    setCurrentPage(1);
    searchRecipes(1);
  };

  // Handle filter changes
  const handleCuisineToggle = (cuisine: string) => {
    setSelectedCuisines(prev => 
      prev.includes(cuisine) 
        ? prev.filter(c => c !== cuisine)
        : [...prev, cuisine]
    );
    setCurrentPage(1);
  };

  const handleDietToggle = (diet: string) => {
    setSelectedDiets(prev => 
      prev.includes(diet) 
        ? prev.filter(d => d !== diet)
        : [...prev, diet]
    );
    setCurrentPage(1);
  };

  const handleClearFilters = () => {
    setSelectedCuisines([]);
    setSelectedDiets([]);
    setCurrentPage(1);
  };

  // Handle pagination
  const handlePageChange = (page: number) => {
    searchRecipes(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleRecipeClick = (recipe: Recipe) => {
    navigate(`/recipe/${recipe.id}`, { state: { recipe } });
  };

  // Trigger search when filters change
  useEffect(() => {
    if (selectedCuisines.length > 0 || selectedDiets.length > 0 || searchQuery) {
      const timer = setTimeout(() => {
        searchRecipes(currentPage);
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [selectedCuisines, selectedDiets, sortBy]);

  // Initial search from URL params
  useEffect(() => {
    const query = searchParams.get('q');
    const page = parseInt(searchParams.get('page') || '1');
    if (query) {
      setSearchQuery(query);
      setCurrentPage(page);
      searchRecipes(page);
    }
  }, []);

  const renderPaginationItems = () => {
    const items = [];
    const { currentPage, totalPages } = searchResults;
    
    // Always show first page
    if (totalPages > 0) {
      items.push(
        <PaginationItem key={1}>
          <PaginationLink
            onClick={() => handlePageChange(1)}
            isActive={currentPage === 1}
            className="cursor-pointer"
          >
            1
          </PaginationLink>
        </PaginationItem>
      );
    }

    // Show ellipsis if needed
    if (currentPage > 3) {
      items.push(<PaginationEllipsis key="start-ellipsis" />);
    }

    // Show pages around current page
    for (let i = Math.max(2, currentPage - 1); i <= Math.min(totalPages - 1, currentPage + 1); i++) {
      items.push(
        <PaginationItem key={i}>
          <PaginationLink
            onClick={() => handlePageChange(i)}
            isActive={currentPage === i}
            className="cursor-pointer"
          >
            {i}
          </PaginationLink>
        </PaginationItem>
      );
    }

    // Show ellipsis if needed
    if (currentPage < totalPages - 2) {
      items.push(<PaginationEllipsis key="end-ellipsis" />);
    }

    // Always show last page if more than 1 page
    if (totalPages > 1) {
      items.push(
        <PaginationItem key={totalPages}>
          <PaginationLink
            onClick={() => handlePageChange(totalPages)}
            isActive={currentPage === totalPages}
            className="cursor-pointer"
          >
            {totalPages}
          </PaginationLink>
        </PaginationItem>
      );
    }

    return items;
  };

  const activeFiltersCount = selectedCuisines.length + selectedDiets.length;

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <div className="container mx-auto px-4 py-6">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Sidebar Filters */}
          <div className={`lg:w-80 ${showFilters ? 'block' : 'hidden lg:block'}`}>
            <Card className="sticky top-6">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold">Filters</h2>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowFilters(false)}
                    className="lg:hidden"
                  >
                    ×
                  </Button>
                </div>
                
                <RecipeFilters
                  searchQuery={searchQuery}
                  selectedCuisines={selectedCuisines}
                  selectedDiets={selectedDiets}
                  onSearchChange={setSearchQuery}
                  onCuisineToggle={handleCuisineToggle}
                  onDietToggle={handleDietToggle}
                  onClearFilters={handleClearFilters}
                />
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <div className="flex-1">
            {/* Search Header */}
            <div className="mb-6">
              <form onSubmit={handleSearch} className="mb-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                  <Input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search recipes..."
                    className="pl-10 h-12 text-base"
                  />
                </div>
              </form>

              {/* Controls Bar */}
              <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowFilters(true)}
                    className="lg:hidden"
                  >
                    <SlidersHorizontal className="w-4 h-4 mr-2" />
                    Filters
                    {activeFiltersCount > 0 && (
                      <Badge variant="secondary" className="ml-2 h-5 w-5 rounded-full p-0 text-xs">
                        {activeFiltersCount}
                      </Badge>
                    )}
                  </Button>
                  
                  {searchResults.totalCount > 0 && (
                    <p className="text-sm text-muted-foreground">
                      {searchResults.totalCount} recipes found
                    </p>
                  )}
                </div>

                <div className="flex items-center gap-4">
                  {/* Sort Selection */}
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">Sort by:</span>
                    <Select value={sortBy} onValueChange={setSortBy}>
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="relevance">Relevance</SelectItem>
                        <SelectItem value="rating">Rating</SelectItem>
                        <SelectItem value="time">Cooking Time</SelectItem>
                        <SelectItem value="newest">Newest</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <Separator orientation="vertical" className="h-6" />

                  {/* View Mode Toggle */}
                  <div className="flex border rounded-md">
                    <Button
                      variant={viewMode === 'grid' ? 'default' : 'ghost'}
                      size="sm"
                      onClick={() => setViewMode('grid')}
                      className="rounded-r-none"
                    >
                      <Grid className="w-4 h-4" />
                    </Button>
                    <Button
                      variant={viewMode === 'list' ? 'default' : 'ghost'}
                      size="sm"
                      onClick={() => setViewMode('list')}
                      className="rounded-l-none"
                    >
                      <List className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </div>

            {/* Active Filters */}
            {activeFiltersCount > 0 && (
              <div className="mb-6">
                <div className="flex flex-wrap gap-2 items-center">
                  <span className="text-sm text-muted-foreground">Active filters:</span>
                  {selectedCuisines.map(cuisine => (
                    <Badge key={cuisine} variant="secondary" className="gap-1">
                      {cuisine}
                      <button
                        onClick={() => handleCuisineToggle(cuisine)}
                        className="ml-1 hover:bg-muted-foreground/20 rounded-full"
                      >
                        ×
                      </button>
                    </Badge>
                  ))}
                  {selectedDiets.map(diet => (
                    <Badge key={diet} variant="secondary" className="gap-1">
                      {diet}
                      <button
                        onClick={() => handleDietToggle(diet)}
                        className="ml-1 hover:bg-muted-foreground/20 rounded-full"
                      >
                        ×
                      </button>
                    </Badge>
                  ))}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleClearFilters}
                    className="h-6 px-2 text-xs"
                  >
                    Clear all
                  </Button>
                </div>
              </div>
            )}

            {/* Loading State */}
            {isLoading && (
              <div className="flex justify-center items-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-2 border-primary border-t-transparent"></div>
              </div>
            )}

            {/* Results */}
            {!isLoading && searchResults.recipes.length > 0 && (
              <>
                <div className={
                  viewMode === 'grid' 
                    ? "grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6" 
                    : "space-y-4"
                }>
                  {searchResults.recipes.map((recipe) => (
                    <SimpleRecipeCard
                      key={recipe.id}
                      recipe={recipe}
                      onClick={() => handleRecipeClick(recipe)}
                    />
                  ))}
                </div>

                {/* Pagination */}
                {searchResults.totalPages > 1 && (
                  <div className="mt-8 flex justify-center">
                    <Pagination>
                      <PaginationContent>
                        {searchResults.currentPage > 1 && (
                          <PaginationPrevious
                            onClick={() => handlePageChange(searchResults.currentPage - 1)}
                            className="cursor-pointer"
                          />
                        )}
                        {renderPaginationItems()}
                        {searchResults.currentPage < searchResults.totalPages && (
                          <PaginationNext
                            onClick={() => handlePageChange(searchResults.currentPage + 1)}
                            className="cursor-pointer"
                          />
                        )}
                      </PaginationContent>
                    </Pagination>
                  </div>
                )}
              </>
            )}

            {/* No Results */}
            {!isLoading && searchResults.recipes.length === 0 && searchQuery && (
              <div className="text-center py-12">
                <Search className="mx-auto h-12 w-12 text-muted-foreground/50" />
                <h3 className="mt-4 text-lg font-medium">No recipes found</h3>
                <p className="mt-2 text-muted-foreground">
                  Try adjusting your search terms or filters
                </p>
                <Button
                  variant="outline"
                  onClick={handleClearFilters}
                  className="mt-4"
                >
                  Clear all filters
                </Button>
              </div>
            )}

            {/* Initial State */}
            {!isLoading && !searchQuery && searchResults.recipes.length === 0 && (
              <div className="text-center py-12">
                <Search className="mx-auto h-12 w-12 text-muted-foreground/50" />
                <h3 className="mt-4 text-lg font-medium">Search for recipes</h3>
                <p className="mt-2 text-muted-foreground">
                  Enter a search term to find delicious recipes
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SearchPage;