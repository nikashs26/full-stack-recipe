import React from 'react';
import { Folder, Recipe } from '../../types/recipe';

interface FolderDetailProps {
  folder: Folder;
  recipes: Recipe[];
  onRecipeSelect: (recipe: Recipe) => void;
  onBack: () => void;
}

export const FolderDetail: React.FC<FolderDetailProps> = ({
  folder,
  recipes,
  onRecipeSelect,
  onBack,
}) => {
  return (
    <div className="p-4">
      <div className="flex items-center mb-6">
        <button
          onClick={onBack}
          className="mr-4 text-blue-500 hover:text-blue-700"
        >
          ← Back to Folders
        </button>
        <h2 className="text-2xl font-bold">{folder.name}</h2>
      </div>

      {folder.description && (
        <p className="text-gray-600 mb-6">{folder.description}</p>
      )}

      {recipes.length === 0 ? (
        <p className="text-gray-500 text-center py-8">
          No recipes in this folder yet.
        </p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {recipes.map((recipe) => (
            <div
              key={recipe.id}
              className="border rounded p-4 hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => onRecipeSelect(recipe)}
            >
              {recipe.image && (
                <img
                  src={recipe.image}
                  alt={recipe.name}
                  className="w-full h-48 object-cover rounded mb-4"
                />
              )}
              <h3 className="text-xl font-semibold">{recipe.name}</h3>
              <p className="text-gray-600 mt-1">{recipe.cuisine}</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {recipe.dietaryRestrictions.map((restriction) => (
                  <span
                    key={restriction}
                    className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm"
                  >
                    {restriction}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}; 