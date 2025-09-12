import { getApiUrl } from '../config/api';
import { getReliableImageUrl } from '../utils/recipeUtils';
import { cleanRecipeDescription } from '../utils/recipeDescriptionCleaner';

// Use the Railway backend API URL
const API_BASE_URL = getApiUrl();

export interface ManualRecipe {
  id: string | number;
  title: string;
  description?: string;
  ready_in_minutes?: number;
  cuisine?: string[] | string;
  cuisines?: string[] | string;
  diets?: string[] | string;
  tags?: string[] | string;
  dietary_restrictions?: string[];
  dish_types?: string[] | string;
  image?: string;
  ingredients?: Array<{ name: string; amount?: string | number; unit?: string }>;
  instructions?: string | string[];
  created_at?: string;
  updated_at?: string;
}

// Fallback sample recipes when backend is empty


export interface FetchRecipesOptions {
  query?: string;
  ingredient?: string;
  page?: number;
  pageSize?: number;
  cuisines?: string[];
  diets?: string[];
  favoriteFoods?: string[];
  baseRecipes?: any[]; // For chained search: filter ingredient search within previous results
}

export interface PaginatedRecipes {
  recipes: ManualRecipe[];
  total: number;
}

export const fetchManualRecipes = async (
  query: any = '', 
  ingredient: any = '',
  options: FetchRecipesOptions = {}
): Promise<PaginatedRecipes> => {
  try {
    const params = new URLSearchParams();
    
    // Handle search query and ingredient
    const queryStr = typeof query === 'string' ? query.trim() : '';
    const ingredientStr = typeof ingredient === 'string' ? ingredient.trim() : '';
    // Always send both parameters to ensure backend can properly determine search type
    // Even if empty, the backend needs to know whether to do name search, ingredient search, or combined search
    params.append('query', queryStr);
    params.append('ingredient', ingredientStr);
    
    // Debug logging to help identify the issue
    console.log('🔍 fetchManualRecipes called with:');
    console.log('  - query:', query, '(type:', typeof query, ')');
    console.log('  - ingredient:', ingredient, '(type:', typeof ingredient, ')');
    console.log('  - queryStr:', queryStr);
    console.log('  - ingredientStr:', ingredientStr);
    console.log('  - URL params being built:', params.toString());
    console.log('  - Backend will receive: query="' + queryStr + '", ingredient="' + ingredientStr + '"');
    console.log('  - This ensures backend can properly determine search type (name, ingredient, or combined)');
    
    // Handle pagination - always send pagination parameters to backend
    if (options.page && options.pageSize) {
      // Calculate offset based on current page and page size
      const offset = (options.page - 1) * options.pageSize;
      params.append('offset', offset.toString());
      params.append('limit', options.pageSize.toString());
      console.log(`🔍 PAGINATION DEBUG: page ${options.page}, pageSize ${options.pageSize}, offset ${offset}`);
      console.log(`🔍 URL params being sent:`, params.toString());
    } else {
      // Fallback: if no pagination options, use defaults
      params.append('offset', '0');
      const defaultLimit = import.meta.env.VITE_RECIPE_LIMIT || '10000';
      params.append('limit', defaultLimit);
      console.log(`⚠️ Using default pagination: offset 0, limit ${defaultLimit}`);
    }
    
    // Handle cuisines filter
    if (options.cuisines?.length) {
      params.append('cuisine', options.cuisines.join(','));
    }
    
    // Handle favorite foods
    if (options.favoriteFoods?.length) {
      params.append('favorite_foods', options.favoriteFoods.join(','));
    }
    
    // Handle diets filter - ensure consistent naming with backend
    if (options.diets?.length) {
      // Map frontend diet names to backend-expected values if needed
      const mappedDiets = options.diets.map(diet => {
        // Convert to lowercase for case-insensitive comparison
        const lowerDiet = diet.toLowerCase();
        if (lowerDiet === 'vegetarian') return 'vegetarian';
        if (lowerDiet === 'vegan') return 'vegan';
        if (lowerDiet === 'gluten-free') return 'gluten free';
        if (lowerDiet === 'dairy-free') return 'dairy free';
        return diet;
      });
      
      // Join with comma and ensure no empty values
      const dietParam = mappedDiets.join(',');
      if (dietParam) {
        params.append('dietary_restrictions', dietParam);
      }
    }
    
    const queryString = params.toString();
    const url = `${API_BASE_URL}/api/get_recipes${queryString ? `?${queryString}` : ''}`;
    console.log('🔍 Final API call details:');
    console.log('  - Base URL:', API_BASE_URL);
    console.log('  - Query string:', queryString);
    console.log('  - Full URL:', url);
    console.log('  - This URL will be called to search for recipes');
    
    // Get the authentication token from localStorage
    const token = localStorage.getItem('auth_token');
    
    const headers: HeadersInit = {
      'Accept': 'application/json',
    };
    
    // Add Authorization header if token exists
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(url, { headers });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Error response:', {
        status: response.status,
        statusText: response.statusText,
        url: response.url,
        error: errorText
      });
      
      // Don't throw for 404, just return empty result
      if (response.status === 404) {
        console.log('No recipes found for query');
        return { recipes: [], total: 0 };
      }
      
      throw new Error(`Error ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json().catch(e => {
      console.error('Error parsing JSON response:', e);
      throw new Error('Invalid response from server');
    });
    
    console.log('🔍 Backend response received:');
    console.log('  - Response status:', response.status);
    console.log('  - Response URL:', response.url);
    console.log('  - Raw data:', data);
    console.log('  - Data type:', typeof data);
    console.log('  - Data keys:', data ? Object.keys(data) : 'No data');
    
    // Handle both array response and object with results key
    let recipes: any[] = [];
    let total = 0;
    
    if (data && data.results && data.total !== undefined) {
      // New format with results and total
      recipes = data.results;
      total = data.total;
    } else if (Array.isArray(data)) {
      // Fallback: Direct array response
      recipes = data;
      total = data.length;
    } else if (data && Array.isArray(data.results)) {
      // Fallback: Object with results array
      recipes = data.results;
      total = data.total || data.results.length;
    } else if (data && data.recipes && Array.isArray(data.recipes)) {
      // Fallback: Some APIs use 'recipes' key
      recipes = data.recipes;
      total = data.total || data.recipes.length;
    }
    
    if (recipes.length > 0) {
      // Transform the response to match ManualRecipe format with enhanced dietary info
      const transformedRecipes = recipes.map((recipe: any) => {
        // Extract data from nested structure (Railway API format)
        const recipeData = recipe.data || recipe;
        const metadata = recipe.metadata || {};
        
        // Normalize dietary restrictions
        let diets: string[] = [];
        if (Array.isArray(recipeData.diets)) {
          // Ensure all diet values are strings and trim whitespace
          diets = recipeData.diets
            .map((d: any) => (typeof d === 'string' ? d.trim().toLowerCase() : ''))
            .filter(Boolean);
        } else if (typeof recipeData.diets === 'string' && recipeData.diets.trim()) {
          // Handle case where diets is a comma-separated string
          diets = recipeData.diets.split(',').map(d => d.trim().toLowerCase()).filter(Boolean);
        }
        
        // Also check dietary_restrictions field
        if (Array.isArray(recipeData.dietary_restrictions)) {
          const restrictions = recipeData.dietary_restrictions
            .map((d: any) => (typeof d === 'string' ? d.trim().toLowerCase() : ''))
            .filter(Boolean);
          // Merge with diets, avoiding duplicates
          diets = [...new Set([...diets, ...restrictions])];
        }
        
        // Normalize tags
        let tags: string[] = [];
        if (Array.isArray(recipeData.tags)) {
          tags = recipeData.tags
            .map((t: any) => (typeof t === 'string' ? t.trim() : ''))
            .filter(Boolean);
        } else if (typeof recipeData.tags === 'string' && recipeData.tags.trim()) {
          // Handle case where tags is a comma-separated string
          tags = recipeData.tags.split(',').map(t => t.trim()).filter(Boolean);
        }
        
        // Normalize dish types
        let dishTypes: string[] = [];
        if (Array.isArray(recipeData.dish_types)) {
          dishTypes = recipeData.dish_types
            .map((t: any) => (typeof t === 'string' ? t.trim() : ''))
            .filter(Boolean);
        } else if (typeof recipeData.dish_types === 'string' && recipeData.dish_types.trim()) {
          // Handle case where dish_types is a comma-separated string
          dishTypes = recipeData.dish_types.split(',').map(t => t.trim()).filter(Boolean);
        }
        
        // Normalize cuisines - check both cuisine and cuisines fields
        let cuisines: string[] = [];
        
        // First try to get cuisines from the cuisines field
        if (recipeData.cuisines) {
          if (Array.isArray(recipeData.cuisines)) {
            cuisines = recipeData.cuisines
              .map((c: any) => typeof c === 'string' ? c.trim() : '')
              .filter(Boolean);
          } else if (typeof recipeData.cuisines === 'string' && recipeData.cuisines.trim()) {
            cuisines = [recipeData.cuisines.trim()];
          }
        }
        
        // If no cuisines found, try the cuisine field
        if (cuisines.length === 0 && recipeData.cuisine) {
          if (Array.isArray(recipeData.cuisine)) {
            cuisines = recipeData.cuisine
              .map((c: any) => typeof c === 'string' ? c.trim() : '')
              .filter(Boolean);
          } else if (typeof recipeData.cuisine === 'string' && recipeData.cuisine.trim()) {
            cuisines = [recipeData.cuisine.trim()];
          }
        }
        
        // If still no cuisines found, try to extract from tags or other fields
        if (cuisines.length === 0 && recipeData.tags && Array.isArray(recipeData.tags)) {
          const cuisineTags = ['italian', 'mexican', 'chinese', 'indian', 'japanese', 'thai', 'french', 'greek', 'spanish', 'mediterranean', 'american'];
          for (const tag of recipeData.tags) {
            if (typeof tag === 'string' && cuisineTags.includes(tag.toLowerCase())) {
              cuisines = [tag];
              break;
            }
          }
        }
          
        // Handle image URL - try multiple possible fields
        let imageUrl = '';
        if (recipeData.image) {
          imageUrl = recipeData.image;
        } else if (recipeData.imageUrl) {
          imageUrl = recipeData.imageUrl;
        } else if (metadata.image) {
          imageUrl = metadata.image;
        } else if (recipeData.source === 'themealdb' && recipeData.id) {
          // Special handling for TheMealDB images
          const recipeName = recipeData.title ? recipeData.title.replace(/\s+/g, '%20') : '';
          imageUrl = `https://www.themealdb.com/images/ingredients/${recipeName}.png`;
        }
        
        // Use getReliableImageUrl to handle the image URL properly
        imageUrl = getReliableImageUrl(imageUrl, 'medium');
        
        // Build ingredients from multiple possible shapes
        const normalizedIngredients: Array<{ name: string; amount?: string | number; unit?: string }> = (() => {
          // Preferred: ingredients as objects with name/amount/unit
          if (Array.isArray(recipeData.ingredients) && recipeData.ingredients.length > 0) {
            return recipeData.ingredients.map((ing: any) => ({
              name: ing?.name || ing?.ingredient || '',
              amount: (ing?.amount !== undefined && ing?.amount !== null)
                ? (typeof ing.amount === 'object'
                    ? (ing.amount?.us?.value ?? ing.amount?.metric?.value ?? '')
                    : String(ing.amount))
                : '',
              unit: ing?.unit || ing?.measures?.us?.unitShort || ing?.measures?.metric?.unitShort || ''
            }));
          }
          // Spoonacular-style extendedIngredients
          if (Array.isArray((recipeData as any).extendedIngredients) && (recipeData as any).extendedIngredients.length > 0) {
            return (recipeData as any).extendedIngredients.map((ing: any) => ({
              name: ing?.name || ing?.originalName || '',
              amount: (ing?.measures?.us?.amount ?? ing?.measures?.metric?.amount ?? ing?.amount ?? ''),
              unit: ing?.measures?.us?.unitShort || ing?.measures?.metric?.unitShort || ing?.unit || ''
            }));
          }
          // Ingredients provided as strings
          if (Array.isArray(recipeData.ingredients) && recipeData.ingredients.length > 0) {
            return recipeData.ingredients
              .filter((ing: any) => typeof ing === 'string')
              .map((textIng: string) => ({ name: textIng, amount: '', unit: '' }));
          }
          return [];
        })();

        // Build instructions from string/array/analyzedInstructions
        const normalizedInstructions: string[] = (() => {
          // Already an array of steps
          if (Array.isArray(recipeData.instructions) && recipeData.instructions.length > 0) {
            return recipeData.instructions.filter((s: any) => typeof s === 'string' && s.trim()).map((s: string) => s.trim());
          }
          // Single string of instructions -> split on newlines or numbered steps
          if (typeof recipeData.instructions === 'string' && recipeData.instructions.trim()) {
            const raw = recipeData.instructions.trim();
            const splitByNewline = raw.split(/\n+|\r+/).map(s => s.trim()).filter(Boolean);
            if (splitByNewline.length > 1) return splitByNewline;
            // Fallback: split by sentences or step numbers
            const splitBySteps = raw.split(/\s*(?:\d+\.|Step\s*\d+:?)\s+/i).map(s => s.trim()).filter(Boolean);
            if (splitBySteps.length > 1) return splitBySteps;
            return [raw];
          }
          // Spoonacular-style analyzedInstructions
          if (Array.isArray((recipeData as any).analyzedInstructions) && (recipeData as any).analyzedInstructions.length > 0) {
            const sections = (recipeData as any).analyzedInstructions as any[];
            const steps = sections.flatMap(section => Array.isArray(section?.steps) ? section.steps : []);
            const texts = steps.map((st: any) => (typeof st?.step === 'string' ? st.step.trim() : '')).filter(Boolean);
            if (texts.length > 0) return texts;
          }
          return [];
        })();

        return {
          id: recipe.id || recipeData.id || `recipe-${Math.random().toString(36).substr(2, 9)}`,
          title: recipeData.title || 'Untitled Recipe',
          description: cleanRecipeDescription((recipeData.summary || recipeData.description || '').toString()),
          ready_in_minutes: recipeData.ready_in_minutes || recipeData.readyInMinutes || metadata.readyInMinutes || 30,
          cuisine: cuisines.length > 0 ? cuisines[0] : undefined,
          cuisines: cuisines,
          diets: diets,
          tags: tags,
          dietary_restrictions: diets, // Use the merged diets array
          dish_types: dishTypes,
          image: imageUrl,
          ingredients: normalizedIngredients,
          instructions: normalizedInstructions,
          created_at: recipeData.created_at || new Date().toISOString(),
          updated_at: recipeData.updated_at || new Date().toISOString(),
          // Include source for debugging
          source: recipe.source || 'unknown'
        };
      });
      
      // Filter out recipes that have neither ingredients nor instructions (clearly unusable)
      const usableRecipes = transformedRecipes.filter(r => (Array.isArray(r.ingredients) && r.ingredients.length > 0) || (Array.isArray(r.instructions) && r.instructions.length > 0));
      
      console.log('🔍 Search results summary:');
      console.log('  - Original query:', queryStr);
      console.log('  - Original ingredient:', ingredientStr);
      console.log('  - Backend returned:', recipes.length, 'recipes');
      console.log('  - Transformed to:', transformedRecipes.length, 'recipes');
      console.log('  - First recipe title:', transformedRecipes[0]?.title || 'No title');
      
      return {
        recipes: usableRecipes,
        total: total || usableRecipes.length
      };
    } else {
      // If no recipes found, return empty array with 0 total
      console.log('🔍 No recipes found for search:');
      console.log('  - Query:', queryStr);
      console.log('  - Ingredient:', ingredientStr);
      console.log('  - This might indicate a backend search issue');
      return {
        recipes: [],
        total: 0
      };
    }
  } catch (error) {
    console.error('Error in fetchManualRecipes:', error);
    // Return empty result when backend fails
    console.log('Backend failed');
    return {
      recipes: [],
      total: 0
    };
  }
};

