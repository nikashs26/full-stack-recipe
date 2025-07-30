import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import * as DialogPrimitive from '@radix-ui/react-dialog';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger, 
  DialogDescription,
  DialogOverlay,
  DialogPortal
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';
import { FolderPlus, Folder, Loader2, Check } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

interface Folder {
  id: string;
  name: string;
  description?: string;
  recipe_count: number;
}

interface RecipeFolderActionsProps {
  recipeId: string;
  recipeType: 'local' | 'external' | 'manual';
  recipeData: any;
}

export function RecipeFolderActions({ recipeId, recipeType, recipeData }: RecipeFolderActionsProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [folders, setFolders] = useState<Folder[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [newFolderName, setNewFolderName] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [foldersWithRecipe, setFoldersWithRecipe] = useState<Set<string>>(new Set());
  const { toast } = useToast();
  const { token, isAuthenticated } = useAuth();

  // Fetch user's folders and check which ones contain the current recipe
  useEffect(() => {
    const fetchFoldersAndRecipeStatus = async () => {
      if (!isOpen) return;
      
      try {
        if (!isAuthenticated || !token) {
          throw new Error('Please sign in to access folders');
        }
        
        console.log('Starting to fetch folders and recipe status...');
        setIsLoading(true);
        
        // Fetch folders
        console.log('Fetching folders from API...');
        const [foldersResponse, recipeFoldersResponse] = await Promise.all([
          fetch('http://localhost:5003/api/folders', {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            credentials: 'include',
          }),
          fetch(`http://localhost:5003/api/recipes/${recipeType}/${recipeId}/folders`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            credentials: 'include',
          })
        ]);
        
        console.log('Folders response status:', foldersResponse.status);
        console.log('Recipe folders response status:', recipeFoldersResponse.status);
        
        // Handle folders response
        if (!foldersResponse.ok) {
          const errorText = await foldersResponse.text();
          console.error('Folders API error:', {
            status: foldersResponse.status,
            statusText: foldersResponse.statusText,
            error: errorText
          });
          throw new Error('Failed to fetch folders');
        }
        
        const foldersData = await foldersResponse.json();
        console.log('Fetched folders:', foldersData);
        
        if (!Array.isArray(foldersData)) {
          console.error('Expected array of folders but got:', foldersData);
          throw new Error('Invalid folders data received');
        }
        
        // Handle recipe folders response
        const recipeFolderIds = new Set<string>();
        if (recipeFoldersResponse.ok) {
          try {
            const recipeFoldersData = await recipeFoldersResponse.json();
            console.log('Recipe folders data:', recipeFoldersData);
            if (Array.isArray(recipeFoldersData)) {
              recipeFoldersData.forEach((folder: any) => {
                if (folder && folder.id !== undefined) {
                  // Ensure we store the ID as a string for consistency
                  recipeFolderIds.add(String(folder.id));
                }
              });
            }
          } catch (e) {
            console.error('Error parsing recipe folders response:', e);
          }
        } else if (recipeFoldersResponse.status !== 404) {
          // 404 is expected if the recipe isn't in any folders yet
          console.error('Recipe folders API error:', {
            status: recipeFoldersResponse.status,
            statusText: recipeFoldersResponse.statusText
          });
        }
        
        console.log('Folders containing recipe:', recipeFolderIds);
        
        // Normalize folder data and ensure required fields
        const validFolders = foldersData
          .filter((folder: any) => {
            const isValid = folder && folder.id !== undefined && typeof folder.name === 'string';
            if (!isValid) {
              console.warn('Invalid folder data:', folder);
            }
            return isValid;
          })
          .map((folder: any) => ({
            ...folder,
            // Ensure ID is always a string for consistent comparison
            id: String(folder.id)
          }));
        
        console.log('Setting valid folders:', validFolders);
        console.log('Setting folders containing recipe:', [...recipeFolderIds]);
        setFolders(validFolders);
        setFoldersWithRecipe(recipeFolderIds);
      } catch (error) {
        console.error('Error fetching folders:', error);
        toast({
          title: 'Error',
          description: error instanceof Error ? error.message : 'Failed to load your folders',
          variant: 'destructive',
        });
      } finally {
        setIsLoading(false);
      }
    };
    
    if (isOpen) {
      fetchFoldersAndRecipeStatus();
    }
  }, [isOpen, toast, recipeId, recipeType, isAuthenticated, token]);

  const createNewFolder = async () => {
    if (!newFolderName.trim()) return;
    
    setIsCreating(true);
    try {
      if (!isAuthenticated || !token) {
        throw new Error('Please sign in to create folders');
      }
      
      const response = await fetch('http://localhost:5003/api/folders', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        credentials: 'include',
        body: JSON.stringify({
          name: newFolderName.trim(),
          description: 'My recipe collection',
        }),
      });

      if (!response.ok) throw new Error('Failed to create folder');
      
      const newFolder = await response.json();
      setFolders([...folders, newFolder]);
      setNewFolderName('');
      
      toast({
        title: 'Success',
        description: `Folder "${newFolder.name}" created`,
      });
    } catch (error) {
      console.error('Error creating folder:', error);
      toast({
        title: 'Error',
        description: 'Failed to create folder. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsCreating(false);
    }
  };

  // Check if a recipe already exists in a folder
  const isRecipeInFolder = async (folderId: string): Promise<boolean> => {
    try {
      const response = await fetch(`http://localhost:5003/api/folders/${folderId}/recipes/${recipeId}?type=${recipeType}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
      
      if (response.ok) {
        const data = await response.json();
        return data.exists || false;
      }
      return false;
    } catch (error) {
      console.error('Error checking if recipe is in folder:', error);
      return false;
    }
  };

  const addToFolder = async (folderIdParam: string) => {
    console.log('[addToFolder] Starting with folderId:', folderIdParam);
    console.log('[addToFolder] Current folders:', folders);
    console.log('[addToFolder] Folders with recipe:', [...foldersWithRecipe]);
    
    if (!folderIdParam) {
      const errorMsg = 'No folderId provided to addToFolder';
      console.error(errorMsg);
      throw new Error('Invalid folder. Please try again.');
    }
    
    setIsSaving(true);
    
    try {
      if (!isAuthenticated || !token) {
        throw new Error('Please sign in to save recipes');
      }

      // Helper function to find a folder by ID with consistent string comparison
      const findFolderById = (id: string) => {
        if (!id) return undefined;
        // Convert both IDs to strings for consistent comparison
        return folders.find(f => String(f.id) === String(id));
      };

      // Find the target folder with consistent ID comparison
      let targetFolder = findFolderById(folderIdParam);
      let resolvedFolderId = targetFolder ? String(targetFolder.id) : folderIdParam;
      
      // Refresh folder list if needed
      if (!targetFolder) {
        console.log('Folder not found in local state, attempting to refresh...');
        try {
          const response = await fetch('http://localhost:5003/api/folders', {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            credentials: 'include',
          });
          
          if (response.ok) {
            const refreshedFolders = await response.json();
            console.log('Refreshed folders:', refreshedFolders);
            
            // Normalize folder IDs to strings
            const normalizedFolders = refreshedFolders.map((f: any) => ({
              ...f,
              id: String(f.id)
            }));
            
            setFolders(normalizedFolders);
            
            // Try to find the folder in the refreshed list
            const foundFolder = normalizedFolders.find((f: any) => 
              String(f.id) === String(folderIdParam)
            );
            
            if (foundFolder) {
              targetFolder = foundFolder;
              resolvedFolderId = String(foundFolder.id);
              console.log('Found folder after refresh:', targetFolder);
            }
          }
        } catch (refreshError) {
          console.error('Error refreshing folders:', refreshError);
        }
      }
      
      // Validate we have a valid folder
      if (!targetFolder) {
        const availableFolders = folders.length > 0 
          ? folders.map(f => `"${f.name}" (ID: ${f.id})`).join(', ')
          : 'No folders available';
          
        throw new Error(`Could not find the specified folder. Available folders: ${availableFolders}`);
      }
      
      console.log('Target folder lookup:', { 
        requestedId: folderIdParam,
        resolvedId: resolvedFolderId,
        targetFolder,
        allFolderIds: folders.map(f => ({ id: f.id, type: typeof f.id, name: f.name })),
        foldersWithRecipe: [...foldersWithRecipe]
      });
      
      // If we still don't have a folder, try refreshing the folder list
      if (!targetFolder && folders.length > 0) {
        console.log('Folder not found in local state, attempting to refresh...');
        try {
          const response = await fetch('http://localhost:5003/api/folders', {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            credentials: 'include',
          });
          
          if (response.ok) {
            const refreshedFolders = await response.json();
            console.log('Refreshed folders:', refreshedFolders);
            setFolders(refreshedFolders);
            
            // Try to find the folder in the refreshed list
            targetFolder = findFolderById(folderIdParam);
            if (targetFolder) {
              resolvedFolderId = targetFolder.id;
              console.log('Found folder after refresh:', targetFolder);
            }
          }
        } catch (refreshError) {
          console.error('Error refreshing folders:', refreshError);
          // Continue with the original ID if refresh fails
        }
      }
      
      // If we still don't have a valid folder, throw an error
      if (!targetFolder) {
        throw new Error(`Folder not found. Available folders: ${
          folders.length > 0 
            ? folders.map(f => `"${f.name}" (ID: ${f.id})`).join(', ')
            : 'No folders available'
        }`);
      }
      
      // Check if recipe is already in the folder using consistent string comparison
      const isInFolder = foldersWithRecipe.has(resolvedFolderId) || 
        Array.from(foldersWithRecipe).some(id => String(id) === resolvedFolderId);
        
      if (isInFolder) {
        throw new Error(`This recipe is already in the "${targetFolder.name}" folder`);
      }

      if (!recipeData) {
        throw new Error('Recipe data is missing. Cannot save to folder.');
      }
      
      // Prepare the recipe data for the API
      const payload = {
        recipe_id: recipeId,
        recipe_type: recipeType,
        recipe_data: {
          ...recipeData,
          // Ensure arrays are properly set
          ingredients: Array.isArray(recipeData.ingredients) ? recipeData.ingredients : [],
          instructions: Array.isArray(recipeData.instructions) ? recipeData.instructions : [],
        },
      };
      
      console.log('Sending payload with recipe type:', recipeType);
      
      const url = `http://localhost:5003/api/folders/${encodeURIComponent(resolvedFolderId)}/items`;
      console.log('Making request to:', url);
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        credentials: 'include',
        body: JSON.stringify(payload),
      });

      let responseData;
      try {
        responseData = await response.json();
      } catch (e) {
        console.error('Failed to parse response:', e);
        throw new Error('Invalid response from server');
      }
      
      if (!response.ok) {
        console.error('Failed to save to folder:', {
          status: response.status,
          statusText: response.statusText,
          response: responseData,
          url: response.url
        });
    
        if (response.status === 400) {
          // More specific error messages based on the response
          if (responseData.error && responseData.error.includes('already in folder')) {
            throw new Error(`This recipe is already in the "${targetFolder.name}" folder`);
          } else if (responseData.error && responseData.error.includes('not found')) {
            throw new Error('The folder was not found. It may have been deleted.');
          } else {
            throw new Error(responseData.error || 'Could not add recipe to folder. The folder may be invalid.');
          }
        } else if (response.status === 401) {
          throw new Error('Your session has expired. Please sign in again.');
        } else if (response.status === 403) {
          throw new Error('You do not have permission to add to this folder.');
        } else if (response.status === 404) {
          throw new Error('Folder not found. It may have been deleted.');
        } else {
          throw new Error('Failed to save to folder. Please try again later.');
        }
      }
      
      console.log('Successfully saved to folder:', responseData);
      
      // Update local state to reflect the save
      setFoldersWithRecipe(prev => {
        const updated = new Set(prev);
        updated.add(resolvedFolderId);
        console.log('Updated foldersWithRecipe:', [...updated]);
        return updated;
      });
      
      // Update the folder's recipe count locally
      setFolders(prevFolders => {
        const updated = prevFolders.map(folder => 
          String(folder.id) === resolvedFolderId
            ? { 
                ...folder, 
                recipe_count: (folder.recipe_count || 0) + 1,
                id: String(folder.id) // Ensure ID remains a string
              }
            : folder
        );
        console.log('Updated folders with new recipe count:', updated);
        return updated;
      });
      
      toast({
        title: 'Recipe saved',
        description: `Added to "${targetFolder.name}"`,
      });
      
      // Close the dialog after a short delay
      setTimeout(() => setIsOpen(false), 1500);
    } catch (error) {
      console.error('Error saving to folder:', error);
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to save recipe to folder. Please try again.',
        variant: 'destructive',
      });
      throw error; // Re-throw to allow the caller to handle if needed
    } finally {
      setIsSaving(false);
    }
  };

  return (
  <Dialog open={isOpen} onOpenChange={setIsOpen}>
    <DialogTrigger asChild>
      <Button variant="outline" className="gap-2">
        <FolderPlus className="h-4 w-4" />
        Save to Folder
      </Button>
    </DialogTrigger>
    <DialogPortal>
      <DialogOverlay className="bg-black/50" />
      <DialogContent className="sm:max-w-[425px]">
        <DialogPrimitive.Title className="sr-only">Save to Folder</DialogPrimitive.Title>
        <DialogHeader>
          <DialogTitle>Save to Folder</DialogTitle>
          <DialogDescription>
            Organize your recipes by saving them to folders
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Create new folder */}
          <div className="flex gap-2">
            <Input
              placeholder="New folder name"
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && createNewFolder()}
              disabled={isCreating}
            />
            <Button 
              onClick={createNewFolder} 
              disabled={!newFolderName.trim() || isCreating}
            >
              {isCreating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <FolderPlus className="mr-2 h-4 w-4" />
                  Create
                </>
              )}
            </Button>
          </div>
          
          {/* Folders list */}
          <div className="border rounded-lg divide-y max-h-60 overflow-y-auto">
            {isLoading ? (
              <div className="p-4 text-center text-muted-foreground">
                <Loader2 className="h-5 w-5 animate-spin mx-auto mb-2" />
                <p>Loading folders...</p>
              </div>
            ) : folders.length === 0 ? (
              <p className="p-4 text-center text-muted-foreground">No folders yet. Create one above.</p>
            ) : (
              folders.map((folder) => {
                const folderId = String(folder.id); // Ensure ID is a string
                return (
                  <div
                    key={`folder-${folderId}`}
                    className={`w-full ${foldersWithRecipe.has(folderId) ? 'opacity-60' : ''}`}
                  >
                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        console.log('Folder button clicked:', { folderId, name: folder.name });
                        if (folderId) {
                          addToFolder(folderId);
                        } else {
                          console.error('Invalid folder ID:', folder);
                          toast({
                            title: 'Error',
                            description: 'Invalid folder. Please try again.',
                            variant: 'destructive',
                          });
                        }
                      }}
                      disabled={isSaving || foldersWithRecipe.has(folderId)}
                      className={`w-full text-left p-3 transition-colors flex justify-between items-center ${
                        foldersWithRecipe.has(folderId)
                          ? 'cursor-not-allowed'
                          : 'hover:bg-accent'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        {foldersWithRecipe.has(folderId) ? (
                          <Check className="h-5 w-5 text-green-500" />
                        ) : (
                          <Folder className="h-5 w-5 text-primary" />
                        )}
                        <span>{folder.name}</span>
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {folder.recipe_count || 0} {folder.recipe_count === 1 ? 'item' : 'items'}
                        {foldersWithRecipe.has(folderId) && (
                          <span className="ml-2 text-green-500">• Added</span>
                        )}
                      </span>
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </DialogContent>
    </DialogPortal>
  </Dialog>
  );
}
