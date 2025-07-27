// URLs for API endpoints - fallback to mock data when not available
// Using localhost for consistency with other API calls
const API_BASE_URL = "http://localhost:5003";
const API_URL = `${API_BASE_URL}/api/recipes`; // ChromaDB recipes endpoint
const API_URL_RECIPE_BY_ID = `${API_BASE_URL}/api/recipes`;

// Fallback data for when the API is unavailable
const FALLBACK_RECIPES = [
  {
    id: 101,
    title: "Beef Tacos",
    image: "https://images.unsplash.com/photo-1599974579688-8dbdd335c77f?auto=format&fit=crop&w=400&h=300",
    cuisines: ["Mexican"],
    diets: ["carnivore"],
    readyInMinutes: 30
  },
  {
    id: 102,
    title: "Vegetable Curry",
    image: "https://images.unsplash.com/photo-1455619452474-d2be8b1e70cd?auto=format&fit=crop&w=400&h=300",
    cuisines: ["Indian"],
    diets: ["Vegetarian"],
    readyInMinutes: 45
  },
  {
    id: 103,
    title: "Chicken Alfredo",
    image: "https://images.unsplash.com/photo-1645112411341-6c4fd023714a?auto=format&fit=crop&w=400&h=300",
    cuisines: ["Italian"],
    diets: ["Non-Vegetarian"],
    readyInMinutes: 25
  },
  {
    id: 104,
    title: "Super Cheesy Burger",
    image: "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=400&h=300",
    cuisines: ["American"],
    diets: ["Non-Vegetarian"],
    readyInMinutes: 40
  },
  {
    id: 105,
    title: "Chicken 65",
    image: "https://images.unsplash.com/photo-1610057099443-fde8c4d50f91?auto=format&fit=crop&w=400&h=300",
    cuisines: ["Indian"],
    diets: ["Non-Vegetarian"],
    readyInMinutes: 35
  },
  {
    id: 106,
    title: "Caesar Salad",
    image: "https://images.unsplash.com/photo-1546793665-c74683f339c1?auto=format&fit=crop&w=400&h=300",
    cuisines: ["American"],
    diets: ["Vegetarian"],
    readyInMinutes: 15
  },
  {
    id: 107,
    title: "Spaghetti Carbonara",
    image: "https://images.unsplash.com/photo-1612874742237-6526221588e3?auto=format&fit=crop&w=400&h=300",
    cuisines: ["Italian"],
    diets: ["Non-Vegetarian"],
    readyInMinutes: 20
  },
  {
    id: 108,
    title: "Thai Green Curry",
    image: "https://images.unsplash.com/photo-1455619452474-d2be8b1e70cd?auto=format&fit=crop&w=400&h=300",
    cuisines: ["Thai"],
    diets: ["Vegetarian"],
    readyInMinutes: 30
  },
  {
    id: 109,
    title: "BBQ Pulled Pork",
    image: "https://images.unsplash.com/photo-1529694157872-4e0c0f3b238b?auto=format&fit=crop&w=400&h=300",
    cuisines: ["American"],
    diets: ["Non-Vegetarian"],
    readyInMinutes: 480
  },
  {
    id: 110,
    title: "Margherita Pizza",
    image: "https://images.unsplash.com/photo-1604382355076-af4b0eb60143?auto=format&fit=crop&w=400&h=300",
    cuisines: ["Italian"],
    diets: ["Vegetarian"],
    readyInMinutes: 25
  },
  {
    id: 111,
    title: "Chicken Tikka Masala",
    image: "https://images.unsplash.com/photo-1588166524941-3bf61a9c41db?auto=format&fit=crop&w=400&h=300",
    cuisines: ["Indian"],
    diets: ["Non-Vegetarian"],
    readyInMinutes: 45
  },
  {
    id: 112,
    title: "Greek Salad",
    image: "https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=400&h=300",
    cuisines: ["Mediterranean"],
    diets: ["Vegetarian"],
    readyInMinutes: 15
  },
  {
    id: 113,
    title: "Classic Mac and Cheese",
    image: "https://images.unsplash.com/photo-1543339494-b4cd4f7ba686?auto=format&fit=crop&w=400&h=300",
    cuisines: ["American"],
    diets: ["Vegetarian"],
    readyInMinutes: 35
  },
  {
    id: 114,
    title: "Buffalo Wings",
    image: "https://images.unsplash.com/photo-1608039858788-667850f129d3?auto=format&fit=crop&w=400&h=300",
    cuisines: ["American"],
    diets: ["Non-Vegetarian"],
    readyInMinutes: 45
  },
  {
    id: 115,
    title: "Grilled Cheese Sandwich",
    image: "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=400&h=300",
    cuisines: ["American"],
    diets: ["Vegetarian"],
    readyInMinutes: 10
  },
  {
    id: 116,
    title: "Pancakes",
    image: "https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?auto=format&fit=crop&w=400&h=300",
    cuisines: ["American"],
    diets: ["Vegetarian"],
    readyInMinutes: 20
  },
  {
    id: 117,
    title: "Meatloaf",
    image: "https://images.unsplash.com/photo-1544378375-12d18e9da4c7?auto=format&fit=crop&w=400&h=300",
    cuisines: ["American"],
    diets: ["Non-Vegetarian"],
    readyInMinutes: 90
  },
  {
    id: 118,
    title: "Coleslaw",
    image: "https://images.unsplash.com/photo-1592417817098-8fd3d9eb14a5?auto=format&fit=crop&w=400&h=300",
    cuisines: ["American"],
    diets: ["Vegetarian"],
    readyInMinutes: 15
  }
];