export const fetchManualRecipeById = async (id: number | string): Promise<ManualRecipe | null> => {
  try {
    console.log('Fetching manual recipe by ID:', id);
    const url = `${API_BASE_URL}/api/recipes/${id}`;
    console.log('API Request URL:', url);
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });

    if (!response.ok) {
      if (response.status === 404) {
        console.log('Recipe not found (404)');
        return null;
      }
      const errorText = await response.text();
      console.error('Error response:', {
        status: response.status,
        statusText: response.statusText,
        error: errorText
      });
      throw new Error(`Failed to fetch recipe: ${response.status} - ${response.statusText}`);
    }

    const recipe = await response.json();
    
    // Transform MongoDB recipe to match the ManualRecipe interface
    const transformedRecipe: ManualRecipe = {
      id: recipe.id || recipe._id,
      title: (() => {
        let title = recipe.title || '';
        // Enhanced title generation logic to fix untitled recipes
        if (!title || title.toLowerCase().includes('untitled') || title.trim() === '') {
          // Strategy 1: Use cuisines + dish types
          if (recipe.cuisines && recipe.cuisines.length > 0) {
            const cuisine = recipe.cuisines[0];
            if (recipe.dishTypes && recipe.dishTypes.length > 0) {
              const dishType = recipe.dishTypes[0];
              title = `${cuisine} ${dishType}`;
            } else {
              title = `Traditional ${cuisine} Recipe`;
            }
          } 
          // Strategy 2: Use main ingredient
          else if (recipe.extendedIngredients && recipe.extendedIngredients.length > 0) {
            const mainIngredient = recipe.extendedIngredients[0].name || 'Special';
            const formatted = mainIngredient.split(' ').map((word: string) => 
              word.charAt(0).toUpperCase() + word.slice(1)
            ).join(' ');
            title = `Homestyle ${formatted}`;
          } 
          // Strategy 3: ID-based appealing fallback
          else {
            const recipeId = recipe.id || recipe._id || Math.random().toString(36).substr(2, 9);
            title = `Kitchen Creation #${recipeId}`;
          }
        }
        return title;
      })(),
      description: recipe.summary || recipe.description || '',
      ready_in_minutes: recipe.readyInMinutes || 30,
      cuisine: recipe.cuisines || [],
      cuisines: recipe.cuisines || [],
      diets: recipe.diets || [],
      image: getReliableImageUrl(recipe.image, 'medium'),
      ingredients: Array.isArray(recipe.ingredients) 
        ? recipe.ingredients.map((ing: any) => ({
            name: ing.name || '',
            amount: ing.amount?.toString() || '',
            unit: ing.unit || ''
          }))
        : Array.isArray(recipe.extendedIngredients)
        ? recipe.extendedIngredients.map((ing: any) => ({
            name: ing.name || '',
            amount: ing.amount?.toString() || '',
            unit: ing.unit || ''
          }))
        : [],
      instructions: Array.isArray(recipe.instructions) 
        ? recipe.instructions
        : recipe.instructions 
        ? [recipe.instructions]
        : recipe.analyzedInstructions && Array.isArray(recipe.analyzedInstructions)
        ? recipe.analyzedInstructions.flatMap((section: any) => 
            section.steps?.map((step: any) => step.step).filter(Boolean) || []
          )
        : [],
      created_at: recipe.added_at ? new Date(recipe.added_at * 1000).toISOString() : new Date().toISOString(),
      updated_at: recipe.added_at ? new Date(recipe.added_at * 1000).toISOString() : new Date().toISOString()
    };

    console.log('Successfully fetched manual recipe:', transformedRecipe.title);
    return transformedRecipe;
  } catch (error) {
    console.error('Error in fetchManualRecipeById:', error);
    return null;
  }
};

