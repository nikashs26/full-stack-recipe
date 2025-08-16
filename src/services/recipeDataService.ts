import { Recipe } from '../types/recipe';

/**
 * Shared service for consistent recipe data processing across the application
 * This ensures that homepage and search page show the same recipe data
 */

export interface NormalizedRecipe {
  id: string | number;
  title: string;
  description?: string;
  image: string;
  cuisines: string[];
  diets: string[];
  ingredients: Array<{
    name: string;
    amount?: string | number;
    unit?: string;
  }>;
  instructions: string[];
  ready_in_minutes?: number;
  nutrition?: {
    calories?: number;
    protein?: number;
    carbs?: number;
    fat?: number;
    fiber?: number;
  };
  source?: string;
  type?: 'external' | 'manual' | 'saved';
}

/**
 * Normalize recipe data from backend to consistent format
 * This is the same logic used in fetchManualRecipes to ensure consistency
 */
export function normalizeRecipeData(recipe: any): NormalizedRecipe {
  // Normalize dietary restrictions
  let diets: string[] = [];
  if (Array.isArray(recipe.diets)) {
    diets = recipe.diets
      .map((d: any) => (typeof d === 'string' ? d.trim().toLowerCase() : ''))
      .filter(Boolean);
  } else if (typeof recipe.diets === 'string' && recipe.diets.trim()) {
    diets = recipe.diets.split(',').map(d => d.trim().toLowerCase()).filter(Boolean);
  }
  
  // Also check dietary_restrictions field
  if (Array.isArray(recipe.dietary_restrictions)) {
    const restrictions = recipe.dietary_restrictions
      .map((d: any) => (typeof d === 'string' ? d.trim().toLowerCase() : ''))
      .filter(Boolean);
    diets = [...new Set([...diets, ...restrictions])];
  }
  
  // Normalize cuisines
  let cuisines: string[] = [];
  if (recipe.cuisines) {
    if (Array.isArray(recipe.cuisines)) {
      cuisines = recipe.cuisines
        .map((c: any) => typeof c === 'string' ? c.trim() : '')
        .filter(Boolean);
    } else if (typeof recipe.cuisines === 'string' && recipe.cuisines.trim()) {
      cuisines = [recipe.cuisines.trim()];
    }
  }
  
  // If no cuisines found, try the cuisine field
  if (cuisines.length === 0 && recipe.cuisine) {
    if (Array.isArray(recipe.cuisine)) {
      cuisines = recipe.cuisine
        .map((c: any) => typeof c === 'string' ? c.trim() : '')
        .filter(Boolean);
    } else if (typeof recipe.cuisine === 'string' && recipe.cuisine.trim()) {
      cuisines = [recipe.cuisine.trim()];
    }
  }
  
  // Handle image URL
  let imageUrl = '';
  if (recipe.image) {
    imageUrl = recipe.image;
  } else if (recipe.imageUrl) {
    imageUrl = recipe.imageUrl;
  } else if (recipe.source === 'themealdb' && recipe.id) {
    const recipeName = recipe.title ? recipe.title.replace(/\s+/g, '%20') : '';
    imageUrl = `https://www.themealdb.com/images/ingredients/${recipeName}.png`;
  } else {
    imageUrl = 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?auto=format&fit=crop&w=400&h=300&q=80';
  }
  
  // Normalize ingredients
  const ingredients = Array.isArray(recipe.ingredients) 
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
    : [];
  
  // Normalize instructions
  const instructions = Array.isArray(recipe.instructions) 
    ? recipe.instructions
    : recipe.instructions 
    ? [recipe.instructions]
    : recipe.analyzedInstructions && Array.isArray(recipe.analyzedInstructions)
    ? recipe.analyzedInstructions.flatMap((section: any) => 
        section.steps?.map((step: any) => step.step).filter(Boolean) || []
      )
    : [];
  
  return {
    id: recipe.id || recipe._id || `recipe-${Math.random().toString(36).substr(2, 9)}`,
    title: recipe.title || 'Untitled Recipe',
    description: recipe.summary || recipe.description || '',
    image: imageUrl,
    cuisines: cuisines.length > 0 ? cuisines : [],
    diets: diets,
    ingredients: ingredients,
    instructions: instructions,
    ready_in_minutes: recipe.ready_in_minutes || recipe.readyInMinutes || 30,
    nutrition: recipe.nutrition || {},
    source: recipe.source || 'unknown',
    type: recipe.type || 'external'
  };
}

/**
 * Fetch and normalize recipes from backend
 * This ensures consistent data processing across the app
 */
