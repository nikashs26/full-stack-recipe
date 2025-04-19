import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Folder, Recipe } from '../types/recipe';
import FolderList from '../components/FolderList';
import RecipeList from '../components/RecipeList';
import { useToast } from '../components/ui/use-toast';
import { API_BASE_URL } from '../config';

const FoldersPage: React.FC = () => {
  const [selectedFolderId, setSelectedFolderId] = useState<string | null>(null);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Fetch folders
  const { data: folders = [] } = useQuery<Folder[]>({
    queryKey: ['folders'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/folders`);
      if (!response.ok) throw new Error('Failed to fetch folders');
      const data = await response.json();
      return data.folders;
    },
  });

  // Fetch recipes for selected folder
  const { data: folderRecipes = [] } = useQuery<Recipe[]>({
    queryKey: ['folder-recipes', selectedFolderId],
    queryFn: async () => {
      if (!selectedFolderId) return [];
      const response = await fetch(`${API_BASE_URL}/folders/${selectedFolderId}/recipes`);
      if (!response.ok) throw new Error('Failed to fetch folder recipes');
      const data = await response.json();
      return data.recipes;
    },
    enabled: !!selectedFolderId,
  });

  // Create folder mutation
  const createFolderMutation = useMutation({
    mutationFn: async ({ name, description }: { name: string; description?: string }) => {
      const response = await fetch(`${API_BASE_URL}/folders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description }),
      });
      if (!response.ok) throw new Error('Failed to create folder');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['folders'] });
      toast({
        title: 'Success',
        description: 'Folder created successfully',
      });
    },
    onError: (error) => {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  // Update folder mutation
  const updateFolderMutation = useMutation({
    mutationFn: async ({ id, name, description }: { id: string; name: string; description?: string }) => {
      const response = await fetch(`${API_BASE_URL}/folders/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description }),
      });
      if (!response.ok) throw new Error('Failed to update folder');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['folders'] });
      toast({
        title: 'Success',
        description: 'Folder updated successfully',
      });
    },
    onError: (error) => {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  // Delete folder mutation
  const deleteFolderMutation = useMutation({
    mutationFn: async (folderId: string) => {
      const response = await fetch(`${API_BASE_URL}/folders/${folderId}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Failed to delete folder');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['folders'] });
      if (selectedFolderId === folderId) {
        setSelectedFolderId(null);
      }
      toast({
        title: 'Success',
        description: 'Folder deleted successfully',
      });
    },
    onError: (error) => {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  const handleFolderCreate = (name: string, description?: string) => {
    createFolderMutation.mutate({ name, description });
  };

  const handleFolderUpdate = (folderId: string, name: string, description?: string) => {
    updateFolderMutation.mutate({ id: folderId, name, description });
  };

  const handleFolderDelete = (folderId: string) => {
    if (window.confirm('Are you sure you want to delete this folder? All recipes will be removed from the folder.')) {
      deleteFolderMutation.mutate(folderId);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1">
          <FolderList
            folders={folders}
            onFolderSelect={setSelectedFolderId}
            onFolderCreate={handleFolderCreate}
            onFolderUpdate={handleFolderUpdate}
            onFolderDelete={handleFolderDelete}
          />
        </div>
        <div className="lg:col-span-2">
          {selectedFolderId ? (
            <div>
              <h2 className="text-2xl font-bold mb-4">
                Recipes in {folders.find(f => f.id === selectedFolderId)?.name}
              </h2>
              <RecipeList recipes={folderRecipes} />
            </div>
          ) : (
            <div className="text-center text-muted-foreground py-8">
              Select a folder to view its recipes
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FoldersPage; 