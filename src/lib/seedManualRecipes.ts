
import { supabase } from "@/integrations/supabase/client";

export const checkAndSeedInitialRecipes = async () => {
  try {
    console.log('Checking for existing manual recipes...');
    
    // Check if any manual recipes exist
    const { data: existingRecipes, error: checkError } = await supabase
      .from('manual_recipes')
      .select('id')
      .limit(1);

    if (checkError) {
      console.error('Error checking existing recipes:', checkError);
      return;
    }

    // If recipes already exist, don't seed
    if (existingRecipes && existingRecipes.length > 0) {
      console.log('Manual recipes already exist, skipping seeding');
      return;
    }

    console.log('No manual recipes found, seeding initial recipes...');

    // Seed initial recipes
    const initialRecipes = [
      {
        title: 'Nashville Hot Chicken Sandwich',
        description: 'A spicy, crispy fried chicken sandwich with Nashville-style hot sauce, pickles, and coleslaw on a brioche bun. This sandwich packs serious heat with a perfect balance of flavors.',
        ready_in_minutes: 45,
        cuisine: ['American', 'Southern'],
        diets: ['None'],
        image: '/placeholder.svg'
      },
      {
        title: 'Authentic Pasta Carbonara',
        description: 'Classic Italian pasta dish with eggs, cheese, pancetta, and black pepper. Simple yet elegant, this Roman specialty is creamy without using cream.',
        ready_in_minutes: 20,
        cuisine: ['Italian'],
        diets: ['None'],
        image: '/placeholder.svg'
      },
      {
        title: 'Thai Green Curry',
        description: 'Aromatic Thai curry with green chilies, coconut milk, thai basil, and your choice of protein. A perfect balance of spicy, sweet, and savory flavors.',
        ready_in_minutes: 30,
        cuisine: ['Thai', 'Asian'],
        diets: ['Gluten-Free'],
        image: '/placeholder.svg'
      },
      {
        title: 'Classic Beef Burger',
        description: 'Juicy beef patty with lettuce, tomato, onion, and special sauce on a toasted sesame bun. The perfect comfort food classic.',
        ready_in_minutes: 25,
        cuisine: ['American'],
        diets: ['None'],
        image: '/placeholder.svg'
      },
      {
        title: 'Margherita Pizza',
        description: 'Traditional Italian pizza with fresh mozzarella, basil, and tomato sauce on a crispy thin crust. Simple ingredients, perfect execution.',
        ready_in_minutes: 35,
        cuisine: ['Italian'],
        diets: ['Vegetarian'],
        image: '/placeholder.svg'
      }
    ];

    const { data, error } = await supabase
      .from('manual_recipes')
      .insert(initialRecipes)
      .select();

    if (error) {
      console.error('Error seeding recipes:', error);
      throw error;
    } else {
      console.log('Successfully seeded initial recipes:', data?.length || 0);
      return data;
    }
  } catch (error) {
    console.error('Error in checkAndSeedInitialRecipes:', error);
    throw error;
  }
};