export async function fetchNormalizedRecipes(
  query: string = '', 
  ingredient: string = '', 
  options: {
    page?: number;
    pageSize?: number;
    cuisines?: string[];
    diets?: string[];
  } = {}
): Promise<{ recipes: NormalizedRecipe[]; total: number }> {
  try {
    const params = new URLSearchParams();
    
    // Handle search query and ingredient
    const queryStr = typeof query === 'string' ? query.trim() : '';
    const ingredientStr = typeof ingredient === 'string' ? ingredient.trim() : '';
    // Always send both parameters to ensure backend can properly determine search type
    // Even if empty, the backend needs to know whether to do name search, ingredient search, or combined search
    params.append('query', queryStr);
    params.append('ingredient', ingredientStr);
    
    // Handle pagination
    const page = options.page || 1;
    const pageSize = options.pageSize || 20;
    const offset = (page - 1) * pageSize;
    params.append('offset', String(offset));
    params.append('limit', String(pageSize));
    
    // Handle cuisines filter
    if (options.cuisines?.length) {
      params.append('cuisine', options.cuisines.join(','));
    }
    
    // Handle diets filter
    if (options.diets?.length) {
      const mappedDiets = options.diets.map(diet => {
        const lowerDiet = diet.toLowerCase();
        if (lowerDiet === 'vegetarian') return 'vegetarian';
        if (lowerDiet === 'vegan') return 'vegan';
        if (lowerDiet === 'gluten-free') return 'gluten free';
        if (lowerDiet === 'dairy-free') return 'dairy free';
        return diet;
      });
      
      const dietParam = mappedDiets.join(',');
      if (dietParam) {
        params.append('dietary_restrictions', dietParam);
      }
    }
    
    const queryString = params.toString();
    const url = `http://localhost:5003/get_recipes${queryString ? `?${queryString}` : ''}`;
    
    console.log('Fetching normalized recipes from:', url);
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });
    
    if (!response.ok) {
      if (response.status === 404) {
        console.log('No recipes found for query');
        return { recipes: [], total: 0 };
      }
      throw new Error(`Error ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log('Received data from backend:', data);
    
    // Handle different response formats
    let recipes: any[] = [];
    let total = 0;
    
    if (data && data.results && data.total !== undefined) {
      recipes = data.results;
      total = data.total;
    } else if (Array.isArray(data)) {
      recipes = data;
      total = data.length;
    } else if (data && Array.isArray(data.results)) {
      recipes = data.results;
      total = data.total || data.results.length;
    } else if (data && data.recipes && Array.isArray(data.recipes)) {
      recipes = data.recipes;
      total = data.total || data.recipes.length;
    }
    
    if (recipes.length > 0) {
      // Normalize all recipes using the shared logic
      const normalizedRecipes = recipes.map(normalizeRecipeData);
      
      return {
        recipes: normalizedRecipes,
        total: total
      };
    }
    
    return { recipes: [], total: 0 };
    
  } catch (error) {
    console.error('Error fetching normalized recipes:', error);
    return { recipes: [], total: 0 };
  }
}

/**
 * Get quality-based recipes using normalized data
 * This replaces the old getQualityBasedRecipes function
 */
export async function getQualityBasedRecipesNormalized(limit: number = 4): Promise<NormalizedRecipe[]> {
  try {
    console.log('🔍 Fetching quality-based recipes with normalized data...');
    
    const { recipes } = await fetchNormalizedRecipes('', '', { pageSize: 100 }); // Get more recipes for selection
    
    if (recipes.length === 0) {
      console.log('No recipes available for quality selection');
      return [];
    }
    
    // Score recipes based on quality indicators
    const scoredRecipes = recipes.map(recipe => {
      let score = 0;
      
      // Recipe completeness score (0-30 points)
      if (recipe.title) score += 10;
      if (recipe.description && recipe.description.length > 50) score += 5;
      if (recipe.ingredients && recipe.ingredients.length >= 5) score += 10;
      if (recipe.instructions && recipe.instructions.length > 100) score += 5;
      
      // Image quality score (0-20 points)
      if (recipe.image && recipe.image !== 'placeholder') score += 20;
      
      // Nutritional info score (0-25 points)
      if (recipe.nutrition) {
        if (recipe.nutrition.calories) score += 5;
        if (recipe.nutrition.protein) score += 5;
        if (recipe.nutrition.carbs) score += 5;
        if (recipe.nutrition.fat) score += 5;
        if (recipe.nutrition.fiber) score += 5;
      }
      
      // Recipe type diversity bonus (0-15 points)
      if (recipe.cuisines && recipe.cuisines.length > 0) score += 10;
      if (recipe.diets && recipe.diets.length > 0) score += 5;
      
      return { ...recipe, qualityScore: score };
    });
    
    // Sort by quality score and ensure diversity
    const sortedByQuality = scoredRecipes.sort((a, b) => b.qualityScore - a.qualityScore);
    
    // Select diverse recipes (different cuisines)
    const selectedRecipes: NormalizedRecipe[] = [];
    const selectedCuisines = new Set<string>();
    
    for (const recipe of sortedByQuality) {
      if (selectedRecipes.length >= limit) break;
      
      // Check if we already have a recipe from this cuisine
      const hasCuisine = recipe.cuisines.some(cuisine => selectedCuisines.has(cuisine));
      
      if (!hasCuisine || selectedRecipes.length < limit / 2) {
        selectedRecipes.push(recipe);
        recipe.cuisines.forEach(cuisine => selectedCuisines.add(cuisine));
      }
    }
    
    // If we still don't have enough recipes, add more from the top
    if (selectedRecipes.length < limit) {
      for (const recipe of sortedByQuality) {
        if (selectedRecipes.length >= limit) break;
        if (!selectedRecipes.find(r => r.id === recipe.id)) {
          selectedRecipes.push(recipe);
        }
      }
    }
    
    console.log(`✅ Selected ${selectedRecipes.length} quality-based recipes`);
    return selectedRecipes.slice(0, limit);
    
  } catch (error) {
    console.error('Error getting quality-based recipes:', error);
    return [];
  }
}
