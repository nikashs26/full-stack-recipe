
import { supabase } from '@/integrations/supabase/client';
import { Database } from '@/integrations/supabase/types';

export type ManualRecipe = Database['public']['Tables']['manual_recipes']['Row'];

export const fetchManualRecipes = async (): Promise<ManualRecipe[]> => {
  try {
    const { data, error } = await supabase
      .from('manual_recipes')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) {
      console.error('Error fetching manual recipes:', error);
      throw error;
    }

    return data || [];
  } catch (error) {
    console.error('Failed to fetch manual recipes:', error);
    return [];
  }
};

export const insertManualRecipe = async (recipe: Omit<ManualRecipe, 'id' | 'created_at' | 'updated_at'>) => {
  try {
    const { data, error } = await supabase
      .from('manual_recipes')
      .insert([recipe])
      .select()
      .single();

    if (error) {
      console.error('Error inserting manual recipe:', error);
      throw error;
    }

    return data;
  } catch (error) {
    console.error('Failed to insert manual recipe:', error);
    throw error;
  }
};
