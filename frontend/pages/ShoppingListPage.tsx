
import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '@/hooks/use-toast';
import Header from '../components/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ShoppingCart, Trash2, Check, Loader2, Lock } from 'lucide-react';
import { Checkbox } from '@/components/ui/checkbox';
import { ShoppingListItem, Recipe } from '../types/recipe'; // Keep Recipe for now if needed elsewhere
import { useQuery, useQueryClient } from '@tanstack/react-query'; // Keep if you still need other queries
import { loadRecipes } from '../utils/storage'; // Keep if you still need to load recipes
import { v4 as uuidv4 } from 'uuid'; // Keep for unique item IDs if necessary

// Define a structure for individual display items
interface DisplayShoppingListItem {
  id: string; // Unique ID for React keying and checkbox state
  name: string;
  checked: boolean;
  recipeId: string;
  recipeName: string;
  recipeImage?: string;
}

const ShoppingListPage: React.FC = () => {
  const { isAuthenticated, isLoading: authLoading, user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [displayList, setDisplayList] = useState<DisplayShoppingListItem[]>([]);

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate('/signin');
      toast({
        title: "Authentication Required",
        description: "Please sign in to access your shopping list.",
        variant: "destructive"
      });
    }
  }, [isAuthenticated, authLoading, navigate, toast]);

  // Show loading state while checking authentication
  if (authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Checking authentication...</p>
        </div>
      </div>
    );
  }

  // Show login prompt if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="pt-24 md:pt-28">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
            <Card className="text-center">
              <CardHeader>
                <div className="flex justify-center mb-4">
                  <Lock className="h-12 w-12 text-orange-500" />
                </div>
                <CardTitle className="text-2xl">Authentication Required</CardTitle>
                <CardDescription>
                  Sign in to access your shopping list and meal planning features
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                  <Link to="/signin">
                    <Button size="lg">Sign In</Button>
                  </Link>
                  <Link to="/signup">
                    <Button variant="outline" size="lg">Sign Up</Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  useEffect(() => {
    if (!isAuthenticated) return; // Don't load if not authenticated

    const loadShoppingList = () => {
      try {
        // Load manually added recipe ingredients
        const storedList = localStorage.getItem('shopping-list');
        console.log('Raw shopping list from localStorage:', storedList);
        if (storedList) {
          const items = JSON.parse(storedList);
          console.log('Parsed shopping list items:', items);
          
          // Filter out any invalid items and ensure they have required properties
          const validItems: DisplayShoppingListItem[] = items
            .filter((item: any) => {
              // Ensure item exists and has all required string properties
              const isValid = item && 
                     typeof item.name === 'string' && 
                     typeof item.recipeId === 'string' && 
                     typeof item.recipeName === 'string' &&
                     item.name.trim() !== '' &&
                     item.recipeId.trim() !== '' &&
                     item.recipeName.trim() !== '';
              
              if (!isValid) {
                console.log('Filtered out invalid item:', item);
              }
              
              return isValid;
            })
            .map((item: any) => ({
              id: item.id || uuidv4(),
              name: item.name.trim(),
              checked: item.completed || false,
              recipeId: item.recipeId.trim(),
              recipeName: item.recipeName.trim(),
              recipeImage: item.recipeImage
            }));
          
          console.log('Filtered valid items:', validItems);
          
          // Sort by recipe name, then by ingredient name (with additional safety checks)
          validItems.sort((a, b) => {
            try {
              const recipeCompare = a.recipeName.localeCompare(b.recipeName);
              if (recipeCompare !== 0) return recipeCompare;
              return a.name.localeCompare(b.name);
            } catch (error) {
              console.error('Error sorting items:', error, { a, b });
              return 0; // Don't sort if there's an error
            }
          });
          
          setDisplayList(validItems);
        } else {
          setDisplayList([]);
        }

      } catch (error) {
        console.error('Failed to load shopping list:', error);
        setDisplayList([]);
        toast({
          title: "Error",
          description: "Failed to load your shopping list.",
          variant: "destructive",
        });
      }
    };
    
    loadShoppingList();
  }, [isAuthenticated, toast]);

  // Save display list to localStorage
  const saveDisplayList = (items: DisplayShoppingListItem[]) => {
    setDisplayList(items);
    
    // Update the checked state in localStorage
    try {
      const storedList = localStorage.getItem('shopping-list');
      if (storedList) {
        const manualItems = JSON.parse(storedList);
        const updatedItems = manualItems.map((item: any) => {
          const displayItem = items.find(di => di.id === item.id);
          return {
            ...item,
            completed: displayItem?.checked || false
          };
        });
        
        localStorage.setItem('shopping-list', JSON.stringify(updatedItems));
      }
    } catch (error) {
      console.error('Error updating localStorage:', error);
    }
  };

  const handleToggleItem = (id: string) => {
    const updatedList = displayList.map(item => 
      item.id === id ? { ...item, checked: !item.checked } : item
    );
    saveDisplayList(updatedList);
  };

  const handleRemoveItem = (id: string) => {
    const updatedList = displayList.filter(item => item.id !== id);
    
    // Remove from localStorage
    try {
      const storedList = JSON.parse(localStorage.getItem('shopping-list') || '[]');
      const updatedStoredList = storedList.filter((item: any) => item.id !== id);
      localStorage.setItem('shopping-list', JSON.stringify(updatedStoredList));
    } catch (error) {
      console.error('Error removing item:', error);
    }
    
    saveDisplayList(updatedList);
    toast({
      title: "Item removed",
      description: "Ingredient removed from your shopping list."
    });
  };

  const handleClearList = () => {
    if (window.confirm('Are you sure you want to clear your entire shopping list?')) {
      localStorage.removeItem('shopping-list');
      setDisplayList([]);
      toast({
        title: "Shopping list cleared",
        description: "Your shopping list has been cleared."
      });
    }
  };

  const handleCleanupCorruptedData = () => {
    try {
      const storedList = localStorage.getItem('shopping-list');
      if (storedList) {
        const items = JSON.parse(storedList);
        const validItems = items.filter((item: any) => 
          item && 
          typeof item.name === 'string' && 
          typeof item.recipeId === 'string' && 
          typeof item.recipeName === 'string' &&
          item.name.trim() !== '' &&
          item.recipeId.trim() !== '' &&
          item.recipeName.trim() !== ''
        );
        
        if (validItems.length !== items.length) {
          localStorage.setItem('shopping-list', JSON.stringify(validItems));
          setDisplayList([]);
          toast({
            title: "Data cleaned up",
            description: `Removed ${items.length - validItems.length} corrupted items from your shopping list.`
          });
        } else {
          toast({
            title: "No cleanup needed",
            description: "Your shopping list data is clean."
          });
        }
      }
    } catch (error) {
      console.error('Error cleaning up data:', error);
      toast({
        title: "Cleanup failed",
        description: "Failed to clean up corrupted data.",
        variant: "destructive"
      });
    }
  };
  
  const handleClearChecked = () => {
    const updatedList = displayList.filter(item => !item.checked);
    saveDisplayList(updatedList);
    toast({
      title: "Completed items removed",
      description: "All checked items have been removed from your shopping list."
    });
  };

  // Group items by recipe for rendering
  const groupedList = displayList.reduce((acc, item) => {
    (acc[item.recipeName] = acc[item.recipeName] || []).push(item);
    return acc;
  }, {} as Record<string, DisplayShoppingListItem[]>);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="pt-24 md:pt-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-2">
              <ShoppingCart className="text-primary h-6 w-6" />
              <div>
                <h1 className="text-3xl font-bold">Shopping List</h1>
                {displayList.length > 0 && (
                  <p className="text-gray-600 text-sm">
                    {displayList.length} ingredients • {Object.keys(groupedList).length} recipes
                  </p>
                )}
              </div>
            </div>
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleCleanupCorruptedData}
                className="flex items-center gap-1"
              >
                <Check className="h-4 w-4" /> Cleanup Data
              </Button>
              {displayList.length > 0 && (
                <>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={handleClearChecked}
                    className="flex items-center gap-1"
                  >
                    <Check className="h-4 w-4" /> Clear Checked
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={handleClearList}
                    className="flex items-center gap-1 text-destructive hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" /> Clear All
                  </Button>
                </>
              )}
            </div>
          </div>

          {/* Removed manual recipe addition section */}
          {/* 
          <div className="bg-white shadow-sm rounded-lg p-6 mb-8">
            <h2 className="text-xl font-semibold mb-4">Add Recipe Ingredients</h2>
            <div className="flex gap-4">
              <select 
                value={selectedRecipeId || ''} 
                onChange={(e) => setSelectedRecipeId(e.target.value || null)}
                className="flex-1 border rounded-md px-3 py-2"
              >
                <option value="">Select a recipe</option>
                {recipes.map((recipe: Recipe) => (
                  <option key={recipe.id} value={recipe.id}>{recipe.name}</option>
                ))}
              </select>
              <Button 
                onClick={handleAddToShoppingList} 
                disabled={!selectedRecipeId}
                className="flex items-center gap-1"
              >
                <ShoppingCart className="h-4 w-4" /> Add Ingredients
              </Button>
            </div>
          </div>
          */}

          {displayList.length > 0 ? (
            <div className="space-y-6">
              <div className="bg-white shadow-sm rounded-lg p-6">
                <h2 className="text-xl font-semibold mb-4">Your Shopping List</h2>
                <div className="space-y-6">
                  {Object.keys(groupedList).sort().map(recipeName => (
                    <div key={recipeName} className="border rounded-lg p-4">
                      <h3 className="text-lg font-bold text-gray-700 mb-3 border-b pb-2">
                        🍳 {recipeName}
                      </h3>
                      <div className="space-y-2">
                        {groupedList[recipeName].map((item) => (
                          <div key={item.id} className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded">
                            <div className="flex items-center gap-3 flex-1">
                              <Checkbox 
                                id={`item-${item.id}`} 
                                checked={item.checked}
                                onCheckedChange={() => handleToggleItem(item.id)}
                              />
                              <label 
                                htmlFor={`item-${item.id}`}
                                className={`${item.checked ? 'line-through text-gray-500' : ''} font-medium`}
                              >
                                {item.name}
                              </label>
                            </div>
                            <button 
                              onClick={() => handleRemoveItem(item.id)}
                              className="text-gray-500 hover:text-red-500"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <ShoppingCart className="mx-auto h-12 w-12 text-gray-400" strokeWidth={1.5} />
              <h3 className="mt-2 text-lg font-medium text-gray-900">Your shopping list is empty</h3>
              <p className="mt-1 text-gray-500">
                Add ingredients to your shopping list by:
              </p>
              <div className="mt-4 space-y-2 text-sm text-gray-600">
                <p>• Clicking "Add to Shopping List" on any recipe page</p>
                <p>• Browse recipes and add your favorites to build your list</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ShoppingListPage;
