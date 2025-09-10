
import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Folder, Recipe } from '../types/recipe';
import Header from '../components/Header';
import FolderList from '../components/FolderList';
import { toast } from '@/components/ui/use-toast';
import { useAuth } from '../context/AuthContext';
import { apiCall } from '../utils/apiUtils';

const FoldersPage: React.FC = () => {
  const [folders, setFolders] = useState<Folder[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<Folder | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const queryClient = useQueryClient();
  const { isAuthenticated, token } = useAuth();

  // Fetch folders from backend
  const { data: backendFolders = [], refetch: refetchFolders } = useQuery({
    queryKey: ['backend-folders'],
    queryFn: async () => {
      if (!isAuthenticated) {
        throw new Error('Please sign in to access folders');
      }
      
              const response = await apiCall('/api/folders');
      if (!response.ok) {
        throw new Error('Failed to fetch folders');
      }
      
      const foldersData = await response.json();
      
      // Transform backend folder format to frontend format
      return foldersData.map((folder: any) => ({
        id: folder.folder_id || folder.id,
        name: folder.name,
        description: folder.description,
        createdAt: folder.created_at,
        updatedAt: folder.updated_at,
        recipe_count: folder.recipe_count || 0
      }));
    },
    enabled: isAuthenticated,
    retry: false
  });

  // Fetch recipes for a specific folder
  const { data: folderRecipesData = [], refetch: refetchFolderRecipes } = useQuery({
    queryKey: ['folder-recipes', selectedFolder?.id],
    queryFn: async () => {
      if (!selectedFolder || !isAuthenticated) {
        return [];
      }
      
      try {
        const response = await apiCall(`/api/folders/${selectedFolder.id}`);
        if (!response.ok) {
          throw new Error('Failed to fetch folder contents');
        }
        
        const folderData = await response.json();
        console.log('Folder data from backend:', folderData);
        
        // Transform backend recipe items to frontend format
        const recipes = (folderData.items || []).map((item: any) => {
          const recipeData = item.recipe_data || {};
          console.log('Processing recipe data:', recipeData);
          console.log('Recipe data keys:', Object.keys(recipeData));
          
            // Helper function to get value from multiple possible field names
            const getFieldValue = (fieldNames: string[], fallback?: any) => {
              for (const fieldName of fieldNames) {
                if (recipeData[fieldName] !== undefined && recipeData[fieldName] !== null) {
                  return recipeData[fieldName];
                }
              }
              return fallback;
            };
            
            // Helper function to get nested field value
            const getNestedFieldValue = (fieldPath: string, fallback?: any) => {
              const parts = fieldPath.split('.');
              let value = recipeData;
              for (const part of parts) {
                if (value && typeof value === 'object' && part in value) {
                  value = value[part];
                } else {
                  return fallback;
                }
              }
              return value !== undefined && value !== null ? value : fallback;
            };
            
            // Debug: Log the actual recipe data structure
            console.log('Recipe data structure for item:', {
              recipeId: item.recipe_id,
              recipeType: item.recipe_type,
              availableKeys: Object.keys(recipeData),
              nameValue: recipeData.name,
              titleValue: recipeData.title,
              descriptionValue: recipeData.description,
              summaryValue: recipeData.summary,
              strMeal: recipeData.strMeal,
              strArea: recipeData.strArea,
              strCategory: recipeData.strCategory,
              rawRecipeData: recipeData
            });
            
            // Enhanced field mapping with more comprehensive fallbacks
            let recipeName = getFieldValue([
              'name', 'title', 'strMeal', 'recipeName', 'recipe_name', 'recipe_title'
            ], '');
            
            // If no name found, try to extract from other fields or generate a descriptive name
            if (!recipeName) {
              // Try to get cuisine or type to create a descriptive name
              const cuisine = getFieldValue(['cuisine', 'cuisines.0', 'strArea'], '');
              const type = getFieldValue(['type', 'category', 'strCategory'], '');
              
              if (cuisine && type) {
                recipeName = `${cuisine} ${type}`;
              } else if (cuisine) {
                recipeName = `${cuisine} Recipe`;
              } else if (type) {
                recipeName = `${type} Recipe`;
              } else {
                recipeName = 'Untitled Recipe';
              }
            }
            
            const recipeDescription = getFieldValue([
              'description', 'summary', 'strInstructions', 'instructions', 'strDescription'
            ], '') || `A delicious ${recipeName.toLowerCase()} recipe.`;
            
            const recipeImage = getFieldValue([
              'image', 'imageUrl', 'strMealThumb', 'strMealThumbnail', 'thumbnail', 'photo'
            ], '');
            
            const recipeIngredients = recipeData.ingredients || 
                                    recipeData.extendedIngredients || 
                                    recipeData.strIngredients || 
                                    [];
            
            const recipeInstructions = recipeData.instructions || 
                                     recipeData.strInstructions || 
                                     recipeData.directions || 
                                     [];
            
            let recipeCuisines = recipeData.cuisines || 
                                recipeData.cuisine || 
                                recipeData.strArea || 
                                [];
            
            // Convert single cuisine to array if needed
            if (typeof recipeCuisines === 'string') {
              recipeCuisines = [recipeCuisines];
            } else if (!Array.isArray(recipeCuisines)) {
              recipeCuisines = [];
            }
          
          return {
            id: item.recipe_id || item.id,
            name: recipeName,
            title: recipeName,
            description: recipeDescription,
            image: recipeImage,
            ingredients: recipeIngredients,
            instructions: recipeInstructions,
            cuisine: Array.isArray(recipeCuisines) ? recipeCuisines[0] : recipeCuisines,
            cuisines: recipeCuisines,
            dietaryRestrictions: recipeData.dietaryRestrictions || 
                               recipeData.diets || 
                               recipeData.strTags || 
                               [],
            servings: recipeData.servings || recipeData.strServings || 4,
            
            // Time fields with comprehensive fallbacks
            prepTime: getFieldValue([
              'prepTime', 'prep_time', 'preparationMinutes', 'strPrepTime', 'prepTimeMinutes'
            ], undefined),
            cookTime: getFieldValue([
              'cookTime', 'cook_time', 'cookingMinutes', 'strCookTime', 'cookTimeMinutes'
            ], undefined),
            totalTime: getFieldValue([
              'totalTime', 'total_time', 'totalMinutes', 'strTotalTime', 'readyInMinutes', 'ready_in_minutes'
            ], undefined),
            readyInMinutes: getFieldValue([
              'readyInMinutes', 'ready_in_minutes', 'totalTime', 'total_time', 'strTotalTime', 'strPrepTime'
            ], undefined),
            
            difficulty: recipeData.difficulty || recipeData.strDifficulty || 'medium',
            nutrition: recipeData.nutrition || {},
            macrosPerServing: recipeData.macrosPerServing || recipeData.macros || {},
            
            // Rating fields with comprehensive fallbacks
            rating: getFieldValue([
              'rating', 'score', 'strRating', 'averageRating', 'avgRating'
            ], undefined),
            ratings: getFieldValue([
              'ratings', 'scores', 'ratingCount', 'reviewCount'
            ], undefined),
            averageRating: getFieldValue([
              'averageRating', 'avgRating', 'rating', 'score', 'strRating'
            ], undefined),
            reviewCount: getFieldValue([
              'reviewCount', 'ratingCount', 'ratings'
            ], 0),
            
            isFavorite: recipeData.isFavorite || false,
            folderId: selectedFolder.id,
            createdAt: item.added_at,
            updatedAt: item.added_at,
            type: item.recipe_type || 'manual',
            
            // Additional fields that might exist
            source: recipeData.source || recipeData.strSource || '',
            sourceUrl: recipeData.sourceUrl || recipeData.strSource || '',
            summary: recipeData.summary || recipeData.description || '',
            calories: getFieldValue([
              'calories', 'nutrition.calories', 'strCalories', 'energy'
            ], undefined),
            protein: getFieldValue([
              'protein', 'nutrition.protein', 'strProtein', 'macros.protein'
            ], undefined),
            carbs: getFieldValue([
              'carbs', 'nutrition.carbs', 'nutrition.carbohydrates', 'strCarbs', 'macros.carbs'
            ], undefined),
            fat: getFieldValue([
              'fat', 'nutrition.fat', 'strFat', 'macros.fat'
            ], undefined)
          };
        });
        
        console.log('Transformed recipes:', recipes);
        console.log('Raw recipe data from backend:', folderData);
        console.log('Sample recipe item structure:', folderData?.items?.[0]);
        return recipes;
      } catch (error) {
        console.error('Error fetching folder recipes:', error);
        return [];
      }
    },
    enabled: !!selectedFolder && isAuthenticated,
  });

  // Fetch recipes
  const { data: recipes = [] } = useQuery({
    queryKey: ['recipes'],
    queryFn: async () => {
      // This should fetch from your backend recipe endpoint
      // For now, using empty array as placeholder
      return [];
    }
  });

  // Update local state when backend data changes
  useEffect(() => {
    if (backendFolders) {
      setFolders(backendFolders);
      setIsLoading(false);
    }
  }, [backendFolders]);

  // Create folder using backend API
  const handleCreateFolder = async (name: string, description?: string) => {
    if (!isAuthenticated) {
      toast({
        title: "Error",
        description: "Please sign in to create folders",
        variant: "destructive"
      });
      return;
    }

    try {
              const response = await apiCall('/api/folders', {
        method: 'POST',
        body: JSON.stringify({
          name: name.trim(),
          description: description?.trim() || 'My recipe collection',
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to create folder');
      }

      const newFolder = await response.json();
      
      // Transform to frontend format
      const transformedFolder: Folder = {
        id: newFolder.folder_id || newFolder.id,
        name: newFolder.name,
        description: newFolder.description,
        createdAt: newFolder.created_at,
        updatedAt: newFolder.updated_at,
        recipe_count: newFolder.recipe_count || 0
      };

      // Add to local state
      setFolders(prev => [...prev, transformedFolder]);
      
      // Refetch folders to ensure consistency
      refetchFolders();
      
      toast({
        title: "Success",
        description: `Folder "${name}" created successfully`,
      });
    } catch (error) {
      console.error('Error creating folder:', error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : 'Failed to create folder',
        variant: "destructive"
      });
    }
  };

  // Update folder using backend API
  const handleUpdateFolder = async (folderId: string, name: string, description?: string) => {
    if (!isAuthenticated) {
      toast({
        title: "Error",
        description: "Please sign in to update folders",
        variant: "destructive"
      });
      return;
    }

    try {
      const response = await apiCall(`/api/folders/${folderId}`, {
        method: 'PUT',
        body: JSON.stringify({
          name: name.trim(),
          description: description?.trim() || '',
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to update folder');
      }

      const updatedFolder = await response.json();
      
      // Transform to frontend format
      const transformedFolder: Folder = {
        id: updatedFolder.folder_id || updatedFolder.id,
        name: updatedFolder.name,
        description: updatedFolder.description,
        createdAt: updatedFolder.created_at,
        updatedAt: updatedFolder.updated_at,
        recipe_count: updatedFolder.recipe_count || 0
      };

      // Update local state
      setFolders(prev => prev.map(folder => 
        folder.id === folderId ? transformedFolder : folder
      ));
      
      // Refetch folders to ensure consistency
      refetchFolders();
      
      toast({
        title: "Success",
        description: `Folder "${name}" updated successfully`,
      });
    } catch (error) {
      console.error('Error updating folder:', error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : 'Failed to update folder',
        variant: "destructive"
      });
    }
  };

  // Delete folder using backend API
  const handleDeleteFolder = async (folderId: string) => {
    if (!isAuthenticated) {
      toast({
        title: "Error",
        description: "Please sign in to delete folders",
        variant: "destructive"
      });
      return;
    }

    // Find folder to be deleted to show its name in the toast
    const folderToDelete = folders.find(folder => folder.id === folderId);
    
    try {
      const response = await apiCall(`/api/folders/${folderId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to delete folder');
      }

      // Remove folder from local state
      setFolders(prev => prev.filter(folder => folder.id !== folderId));
      
      // Refetch folders to ensure consistency
      refetchFolders();
      
      toast({
        title: "Success",
        description: `Folder "${folderToDelete?.name}" deleted successfully`,
      });
    } catch (error) {
      console.error('Error deleting folder:', error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : 'Failed to delete folder',
        variant: "destructive"
      });
    }
  };

  // Select folder to view its recipes
  const handleFolderSelect = (folderId: string) => {
    const folder = folders.find(f => f.id === folderId);
    if (folder) {
      setSelectedFolder(folder);
    }
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="pt-24 md:pt-28">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="bg-white shadow-sm rounded-lg p-6">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
                <p className="mt-2 text-gray-600">Loading folders...</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show sign-in prompt if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="pt-24 md:pt-28">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="bg-white shadow-sm rounded-lg p-6 text-center">
              <h2 className="text-xl font-semibold mb-2">Sign In Required</h2>
              <p className="text-gray-600 mb-4">Please sign in to access your recipe folders.</p>
              <button 
                onClick={() => window.location.href = '/signin'}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
              >
                Sign In
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

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
              selectedFolder={selectedFolder}
              folderRecipes={folderRecipesData}
              onCloseFolder={() => setSelectedFolder(null)}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default FoldersPage;
