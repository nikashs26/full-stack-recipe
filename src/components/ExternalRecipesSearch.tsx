
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchRecipes } from '../lib/spoonacular';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Loader2, Search } from 'lucide-react';
import { useToast } from "@/hooks/use-toast";
import { SpoonacularRecipe } from '../types/spoonacular';

const ExternalRecipesSearch: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeQuery, setActiveQuery] = useState('');
  const { toast } = useToast();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['recipes', activeQuery],
    queryFn: () => fetchRecipes(activeQuery),
    enabled: !!activeQuery,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      setActiveQuery(searchQuery.trim());
    }
  };

  if (isError && activeQuery) {
    toast({
      title: "Error",
      description: `Failed to fetch recipes: ${(error as Error).message}`,
      variant: "destructive",
    });
  }

  return (
    <div className="mt-12 animate-fade-in">
      <Card>
        <CardHeader>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Search External Recipes</h2>
          <p className="text-gray-600">Find more recipes from our database</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="mb-6">
            <div className="flex gap-2">
              <div className="relative flex-grow">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-5 w-5 text-gray-400" aria-hidden="true" />
                </div>
                <Input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search for recipes..."
                  className="pl-10"
                />
              </div>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Searching...
                  </>
                ) : (
                  'Search'
                )}
              </Button>
            </div>
          </form>
          
          {isLoading ? (
            <div className="flex justify-center items-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : data?.results && data.results.length > 0 ? (
            <div>
              <h3 className="text-lg font-semibold mb-4">Search Results</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {data.results.map((recipe: SpoonacularRecipe) => (
                  <Card key={recipe.id} className="h-full flex flex-col">
                    <div className="relative h-40 w-full overflow-hidden">
                      <img 
                        src={recipe.image} 
                        alt={recipe.title} 
                        className="absolute inset-0 h-full w-full object-cover transition-transform duration-500 hover:scale-110"
                      />
                    </div>
                    <CardContent className="flex-grow p-4">
                      <h4 className="text-lg font-semibold text-gray-800 line-clamp-2">
                        {recipe.title}
                      </h4>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ) : activeQuery ? (
            <div className="text-center py-8">
              <h3 className="text-lg font-medium text-gray-600">No recipes found</h3>
              <p className="text-gray-500 mt-2">Try a different search term</p>
            </div>
          ) : (
            <div className="text-center py-8">
              <h3 className="text-lg font-medium text-gray-600">Search for recipes</h3>
              <p className="text-gray-500 mt-2">Enter a search term to find more recipes</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ExternalRecipesSearch;
