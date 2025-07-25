// List of valid cuisines from UserPreferencesPage
const validCuisines = [
  'italian', 'mexican', 'indian', 'chinese', 'japanese',
  'thai', 'mediterranean', 'french', 'greek', 'spanish',
  'korean', 'vietnamese', 'american', 'british', 'irish',
  'caribbean', 'moroccan'
];

// List of valid dietary restrictions from UserPreferencesPage
const validDietaryRestrictions = [
  'vegetarian', 'vegan', 'gluten-free', 'dairy-free', 'keto', 'paleo'
];

// List of valid allergens from UserPreferencesPage
const validAllergens = [
  'nuts', 'shellfish', 'dairy', 'eggs', 'soy', 'wheat'
];

/**
 * Normalize and validate cuisine tags
 */
export const normalizeCuisines = (cuisines: any[] | undefined): string[] => {
  if (!cuisines || !Array.isArray(cuisines)) return [];
  
  return cuisines
    .map(cuisine => {
      if (typeof cuisine === 'string') {
        // Convert to lowercase and trim
        const normalized = cuisine.toLowerCase().trim();
        // Check if it's a valid cuisine
        return validCuisines.includes(normalized) ? normalized : null;
      }
      return null;
    })
    .filter((cuisine): cuisine is string => cuisine !== null);
};

/**
 * Normalize and validate dietary restrictions
 */
export const normalizeDietaryRestrictions = (restrictions: any[] | undefined): string[] => {
  if (!restrictions || !Array.isArray(restrictions)) return [];
  
  return restrictions
    .map(restriction => {
      if (typeof restriction === 'string') {
        // Convert to lowercase and trim
        const normalized = restriction.toLowerCase().trim();
        // Check if it's a valid dietary restriction
        return validDietaryRestrictions.includes(normalized) ? normalized : null;
      }
      return null;
    })
    .filter((restriction): restriction is string => restriction !== null);
};

/**
 * Normalize and validate allergens
 */
export const normalizeAllergens = (allergens: any[] | undefined): string[] => {
  if (!allergens || !Array.isArray(allergens)) return [];
  
  return allergens
    .map(allergen => {
      if (typeof allergen === 'string') {
        // Convert to lowercase and trim
        const normalized = allergen.toLowerCase().trim();
        // Check if it's a valid allergen
        return validAllergens.includes(normalized) ? normalized : null;
      }
      return null;
    })
    .filter((allergen): allergen is string => allergen !== null);
};

/**
 * Normalize a recipe's tags to ensure they match the allowed values
 */
export const normalizeRecipeTags = (recipe: any) => {
  if (!recipe) return recipe;
  
  return {
    ...recipe,
    cuisines: normalizeCuisines(recipe.cuisines),
    dietaryRestrictions: normalizeDietaryRestrictions(recipe.dietaryRestrictions || recipe.diets),
    allergens: normalizeAllergens(recipe.allergens)
  };
};

export const getValidCuisines = () => [...validCuisines];
export const getValidDietaryRestrictions = () => [...validDietaryRestrictions];
export const getValidAllergens = () => [...validAllergens];
