
import { createManualRecipe } from './manualRecipes';

export const seedNashvilleHotChicken = async () => {
  try {
    const nashvilleRecipe = {
      title: "Nashville Hot Chicken Sandwich",
      description: "A fiery, crispy fried chicken sandwich with Nashville-style hot seasoning, served on a brioche bun with pickles and coleslaw.",
      image: "https://images.unsplash.com/photo-1594212699903-ec8a3eca50f5?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80",
      cuisine: ["American", "Southern"],
      diets: ["high-protein"],
      ready_in_minutes: 45
    };

    const result = await createManualRecipe(nashvilleRecipe);
    console.log('Nashville hot chicken sandwich added:', result);
    return result;
  } catch (error) {
    console.error('Error seeding Nashville recipe:', error);
    throw error;
  }
};

// Function to check if we should seed data
export const checkAndSeedInitialRecipes = async () => {
  try {
    const { fetchManualRecipes } = await import('./manualRecipes');
    const existingRecipes = await fetchManualRecipes();
    
    // If no recipes exist, seed the Nashville hot chicken
    if (existingRecipes.length === 0) {
      await seedNashvilleHotChicken();
      console.log('Initial manual recipes seeded');
    }
  } catch (error) {
    console.error('Error checking/seeding recipes:', error);
  }
};
