
import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { v4 as uuidv4 } from 'uuid';
import { Folder, Recipe } from '../types/recipe';
import Header from '../components/Header';
import FolderList from '../components/FolderList';
import { toast } from '@/components/ui/use-toast';
import { loadRecipes, saveRecipes, getLocalRecipes } from '../utils/storage';

const FoldersPage: React.FC = () => {
  const [folders, setFolders] = useState<Folder[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<Folder | null>(null);
  const queryClient = useQueryClient();

  // Fetch recipes
  const { data: recipes = [] } = useQuery({
    queryKey: ['recipes'],
    queryFn: loadRecipes
  });

  // Load folders from localStorage
  useEffect(() => {
    const loadFolders = () => {
      try {
        const storedFolders = localStorage.getItem('recipe-folders');
        return storedFolders ? JSON.parse(storedFolders) : [];
      } catch (error) {
        console.error('Failed to load folders:', error);
        return [];
      }
    };
    
    setFolders(loadFolders());
  }, []);

  // Save folders to localStorage
  const saveFolders = (updatedFolders: Folder[]) => {
    try {
      localStorage.setItem('recipe-folders', JSON.stringify(updatedFolders));
      setFolders(updatedFolders);
    } catch (error) {
      console.error('Failed to save folders:', error);
    }
  };

  // Create folder
  const handleCreateFolder = (name: string, description?: string) => {
    const newFolder: Folder = {
      id: uuidv4(),
      name,
      description,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    
    const updatedFolders = [...folders, newFolder];
    saveFolders(updatedFolders);
    toast({
      title: "Success",
      description: `Folder "${name}" created successfully`,
    });
  };

  // Update folder
  const handleUpdateFolder = (folderId: string, name: string, description?: string) => {
    const updatedFolders = folders.map(folder => 
      folder.id === folderId 
        ? { ...folder, name, description, updatedAt: new Date().toISOString() } 
        : folder
    );
    
    saveFolders(updatedFolders);
    toast({
      title: "Success",
      description: `Folder "${name}" updated successfully`,
    });
  };

  // Delete folder
  const handleDeleteFolder = (folderId: string) => {
    // Find folder to be deleted to show its name in the toast
    const folderToDelete = folders.find(folder => folder.id === folderId);
    
    // Update recipes to remove the folder reference
    const updatedRecipes = recipes.map((recipe: Recipe) => 
      recipe.folderId === folderId 
        ? { ...recipe, folderId: undefined }
        : recipe
    );
    
    // Remove folder from folders list
    const updatedFolders = folders.filter(folder => folder.id !== folderId);
    
    saveRecipes(updatedRecipes);
    saveFolders(updatedFolders);
    
    // Invalidate queries to refresh data
    queryClient.invalidateQueries({ queryKey: ['recipes'] });
    
    toast({
      title: "Success",
      description: `Folder "${folderToDelete?.name}" deleted successfully`,
    });
  };

  // Select folder to view its recipes
  const handleFolderSelect = (folderId: string) => {
    const folder = folders.find(f => f.id === folderId);
    if (folder) {
      setSelectedFolder(folder);
    }
  };

  // Get recipes assigned to selected folder
  const folderRecipes = selectedFolder 
    ? recipes.filter((recipe: Recipe) => recipe.folderId === selectedFolder.id)
    : [];

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="pt-24 md:pt-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="bg-white shadow-sm rounded-lg p-6">
            <FolderList 
              folders={folders}
              onFolderSelect={handleFolderSelect}
              onFolderCreate={handleCreateFolder}
              onFolderUpdate={handleUpdateFolder}
              onFolderDelete={handleDeleteFolder}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default FoldersPage;
