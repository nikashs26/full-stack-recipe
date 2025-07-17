
import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useToast } from '@/hooks/use-toast';
import Header from '../components/Header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ShoppingCart, Plus, Trash2, Check, X, Loader2, Lock, DollarSign } from 'lucide-react';
import { Checkbox } from '@/components/ui/checkbox';
import { ShoppingListItem, Recipe } from '../types/recipe'; // Keep Recipe for now if needed elsewhere
import { useQuery, useQueryClient } from '@tanstack/react-query'; // Keep if you still need other queries
import { loadRecipes } from '../utils/storage'; // Keep if you still need to load recipes
import { v4 as uuidv4 } from 'uuid'; // Keep for unique item IDs if necessary

// Define the structure of the agent-generated shopping list
interface AgentShoppingList {
  items: {
    name: string;
    category: string;
    completed: boolean;
  }[];
  estimated_cost: string;
  generated_at: string;
  meal_plan_id: string;
}

// Define a structure for individual display items
interface DisplayShoppingListItem {
  id: string; // Unique ID for React keying and checkbox state
  category: string;
  name: string;
  checked: boolean;
}

const ShoppingListPage: React.FC = () => {
  const { isAuthenticated, isLoading: authLoading, user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [agentShoppingList, setAgentShoppingList] = useState<AgentShoppingList | null>(null);
  const [displayList, setDisplayList] = useState<DisplayShoppingListItem[]>([]);
  const [estimatedCost, setEstimatedCost] = useState<string>('');
  const [servingAmount, setServingAmount] = useState<string>('');
  const [weeklyBudget, setWeeklyBudget] = useState<string>('');

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

    const loadAgentShoppingList = () => {
      try {
        const storedList = localStorage.getItem('agent-shopping-list');
        if (storedList) {
          const parsedList = JSON.parse(storedList);
          setAgentShoppingList(parsedList);
          setEstimatedCost(parsedList.estimated_cost || '');
          
          // Convert to display format
          const flattenedList: DisplayShoppingListItem[] = parsedList.items.map(item => ({
            id: uuidv4(),
            category: item.category,
            name: item.name,
            checked: item.completed || false,
          }));
          
          // Sort by category then by ingredient name
          flattenedList.sort((a, b) => {
            if (a.category < b.category) return -1;
            if (a.category > b.category) return 1;
            return a.name.localeCompare(b.name);
          });
          setDisplayList(flattenedList);

        } else {
          setAgentShoppingList(null);
          setDisplayList([]);
        }
      } catch (error) {
        console.error('Failed to load agent-generated shopping list:', error);
        setAgentShoppingList(null);
        setDisplayList([]);
        toast({
          title: "Error",
          description: "Failed to load your shopping list.",
          variant: "destructive",
        });
      }
    };
    
    loadAgentShoppingList();
  }, [isAuthenticated, toast]);

  // Save display list to localStorage (not strictly necessary if only reading from agent-list)
  // But good for persistence of checked state
  const saveDisplayList = (items: DisplayShoppingListItem[]) => {
    setDisplayList(items);
    // If you want to persist checked state across sessions for the *agent-generated* list
    // you'd need a more complex structure to map checked state back to categories/ingredients
    // For simplicity, we'll only persist the checked state locally within this component's lifecycle.
  };

  const handleToggleItem = (id: string) => {
    const updatedList = displayList.map(item => 
      item.id === id ? { ...item, checked: !item.checked } : item
    );
    saveDisplayList(updatedList);
  };

  const handleRemoveItem = (id: string) => {
    const updatedList = displayList.filter(item => item.id !== id);
    saveDisplayList(updatedList);
    toast({
      title: "Item removed",
      description: "Ingredient removed from your shopping list."
    });
  };

  const handleClearList = () => {
    if (window.confirm('Are you sure you want to clear your entire shopping list?')) {
      localStorage.removeItem('agent-shopping-list'); // Clear the stored agent list
      setAgentShoppingList(null);
      setDisplayList([]);
      toast({
        title: "Shopping list cleared",
        description: "Your shopping list has been cleared."
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

  // Group items by category for rendering
  const groupedList = displayList.reduce((acc, item) => {
    (acc[item.category] = acc[item.category] || []).push(item);
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
              <h1 className="text-3xl font-bold">Shopping List</h1>
            </div>
            {displayList.length > 0 && (
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
              {/* Budget and Serving Information */}
              <div className="bg-white shadow-sm rounded-lg p-6">
                <h2 className="text-xl font-semibold mb-4 flex items-center">
                  <DollarSign className="h-5 w-5 mr-2" />
                  Shopping Summary
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">{estimatedCost || 'N/A'}</div>
                    <div className="text-sm text-gray-600">Estimated Cost</div>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">{servingAmount || 'N/A'}</div>
                    <div className="text-sm text-gray-600">People to Serve</div>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600">{weeklyBudget ? `$${weeklyBudget}` : 'N/A'}</div>
                    <div className="text-sm text-gray-600">Weekly Budget</div>
                  </div>
                </div>
                {weeklyBudget && estimatedCost && (
                  <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                    <div className="text-sm text-gray-600">
                      Budget Status: {parseFloat(estimatedCost.replace(/[^0-9.-]+/g,"")) <= parseFloat(weeklyBudget) ? 
                        <span className="text-green-600 font-semibold">✓ Within Budget</span> : 
                        <span className="text-red-600 font-semibold">⚠ Over Budget</span>
                      }
                    </div>
                  </div>
                )}
              </div>

              <div className="bg-white shadow-sm rounded-lg p-6">
                <h2 className="text-xl font-semibold mb-4">Generated Shopping List</h2>
                <div className="space-y-6">
                  {Object.keys(groupedList).sort().map(category => (
                    <div key={category}>
                      <h3 className="text-lg font-bold text-gray-700 mb-3 border-b pb-2 capitalize">
                        {category}
                      </h3>
                      <div className="divide-y">
                        {groupedList[category].map((item) => (
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
              <h3 className="mt-2 text-lg font-medium text-gray-900">No shopping list generated yet</h3>
              <p className="mt-1 text-gray-500">
                Go to the <Link to="/meal-planner" className="text-primary hover:underline">Meal Planner</Link> to generate your weekly plan and then create a shopping list.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ShoppingListPage;
