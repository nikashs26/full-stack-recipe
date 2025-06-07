
import { supabase } from "@/integrations/supabase/client";
import { Database } from "@/integrations/supabase/types";

type ManualRecipe = Database['public']['Tables']['manual_recipes']['Row'];

export const fetchManualRecipes = async (): Promise<ManualRecipe[]> => {
  const { data, error } = await supabase
    .from('manual_recipes')
    .select('*')
    .order('created_at', { ascending: false });

  if (error) {
    console.error('Error fetching manual recipes:', error);
    throw error;
  }

  return data || [];
};

export const fetchManualRecipeById = async (id: number): Promise<ManualRecipe | null> => {
  const { data, error } = await supabase
    .from('manual_recipes')
    .select('*')
    .eq('id', id)
    .maybeSingle();

  if (error) {
    console.error('Error fetching manual recipe:', error);
    throw error;
  }

  return data;
};

export const createManualRecipe = async (recipe: Database['public']['Tables']['manual_recipes']['Insert']): Promise<ManualRecipe> => {
  const { data, error } = await supabase
    .from('manual_recipes')
    .insert(recipe)
    .select()
    .single();

  if (error) {
    console.error('Error creating manual recipe:', error);
    throw error;
  }

  return data;
};
