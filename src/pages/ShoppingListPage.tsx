
import React, { useState, useEffect } from 'react';
import Header from '../components/Header';
import { ShoppingListItem, Recipe } from '../types/recipe';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { loadRecipes } from '../utils/storage';
import { Check, ShoppingCart, Trash2, RefreshCw } from 'lucide-react';
import { v4 as uuidv4 } from 'uuid';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { useToast } from '@/hooks/use-toast';

const ShoppingListPage: React.FC = () => {
  const [shoppingList, setShoppingList] = useState<ShoppingListItem[]>([]);
  const [selectedRecipeId, setSelectedRecipeId] = useState<string | null>(null);
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  // Fetch recipes
  const { data: recipes = [] } = useQuery({
    queryKey: ['recipes'],
    queryFn: loadRecipes
  });

  // Load shopping list from localStorage
  useEffect(() => {
    const loadShoppingList = () => {
      try {
        const storedList = localStorage.getItem('recipe-shopping-list');
        return storedList ? JSON.parse(storedList) : [];
      } catch (error) {
        console.error('Failed to load shopping list:', error);
        return [];
      }
    };
    
    setShoppingList(loadShoppingList());
  }, []);

  // Save shopping list to localStorage
  const saveShoppingList = (items: ShoppingListItem[]) => {
    try {
      localStorage.setItem('recipe-shopping-list', JSON.stringify(items));
      setShoppingList(items);
    } catch (error) {
      console.error('Failed to save shopping list:', error);
    }
  };

  const handleAddToShoppingList = () => {
    if (!selectedRecipeId) return;
    
    const recipe = recipes.find((r: Recipe) => r.id === selectedRecipeId);
    if (!recipe) return;
    
    const newItems: ShoppingListItem[] = recipe.ingredients.map(ingredient => ({
      id: uuidv4(),
      ingredient,
      recipeId: recipe.id,
      recipeName: recipe.name,
      checked: false
    }));
    
    const updatedList = [...shoppingList, ...newItems];
    saveShoppingList(updatedList);
    
    toast({
      title: "Added to shopping list",
      description: `Ingredients from "${recipe.name}" have been added to your shopping list.`
    });
    
    setSelectedRecipeId(null);
  };

  const handleToggleItem = (id: string) => {
    const updatedList = shoppingList.map(item => 
      item.id === id ? { ...item, checked: !item.checked } : item
    );
    saveShoppingList(updatedList);
  };

  const handleRemoveItem = (id: string) => {
    const updatedList = shoppingList.filter(item => item.id !== id);
    saveShoppingList(updatedList);
  };

  const handleClearList = () => {
    if (window.confirm('Are you sure you want to clear your entire shopping list?')) {
      saveShoppingList([]);
      toast({
        title: "Shopping list cleared",
        description: "Your shopping list has been cleared."
      });
    }
  };
  
  const handleClearChecked = () => {
    const updatedList = shoppingList.filter(item => !item.checked);
    saveShoppingList(updatedList);
    toast({
      title: "Completed items removed",
      description: "All checked items have been removed from your shopping list."
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="pt-24 md:pt-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-2">
              <ShoppingCart className="text-primary h-6 w-6" />
              <h1 className="text-3xl font-bold">Shopping List</h1>
            </div>
            {shoppingList.length > 0 && (
              <div className="flex gap-2">
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
              </div>
            )}
          </div>

          <div className="bg-white shadow-sm rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Add Recipe Ingredients</h2>
            <div className="flex gap-4 mb-8">
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

            {shoppingList.length > 0 ? (
              <div>
                <h2 className="text-xl font-semibold mb-4">Your Shopping List</h2>
                <div className="divide-y">
                  {shoppingList.map((item) => (
                    <div key={item.id} className="py-3 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Checkbox 
                          id={`item-${item.id}`} 
                          checked={item.checked}
                          onCheckedChange={() => handleToggleItem(item.id)}
                        />
                        <label 
                          htmlFor={`item-${item.id}`}
                          className={`${item.checked ? 'line-through text-gray-500' : ''}`}
                        >
                          {item.ingredient}
                          <span className="text-xs text-gray-500 ml-2">
                            ({item.recipeName})
                          </span>
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
            ) : (
              <div className="text-center py-12">
                <ShoppingCart className="mx-auto h-12 w-12 text-gray-400" strokeWidth={1.5} />
                <h3 className="mt-2 text-lg font-medium text-gray-900">Your shopping list is empty</h3>
                <p className="mt-1 text-gray-500">
                  Add ingredients from your favorite recipes.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ShoppingListPage;
