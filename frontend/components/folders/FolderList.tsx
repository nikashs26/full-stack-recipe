import React, { useState } from 'react';
import { Folder } from '../../types/recipe';

interface FolderListProps {
  folders: Folder[];
  onFolderSelect: (folder: Folder) => void;
  onFolderCreate: (name: string, description?: string) => void;
  onFolderDelete: (folderId: string) => void;
}

export const FolderList: React.FC<FolderListProps> = ({
  folders,
  onFolderSelect,
  onFolderCreate,
  onFolderDelete,
}) => {
  const [isCreating, setIsCreating] = useState(false);
  const [newFolderName, setNewFolderName] = useState('');
  const [newFolderDescription, setNewFolderDescription] = useState('');

  const handleCreateFolder = (e: React.FormEvent) => {
    e.preventDefault();
    if (newFolderName.trim()) {
      onFolderCreate(newFolderName.trim(), newFolderDescription.trim());
      setNewFolderName('');
      setNewFolderDescription('');
      setIsCreating(false);
    }
  };

  return (
    <div className="p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold">My Folders</h2>
        <button
          onClick={() => setIsCreating(!isCreating)}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          {isCreating ? 'Cancel' : 'New Folder'}
        </button>
      </div>

      {isCreating && (
        <form onSubmit={handleCreateFolder} className="mb-4 p-4 border rounded">
          <input
            type="text"
            value={newFolderName}
            onChange={(e) => setNewFolderName(e.target.value)}
            placeholder="Folder Name"
            className="w-full mb-2 p-2 border rounded"
            required
          />
          <textarea
            value={newFolderDescription}
            onChange={(e) => setNewFolderDescription(e.target.value)}
            placeholder="Description (optional)"
            className="w-full mb-2 p-2 border rounded"
          />
          <button
            type="submit"
            className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
          >
            Create Folder
          </button>
        </form>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {folders.map((folder) => (
          <div
            key={folder.id}
            className="border rounded p-4 hover:shadow-lg transition-shadow"
          >
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-xl font-semibold">{folder.name}</h3>
                {folder.description && (
                  <p className="text-gray-600 mt-1">{folder.description}</p>
                )}
              </div>
              <button
                onClick={() => onFolderDelete(folder.id)}
                className="text-red-500 hover:text-red-700"
              >
                Delete
              </button>
            </div>
            <button
              onClick={() => onFolderSelect(folder)}
              className="mt-4 text-blue-500 hover:text-blue-700"
            >
              View Recipes
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}; 