export const fetchRecipes = async (query: string = "", ingredient: string = "", limit: number = 12) => {
    console.log(`[DEBUG] Fetching recipes with query: "${query}", ingredient: "${ingredient}"`);
    
    try {
        // Build the URL with appropriate parameters
        const params = new URLSearchParams();
        if (query) params.append('query', query);
        if (ingredient) params.append('ingredient', ingredient);
        
        const url = `${API_URL}?${params.toString()}`;
        console.log('[DEBUG] API Request URL:', url);
        
        // Add a timeout to the fetch request
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
        
        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            console.log('[DEBUG] API Response status:', response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('[DEBUG] API Error Response:', {
                    status: response.status,
                    statusText: response.statusText,
                    url: response.url,
                    error: errorText
                });
                throw new Error(`API Error: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('[DEBUG] API Response data:', JSON.stringify(data, null, 2));
            
            // Check if we have a valid response structure
            if (!data) {
                console.error('[DEBUG] Empty response from API');
                return { results: [], totalResults: 0 };
            }
            
            // Handle both array and object with results property
            const results = Array.isArray(data) ? data : (data.results || []);
            
            if (!Array.isArray(results)) {
                console.error('[DEBUG] Invalid results format:', results);
                return { results: [], totalResults: 0 };
            }
            
            // Format recipes to match expected frontend format
            const formattedResults = results.slice(0, limit).map((recipe: any) => {
                try {
                    // If recipe is a string, try to parse it as JSON
                    const recipeData = typeof recipe === 'string' ? JSON.parse(recipe) : recipe;
                    
                    return {
                        id: recipeData.id || `recipe-${Math.random().toString(36).substr(2, 9)}`,
                        title: recipeData.title || recipeData.strMeal || 'Untitled Recipe',
                        image: recipeData.image || recipeData.strMealThumb || '',
                        cuisines: Array.isArray(recipeData.cuisines) ? recipeData.cuisines : 
                                 (recipeData.cuisine ? [recipeData.cuisine] : 
                                 (recipeData.strArea ? [recipeData.strArea] : [])),
                        diets: Array.isArray(recipeData.diets) ? recipeData.diets : [],
                        readyInMinutes: recipeData.readyInMinutes || 30,
                        instructions: Array.isArray(recipeData.instructions) ? recipeData.instructions : 
                                     (recipeData.strInstructions ? [recipeData.strInstructions] : []),
                        ingredients: Array.isArray(recipeData.ingredients) ? recipeData.ingredients : [],
                        source: 'external',
                        // Include any other fields that might be needed
                        ...recipeData
                    };
                } catch (e) {
                    console.error('[DEBUG] Error formatting recipe:', e, 'Raw recipe:', recipe);
                    return null;
                }
            }).filter(Boolean); // Remove any null entries from failed parsing
            
            console.log(`[DEBUG] Successfully formatted ${formattedResults.length} recipes`);
            
            return { 
                results: formattedResults,
                totalResults: formattedResults.length
            };
            
        } catch (error) {
            clearTimeout(timeoutId);
            throw error; // Re-throw to be caught by the outer catch
        }
        
    } catch (error) {
        console.error('[DEBUG] Error in fetchRecipes:', error);
        return { 
            results: [],
            totalResults: 0,
            error: error instanceof Error ? error.message : 'Unknown error occurred',
            details: error instanceof Error ? error.stack : undefined
        };
    }
};

// Helper function to filter fallback recipes
const filterFallbackRecipes = (query: string = "", ingredient: string = "") => {
    if (!query && !ingredient) {
        // Return all fallback recipes if no search criteria
        return FALLBACK_RECIPES;
    }
    
    return FALLBACK_RECIPES.filter(recipe => {
        const matchesQuery = query ? 
            recipe.title.toLowerCase().includes(query.toLowerCase()) ||
            recipe.cuisines.some(cuisine => cuisine.toLowerCase().includes(query.toLowerCase())) : 
            true;
            
        const matchesIngredient = ingredient ? 
            // This is a simplification as we don't have ingredients in our fallback data
            recipe.title.toLowerCase().includes(ingredient.toLowerCase()) : 
            true;
        
        // Use actual cuisine data for filtering
        if (query) {
            const recipeCuisines = recipe.cuisines || [];
            
            // Primary check: Does the recipe's cuisine array contain the requested cuisine?
            const directCuisineMatch = recipeCuisines.some(cuisine => 
                cuisine.toLowerCase() === query.toLowerCase()
            );
            
            // Secondary check: Does the recipe title contain the cuisine/query?
            const titleMatch = recipe.title.toLowerCase().includes(query.toLowerCase());
            
            // If it's a direct match, accept it
            if (directCuisineMatch || titleMatch) {
                console.log(`✅ Fallback recipe "${recipe.title}" matches ${query} (cuisines: ${recipeCuisines.join(', ')})`);
                return matchesIngredient;
            }
            
            // If no direct match, reject it
            console.log(`❌ Fallback recipe "${recipe.title}" does not match ${query} (cuisines: ${recipeCuisines.join(', ')})`);
            return false;
        }
            
        return matchesQuery && matchesIngredient;
    });
};

export const fetchRecipeById = async (recipeId: number | string) => {
    console.log(`Fetching recipe by ID: ${recipeId}`);
    
    // Check if this is a fallback recipe ID
    const fallbackRecipe = FALLBACK_RECIPES.find(recipe => recipe.id === parseInt(recipeId.toString()));
    if (fallbackRecipe) {
        console.log("Found fallback recipe, returning detailed information");
        return getDetailedFallbackRecipe(fallbackRecipe);
    }
    
    try {
        // Try to fetch from API first
        const response = await fetch(`${API_URL_RECIPE_BY_ID}?id=${recipeId}`, {
            signal: AbortSignal.timeout(10000)
        });
        
        console.log(`Recipe API response status: ${response.status}`);
        
        if (!response.ok) {
            throw new Error(`Failed to fetch recipe (Status: ${response.status})`);
        }
        
        const data = await response.json();
        console.log("Recipe API response received:", data);
        
        if (data && data.id) {
            return data;
        } else {
            throw new Error("Invalid recipe data received from API");
        }
    } catch (error) {
        console.error("Error fetching recipe by ID:", error);
        
        // Return a detailed fallback recipe if API fails
        return getDetailedFallbackRecipe({
            id: parseInt(recipeId.toString()),
            title: "Recipe Not Available",
            image: "https://via.placeholder.com/312x231?text=Recipe+Not+Available",
            cuisines: ["International"],
            diets: ["Various"],
            readyInMinutes: 30
        });
    }
};

// Helper function to create detailed recipe information for fallback recipes
const getDetailedFallbackRecipe = (recipe: any) => {
    const detailedRecipes = {
        101: {
            ...recipe,
            summary: "Delicious beef tacos with fresh toppings and warm tortillas. A classic Mexican dish that's perfect for any occasion.",
            ingredients: [
                { name: "Ground beef", amount: 1, unit: "lb" },
                { name: "Taco seasoning", amount: 1, unit: "packet" },
                { name: "Corn tortillas", amount: 8, unit: "pieces" },
                { name: "Lettuce", amount: 2, unit: "cups shredded" },
                { name: "Tomatoes", amount: 2, unit: "medium diced" },
                { name: "Cheese", amount: 1, unit: "cup shredded" },
                { name: "Sour cream", amount: 0.5, unit: "cup" }
            ],
            instructions: [
                "Brown the ground beef in a large skillet over medium-high heat.",
                "Add taco seasoning and water according to packet directions.",
                "Simmer for 5 minutes until sauce thickens.",
                "Warm tortillas in microwave or on griddle.",
                "Fill tortillas with beef mixture and desired toppings.",
                "Serve immediately with lime wedges."
            ]
        },
        102: {
            ...recipe,
            summary: "A flavorful and aromatic vegetable curry packed with nutrients and spices. Perfect for vegetarians and curry lovers.",
            ingredients: [
                { name: "Mixed vegetables", amount: 3, unit: "cups chopped" },
                { name: "Coconut milk", amount: 1, unit: "can" },
                { name: "Curry powder", amount: 2, unit: "tbsp" },
                { name: "Onion", amount: 1, unit: "large diced" },
                { name: "Garlic", amount: 3, unit: "cloves minced" },
                { name: "Ginger", amount: 1, unit: "tbsp fresh grated" },
                { name: "Vegetable oil", amount: 2, unit: "tbsp" }
            ],
            instructions: [
                "Heat oil in a large pot over medium heat.",
                "Sauté onion, garlic, and ginger until fragrant.",
                "Add curry powder and cook for 1 minute.",
                "Add vegetables and coconut milk.",
                "Simmer for 20-25 minutes until vegetables are tender.",
                "Season with salt and pepper to taste.",
                "Serve over rice or with naan bread."
            ]
        },
        103: {
            ...recipe,
            summary: "Creamy chicken alfredo pasta with tender chicken and rich parmesan sauce. A comforting Italian-American classic.",
            ingredients: [
                { name: "Chicken breast", amount: 2, unit: "pieces" },
                { name: "Fettuccine pasta", amount: 12, unit: "oz" },
                { name: "Heavy cream", amount: 1, unit: "cup" },
                { name: "Parmesan cheese", amount: 1, unit: "cup grated" },
                { name: "Butter", amount: 4, unit: "tbsp" },
                { name: "Garlic", amount: 3, unit: "cloves minced" }
            ],
            instructions: [
                "Cook pasta according to package directions.",
                "Season and cook chicken until golden brown.",
                "Slice chicken and set aside.",
                "Melt butter in the same pan, add garlic.",
                "Add cream and simmer until slightly thickened.",
                "Stir in parmesan cheese until melted.",
                "Toss pasta with sauce and top with chicken."
            ]
        },
        106: {
            ...recipe,
            summary: "Classic Caesar salad with crisp romaine lettuce, parmesan cheese, and creamy dressing.",
            ingredients: [
                { name: "Romaine lettuce", amount: 2, unit: "heads" },
                { name: "Parmesan cheese", amount: 0.5, unit: "cup grated" },
                { name: "Croutons", amount: 1, unit: "cup" },
                { name: "Caesar dressing", amount: 0.5, unit: "cup" },
                { name: "Lemon", amount: 1, unit: "piece" }
            ],
            instructions: [
                "Wash and chop romaine lettuce.",
                "Toss lettuce with Caesar dressing.",
                "Add croutons and parmesan cheese.",
                "Squeeze fresh lemon juice over salad.",
                "Serve immediately."
            ]
        }
    };
    
    return detailedRecipes[recipe.id] || {
        ...recipe,
        summary: `A delicious ${recipe.title.toLowerCase()} recipe with authentic flavors and fresh ingredients.`,
        ingredients: [
            { name: "Main ingredient", amount: 1, unit: "portion" },
            { name: "Seasonings", amount: 1, unit: "as needed" },
            { name: "Additional ingredients", amount: 1, unit: "as required" }
        ],
        instructions: [
            "Prepare all ingredients according to recipe requirements.",
            "Follow traditional cooking methods for this dish.",
            "Season to taste and serve hot.",
            "Enjoy your homemade meal!"
        ]
    };
};

// ChromaDB API functions
export const getAllRecipes = async () => {
    try {
        const response = await fetch(API_URL);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Error fetching recipes:", error);
        return [];
    }
};

export const getRecipe = async (recipeId: string) => {
    try {
        const response = await fetch(`${API_URL}/${recipeId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Error fetching recipe ${recipeId}:`, error);
        return null;
    }
};

export const saveRecipe = async (recipe: any) => {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(recipe),
            credentials: 'include'
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error saving recipe:', error);
        throw error;
    }
};
