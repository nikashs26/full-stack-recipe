
// Update to use MongoDB backend instead of Supabase
const API_BASE_URL = "http://localhost:5003";

export interface ManualRecipe {
  id: string | number;
  title: string;
  description?: string;
  ready_in_minutes?: number;
  cuisine?: string[];
  diets?: string[];
  image?: string;
  created_at?: string;
  updated_at?: string;
}

// Fallback sample recipes when backend is empty
const SAMPLE_RECIPES: ManualRecipe[] = [
  {
    id: 'sample_1',
    title: 'Classic Spaghetti Carbonara',
    description: 'Authentic Italian pasta dish with eggs, cheese, pancetta, and black pepper. Creamy without using cream.',
    ready_in_minutes: 20,
    cuisine: ['Italian'],
    diets: [],
    image: 'https://www.recipetineats.com/wp-content/uploads/2019/05/Spaghetti-Carbonara_9.jpg',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: 'sample_2',
    title: 'Thai Green Curry',
    description: 'Aromatic Thai curry with green chilies, coconut milk, thai basil, and vegetables. Perfect balance of spicy and sweet.',
    ready_in_minutes: 30,
    cuisine: ['Thai', 'Asian'],
    diets: ['Vegetarian', 'Gluten-Free'],
    image: 'https://www.recipetineats.com/wp-content/uploads/2014/12/Thai-Green-Curry_1.jpg',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: 'sample_3',
    title: 'Beef Tacos',
    description: 'Delicious beef tacos with fresh toppings and warm tortillas. A classic Mexican favorite.',
    ready_in_minutes: 30,
    cuisine: ['Mexican'],
    diets: [],
    image: 'https://example.com/beef-tacos.jpg',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: 'sample_4',
    title: 'Chicken Tikka Masala',
    description: 'Creamy tomato-based curry with tender chicken pieces. A popular Indian restaurant dish.',
    ready_in_minutes: 45,
    cuisine: ['Indian'],
    diets: ['Gluten-Free'],
    image: 'https://www.recipetineats.com/wp-content/uploads/2019/01/Chicken-Tikka-Masala_9.jpg',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: 'sample_5',
    title: 'Caesar Salad',
    description: 'Classic Caesar salad with crisp romaine lettuce, parmesan cheese, and creamy dressing.',
    ready_in_minutes: 15,
    cuisine: ['American'],
    diets: ['Vegetarian'],
    image: 'https://natashaskitchen.com/wp-content/uploads/2019/01/Caesar-Salad-Recipe-3.jpg',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: 'sample_6',
    title: 'Margherita Pizza',
    description: 'Traditional Italian pizza with fresh mozzarella, basil, and tomato sauce on a crispy crust.',
    ready_in_minutes: 35,
    cuisine: ['Italian'],
    diets: ['Vegetarian'],
    image: 'https://www.recipetineats.com/wp-content/uploads/2020/05/Margherita-Pizza_9.jpg',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: 'sample_7',
    title: 'Greek Salad',
    description: 'Fresh Mediterranean salad with tomatoes, cucumber, olives, and feta cheese.',
    ready_in_minutes: 15,
    cuisine: ['Mediterranean', 'Greek'],
    diets: ['Vegetarian', 'Gluten-Free'],
    image: 'https://www.recipetineats.com/wp-content/uploads/2016/04/Greek-Salad_7.jpg',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: 'sample_8',
    title: 'BBQ Pulled Pork',
    description: 'Slow-cooked pulled pork with tangy BBQ sauce. Perfect for sandwiches or as a main dish.',
    ready_in_minutes: 480,
    cuisine: ['American'],
    diets: ['Gluten-Free'],
    image: 'https://www.recipetineats.com/wp-content/uploads/2017/05/Slow-Cooker-Pulled-Pork_9.jpg',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: 'sample_9',
    title: 'Vegetable Stir Fry',
    description: 'Quick and healthy stir fry with fresh vegetables and savory sauce.',
    ready_in_minutes: 20,
    cuisine: ['Asian', 'Chinese'],
    diets: ['Vegetarian', 'Vegan'],
    image: 'https://example.com/veggie-stir-fry.jpg',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: 'sample_10',
    title: 'Chocolate Chip Cookies',
    description: 'Classic homemade chocolate chip cookies that are crispy on the outside and soft on the inside.',
    ready_in_minutes: 25,
    cuisine: ['American'],
    diets: ['Vegetarian'],
    image: 'https://example.com/chocolate-chip-cookies.jpg',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }
];

export const fetchManualRecipes = async (): Promise<ManualRecipe[]> => {
  try {
    console.log('Fetching manual recipes from MongoDB backend...');
    const response = await fetch(`${API_BASE_URL}/recipes`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch recipes: ${response.status}`);
    }

    const data = await response.json();
    const recipes = data.results || [];
    
    // If we have recipes from the backend, use them
    if (recipes && recipes.length > 0) {
      // Transform MongoDB recipes to match the ManualRecipe interface
      const transformedRecipes = recipes.map((recipe: any) => ({
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
        diets: recipe.diets || [],
        image: recipe.image || '/placeholder.svg',
        created_at: recipe.added_at ? new Date(recipe.added_at * 1000).toISOString() : new Date().toISOString(),
        updated_at: recipe.added_at ? new Date(recipe.added_at * 1000).toISOString() : new Date().toISOString()
      }));

      console.log('Successfully fetched manual recipes from backend:', transformedRecipes.length);
      return transformedRecipes;
    } else {
      // If backend is empty, return sample recipes
      console.log('Backend returned empty recipes, using sample data');
      return SAMPLE_RECIPES;
    }
  } catch (error) {
    console.error('Error in fetchManualRecipes:', error);
    // Return sample recipes when backend fails
    console.log('Backend failed, using sample recipes');
    return SAMPLE_RECIPES;
  }
};

export const fetchManualRecipeById = async (id: number | string): Promise<ManualRecipe | null> => {
  try {
    console.log('Fetching manual recipe by ID:', id);
    const response = await fetch(`${API_BASE_URL}/recipes/${id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      throw new Error(`Failed to fetch recipe: ${response.status}`);
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
      diets: recipe.diets || [],
      image: recipe.image || '/placeholder.svg',
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
    const response = await fetch(`${API_BASE_URL}/recipes`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        title: recipe.title,
        summary: recipe.description,
        readyInMinutes: recipe.ready_in_minutes || 30,
        cuisines: recipe.cuisine || [],
        diets: recipe.diets || [],
        image: recipe.image || '/placeholder.svg',
        added_at: Date.now() / 1000
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to create recipe: ${response.status}`);
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
      image: recipe.image || '/placeholder.svg',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
  } catch (error) {
    console.error('Error in createManualRecipe:', error);
    return null;
  }
};
