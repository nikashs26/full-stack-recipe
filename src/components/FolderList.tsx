import React, { useState } from 'react';
import { Folder } from '../types/recipe';
import { Plus, Folder as FolderIcon, Trash2, Edit2 } from 'lucide-react';
import { useToast } from './ui/use-toast';

interface FolderListProps {
  folders: Folder[];
  onFolderSelect: (folderId: string) => void;
  onFolderCreate: (name: string, description?: string) => void;
  onFolderUpdate: (folderId: string, name: string, description?: string) => void;
  onFolderDelete: (folderId: string) => void;
}

const FolderList: React.FC<FolderListProps> = ({
  folders,
  onFolderSelect,
  onFolderCreate,
  onFolderUpdate,
  onFolderDelete,
}) => {
  const [isCreating, setIsCreating] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [newFolderDescription, setNewFolderDescription] = useState('');
  const [editingFolder, setEditingFolder] = useState<Folder | null>(null);
  const { toast } = useToast();

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFolderName.trim()) {
      toast({
        title: "Error",
        description: "Folder name is required",
        variant: "destructive",
      });
      return;
    }
    onFolderCreate(newFolderName.trim(), newFolderDescription.trim());
    setNewFolderName('');
    setNewFolderDescription('');
    setIsCreating(false);
  };

  const handleUpdateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingFolder || !editingFolder.name.trim()) {
      toast({
        title: "Error",
        description: "Folder name is required",
        variant: "destructive",
      });
      return;
    }
    onFolderUpdate(editingFolder.id, editingFolder.name.trim(), editingFolder.description?.trim());
    setEditingFolder(null);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">My Folders</h2>
        <button
          onClick={() => setIsCreating(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
        >
          <Plus className="w-4 h-4" />
          New Folder
        </button>
      </div>

      {isCreating && (
        <form onSubmit={handleCreateSubmit} className="space-y-4 p-4 border rounded-lg">
          <div>
            <label htmlFor="folderName" className="block text-sm font-medium mb-1">
              Folder Name
            </label>
            <input
              type="text"
              id="folderName"
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              className="w-full px-3 py-2 border rounded-md"
              placeholder="Enter folder name"
            />
          </div>
          <div>
            <label htmlFor="folderDescription" className="block text-sm font-medium mb-1">
              Description (optional)
            </label>
            <textarea
              id="folderDescription"
              value={newFolderDescription}
              onChange={(e) => setNewFolderDescription(e.target.value)}
              className="w-full px-3 py-2 border rounded-md"
              placeholder="Enter folder description"
              rows={3}
            />
          </div>
          <div className="flex gap-2">
            <button
              type="submit"
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
              Create
            </button>
            <button
              type="button"
              onClick={() => setIsCreating(false)}
              className="px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/90"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {folders.map((folder) => (
          <div
            key={folder.id}
            className="p-4 border rounded-lg hover:border-primary cursor-pointer"
            onClick={() => onFolderSelect(folder.id)}
          >
            {editingFolder?.id === folder.id ? (
              <form onSubmit={handleUpdateSubmit} className="space-y-4">
                <div>
                  <label htmlFor={`edit-${folder.id}`} className="block text-sm font-medium mb-1">
                    Folder Name
                  </label>
                  <input
                    type="text"
                    id={`edit-${folder.id}`}
                    value={editingFolder.name}
                    onChange={(e) => setEditingFolder({ ...editingFolder, name: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
                <div>
                  <label htmlFor={`edit-desc-${folder.id}`} className="block text-sm font-medium mb-1">
                    Description (optional)
                  </label>
                  <textarea
                    id={`edit-desc-${folder.id}`}
                    value={editingFolder.description || ''}
                    onChange={(e) => setEditingFolder({ ...editingFolder, description: e.target.value })}
                    className="w-full px-3 py-2 border rounded-md"
                    rows={3}
                  />
                </div>
                <div className="flex gap-2">
                  <button
                    type="submit"
                    className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
                  >
                    Save
                  </button>
                  <button
                    type="button"
                    onClick={() => setEditingFolder(null)}
                    className="px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/90"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <FolderIcon className="w-5 h-5 text-primary" />
                    <h3 className="font-semibold">{folder.name}</h3>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setEditingFolder(folder);
                      }}
                      className="p-1 hover:bg-secondary rounded-md"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onFolderDelete(folder.id);
                      }}
                      className="p-1 hover:bg-destructive hover:text-destructive-foreground rounded-md"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                {folder.description && (
                  <p className="text-sm text-muted-foreground">{folder.description}</p>
                )}
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default FolderList; 