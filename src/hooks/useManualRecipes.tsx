
import { useQuery } from '@tanstack/react-query';
import { fetchManualRecipes } from '../lib/manualRecipes';

export const useManualRecipes = () => {
  return useQuery({
    queryKey: ['manual-recipes'],
    queryFn: fetchManualRecipes,
    retry: 1,
    staleTime: 60000
  });
};
