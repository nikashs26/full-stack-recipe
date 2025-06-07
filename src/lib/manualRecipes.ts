
import { supabase } from "@/integrations/supabase/client";
import { Database } from "@/integrations/supabase/types";

type ManualRecipe = Database['public']['Tables']['manual_recipes']['Row'];

export const fetchManualRecipes = async (): Promise<ManualRecipe[]> => {
  try {
    console.log('Fetching manual recipes from Supabase...');
    const { data, error } = await supabase
      .from('manual_recipes')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) {
      console.error('Error fetching manual recipes:', error);
      throw error;
    }

    console.log('Successfully fetched manual recipes:', data?.length || 0);
    return data || [];
  } catch (error) {
    console.error('Error in fetchManualRecipes:', error);
    throw error;
  }
};

export const fetchManualRecipeById = async (id: number): Promise<ManualRecipe | null> => {
  try {
    console.log('Fetching manual recipe by ID:', id);
    const { data, error } = await supabase
      .from('manual_recipes')
      .select('*')
      .eq('id', id)
      .maybeSingle();

    if (error) {
      console.error('Error fetching manual recipe:', error);
      throw error;
    }

    console.log('Successfully fetched manual recipe:', data?.title);
    return data;
  } catch (error) {
    console.error('Error in fetchManualRecipeById:', error);
    throw error;
  }
};

export const createManualRecipe = async (recipe: Database['public']['Tables']['manual_recipes']['Insert']): Promise<ManualRecipe> => {
  try {
    console.log('Creating manual recipe:', recipe.title);
    const { data, error } = await supabase
      .from('manual_recipes')
      .insert(recipe)
      .select()
      .single();

    if (error) {
      console.error('Error creating manual recipe:', error);
      throw error;
    }

    console.log('Successfully created manual recipe:', data.title);
    return data;
  } catch (error) {
    console.error('Error in createManualRecipe:', error);
    throw error;
  }
};
