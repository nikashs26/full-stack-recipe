
import React, { useState } from 'react';
import { Folder, Recipe } from '../types/recipe';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { Check, Folder as FolderIcon } from 'lucide-react';
import { toast } from './ui/use-toast';

interface FolderAssignmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  recipe: Recipe;
  folders: Folder[];
  onAssignFolder: (recipeId: string, folderId: string | undefined) => void;
}

const FolderAssignmentModal: React.FC<FolderAssignmentModalProps> = ({
  isOpen,
  onClose,
  recipe,
  folders,
  onAssignFolder,
}) => {
  const [selectedFolderId, setSelectedFolderId] = useState<string | undefined>(recipe.folderId);

  const handleAssignFolder = () => {
    onAssignFolder(recipe.id, selectedFolderId);
    toast({
      title: "Success",
      description: selectedFolderId
        ? `Recipe assigned to folder successfully`
        : `Recipe removed from folder`,
    });
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add "{recipe.name}" to Folder</DialogTitle>
        </DialogHeader>
        <div className="py-4">
          {folders.length === 0 ? (
            <p className="text-center text-muted-foreground">
              You don't have any folders yet. Create a folder first.
            </p>
          ) : (
            <ScrollArea className="h-[300px] pr-4">
              <div className="space-y-2">
                <div
                  className={`flex items-center justify-between p-2 rounded-md cursor-pointer ${
                    selectedFolderId === undefined ? 'bg-primary/10' : 'hover:bg-secondary'
                  }`}
                  onClick={() => setSelectedFolderId(undefined)}
                >
                  <div className="flex items-center gap-2">
                    <FolderIcon className="h-5 w-5 text-muted-foreground" />
                    <span>None (Remove from folder)</span>
                  </div>
                  {selectedFolderId === undefined && (
                    <Check className="h-4 w-4 text-primary" />
                  )}
                </div>
                {folders.map((folder) => (
                  <div
                    key={folder.id}
                    className={`flex items-center justify-between p-2 rounded-md cursor-pointer ${
                      selectedFolderId === folder.id ? 'bg-primary/10' : 'hover:bg-secondary'
                    }`}
                    onClick={() => setSelectedFolderId(folder.id)}
                  >
                    <div className="flex items-center gap-2">
                      <FolderIcon className="h-5 w-5 text-primary" />
                      <span>{folder.name}</span>
                    </div>
                    {selectedFolderId === folder.id && (
                      <Check className="h-4 w-4 text-primary" />
                    )}
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleAssignFolder} disabled={folders.length === 0}>
            Save
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default FolderAssignmentModal;
