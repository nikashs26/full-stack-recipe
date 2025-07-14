
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Header from '../components/Header';
import { ShoppingListItem, Recipe } from '../types/recipe'; // Keep Recipe for now if needed elsewhere
import { useQuery, useQueryClient } from '@tanstack/react-query'; // Keep if you still need other queries
import { loadRecipes } from '../utils/storage'; // Keep if you still need to load recipes
import { Check, ShoppingCart, Trash2, RefreshCw, DollarSign } from 'lucide-react';
import { v4 as uuidv4 } from 'uuid'; // Keep for unique item IDs if necessary
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { useToast } from '@/hooks/use-toast';

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
  const [agentShoppingList, setAgentShoppingList] = useState<AgentShoppingList | null>(null);
  const [displayList, setDisplayList] = useState<DisplayShoppingListItem[]>([]);
  const [estimatedCost, setEstimatedCost] = useState<string>('');
  const [servingAmount, setServingAmount] = useState<string>('');
  const [weeklyBudget, setWeeklyBudget] = useState<string>('');
  const { toast } = useToast();

  useEffect(() => {
    const loadAgentShoppingList = () => {
      try {
        const storedList = localStorage.getItem('agent-shopping-list');
        if (storedList) {
          const parsedList = JSON.parse(storedList);
          setAgentShoppingList(parsedList);
          setEstimatedCost(parsedList.estimated_cost || '');
          
          // Load budget and serving info from preferences
          const loadPreferences = async () => {
            try {
              const response = await fetch('http://localhost:5003/api/temp-preferences', {
                credentials: 'include' // Include cookies for session
              });
              if (response.ok) {
                const data = await response.json();
                if (data.preferences) {
                  setWeeklyBudget(data.preferences.weeklyBudget || '');
                  setServingAmount(data.preferences.servingAmount || '');
                }
              }
            } catch (error) {
              console.error('Error loading preferences:', error);
            }
          };
          loadPreferences();
          
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
  }, []);

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