export const createManualRecipe = async (recipe: Partial<ManualRecipe>): Promise<ManualRecipe | null> => {
  try {
    console.log('Creating manual recipe:', recipe.title);
    const url = `${API_BASE_URL}/api/recipes`;
    console.log('API Request URL:', url);
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify({
        title: recipe.title,
        summary: recipe.description,
        readyInMinutes: recipe.ready_in_minutes || 30,
        cuisines: recipe.cuisine || [],
        diets: recipe.diets || [],
        image: getReliableImageUrl(recipe.image, 'medium'),
        added_at: Date.now() / 1000
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Error response:', {
        status: response.status,
        statusText: response.statusText,
        error: errorText
      });
      throw new Error(`Failed to create recipe: ${response.status} - ${response.statusText}`);
    }

    const data = await response.json();
    console.log('Successfully created manual recipe');
    
    // Return the created recipe in the expected format
    return {
      id: data.id,
      title: recipe.title || 'Untitled Recipe',
      description: recipe.description || '',
      ready_in_minutes: recipe.ready_in_minutes || 30,
      cuisine: recipe.cuisine || [],
      diets: recipe.diets || [],
      image: getReliableImageUrl(recipe.image, 'medium'),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
  } catch (error) {
    console.error('Error in createManualRecipe:', error);
    return null;
  }
};
