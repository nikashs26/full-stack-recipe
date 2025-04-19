import React, { useState } from 'react';
import { Recipe, DietaryRestriction, Folder } from '../types/recipe';
import { Plus, Minus, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';


interface RecipeFormProps {
  initialData?: Recipe;
  onSubmit: (recipe: Omit<Recipe, 'id' | 'ratings' | 'comments'> & { id?: string }) => void;
  isEdit?: boolean;
}

const RecipeForm: React.FC<RecipeFormProps> = ({ 
  initialData, 
  onSubmit,
  isEdit = false
}) => {
  const navigate = useNavigate();
  const [name, setName] = useState(initialData?.name || '');
  const [cuisine, setCuisine] = useState(initialData?.cuisine || '');
  const [dietaryRestrictions, setDietaryRestrictions] = useState<DietaryRestriction[]>(
    initialData?.dietaryRestrictions || []
  );
  const [ingredients, setIngredients] = useState<string[]>(
    initialData?.ingredients || ['']
  );
  const [instructions, setInstructions] = useState<string[]>(
    initialData?.instructions || ['']
  );
  const [image, setImage] = useState(initialData?.image || '');
  const [folderId, setFolderId] = useState<string | undefined>(initialData?.folderId);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Fetch folders for the dropdown
  const { data: folders = [] } = useQuery<Folder[]>({
    queryKey: ['folders'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/folders`);
      if (!response.ok) throw new Error('Failed to fetch folders');
      const data = await response.json();
      return data.folders;
    },
  });

  const handleDietaryRestrictionChange = (restriction: DietaryRestriction) => {
    if (dietaryRestrictions.includes(restriction)) {
      setDietaryRestrictions(dietaryRestrictions.filter(r => r !== restriction));
    } else {
      setDietaryRestrictions([...dietaryRestrictions, restriction]);
    }
  };

  const handleIngredientChange = (index: number, value: string) => {
    const updatedIngredients = [...ingredients];
    updatedIngredients[index] = value;
    setIngredients(updatedIngredients);
  };

  const handleInstructionChange = (index: number, value: string) => {
    const updatedInstructions = [...instructions];
    updatedInstructions[index] = value;
    setInstructions(updatedInstructions);
  };

  const addIngredient = () => {
    setIngredients([...ingredients, '']);
  };

  const removeIngredient = (index: number) => {
    if (ingredients.length > 1) {
      const updatedIngredients = [...ingredients];
      updatedIngredients.splice(index, 1);
      setIngredients(updatedIngredients);
    }
  };

  const addInstruction = () => {
    setInstructions([...instructions, '']);
  };

  const removeInstruction = (index: number) => {
    if (instructions.length > 1) {
      const updatedInstructions = [...instructions];
      updatedInstructions.splice(index, 1);
      setInstructions(updatedInstructions);
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    
    if (!name.trim()) newErrors.name = 'Recipe name is required';
    if (!cuisine.trim()) newErrors.cuisine = 'Cuisine is required';
    if (dietaryRestrictions.length === 0) newErrors.dietary = 'Select at least one dietary restriction';
    if (!ingredients.filter(i => i.trim()).length) newErrors.ingredients = 'At least one ingredient is required';
    if (!instructions.filter(i => i.trim()).length) newErrors.instructions = 'At least one instruction is required';
    if (!image.trim()) newErrors.image = 'Image URL is required';
    
    return newErrors;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Filter out empty ingredients and instructions
    const filteredIngredients = ingredients.filter(i => i.trim());
    const filteredInstructions = instructions.filter(i => i.trim());
    
    const validationErrors = validateForm();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    
    const recipeData = {
      ...(initialData?.id && { id: initialData.id }),
      name,
      cuisine,
      dietaryRestrictions,
      ingredients: filteredIngredients,
      instructions: filteredInstructions,
      image,
      folderId,
    };
    
    onSubmit(recipeData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700">
          Recipe Name
        </label>
        <input
          type="text"
          id="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className={`mt-1 block w-full rounded-md border ${errors.name ? 'border-red-500' : 'border-gray-300'} px-3 py-2 focus:border-recipe-primary focus:outline-none focus:ring-recipe-primary sm:text-sm`}
        />
        {errors.name && <p className="mt-1 text-sm text-red-500">{errors.name}</p>}
      </div>
      
      <div>
        <label htmlFor="cuisine" className="block text-sm font-medium text-gray-700">
          Cuisine
        </label>
        <input
          type="text"
          id="cuisine"
          value={cuisine}
          onChange={(e) => setCuisine(e.target.value)}
          className={`mt-1 block w-full rounded-md border ${errors.cuisine ? 'border-red-500' : 'border-gray-300'} px-3 py-2 focus:border-recipe-primary focus:outline-none focus:ring-recipe-primary sm:text-sm`}
        />
        {errors.cuisine && <p className="mt-1 text-sm text-red-500">{errors.cuisine}</p>}
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700">
          Dietary Restrictions
        </label>
        <div className="mt-2 space-y-2">
          {(['vegetarian', 'vegan', 'gluten-free', 'carnivore'] as DietaryRestriction[]).map((restriction) => (
            <div key={restriction} className="flex items-center">
              <input
                type="checkbox"
                id={restriction}
                checked={dietaryRestrictions.includes(restriction)}
                onChange={() => handleDietaryRestrictionChange(restriction)}
                className="h-4 w-4 text-recipe-primary focus:ring-recipe-primary border-gray-300 rounded"
              />
              <label htmlFor={restriction} className="ml-2 block text-sm text-gray-700 capitalize">
                {restriction}
              </label>
            </div>
          ))}
        </div>
        {errors.dietary && <p className="mt-1 text-sm text-red-500">{errors.dietary}</p>}
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700">
          Ingredients
        </label>
        <div className="mt-2 space-y-2">
          {ingredients.map((ingredient, index) => (
            <div key={index} className="flex items-center space-x-2">
              <input
                type="text"
                value={ingredient}
                onChange={(e) => handleIngredientChange(index, e.target.value)}
                placeholder="Enter ingredient"
                className="block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-recipe-primary focus:outline-none focus:ring-recipe-primary sm:text-sm"
              />
              <button
                type="button"
                onClick={() => removeIngredient(index)}
                className="inline-flex items-center p-1 border border-transparent rounded-full text-red-600 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                <Minus className="h-5 w-5" />
              </button>
            </div>
          ))}
          <button
            type="button"
            onClick={addIngredient}
            className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-recipe-primary bg-recipe-accent hover:bg-recipe-accent/80 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-recipe-primary"
          >
            <Plus className="h-4 w-4 mr-1" /> Add Ingredient
          </button>
        </div>
        {errors.ingredients && <p className="mt-1 text-sm text-red-500">{errors.ingredients}</p>}
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700">
          Instructions
        </label>
        <div className="mt-2 space-y-2">
          {instructions.map((instruction, index) => (
            <div key={index} className="flex items-start space-x-2">
              <div className="mt-2 font-medium text-gray-500">{index + 1}.</div>
              <textarea
                value={instruction}
                onChange={(e) => handleInstructionChange(index, e.target.value)}
                placeholder="Enter instruction step"
                rows={2}
                className="block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-recipe-primary focus:outline-none focus:ring-recipe-primary sm:text-sm"
              />
              <button
                type="button"
                onClick={() => removeInstruction(index)}
                className="inline-flex items-center p-1 border border-transparent rounded-full text-red-600 hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                <Minus className="h-5 w-5" />
              </button>
            </div>
          ))}
          <button
            type="button"
            onClick={addInstruction}
            className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-recipe-primary bg-recipe-accent hover:bg-recipe-accent/80 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-recipe-primary"
          >
            <Plus className="h-4 w-4 mr-1" /> Add Instruction
          </button>
        </div>
        {errors.instructions && <p className="mt-1 text-sm text-red-500">{errors.instructions}</p>}
      </div>
      
      <div>
        <label htmlFor="image" className="block text-sm font-medium text-gray-700">
          Image URL
        </label>
        <input
          type="text"
          id="image"
          value={image}
          onChange={(e) => setImage(e.target.value)}
          placeholder="https://example.com/image.jpg"
          className={`mt-1 block w-full rounded-md border ${errors.image ? 'border-red-500' : 'border-gray-300'} px-3 py-2 focus:border-recipe-primary focus:outline-none focus:ring-recipe-primary sm:text-sm`}
        />
        {errors.image && <p className="mt-1 text-sm text-red-500">{errors.image}</p>}
        {image && (
          <div className="mt-2">
            <p className="text-sm text-gray-500 mb-1">Image Preview:</p>
            <img
              src={image}
              alt="Recipe preview"
              className="h-32 w-auto object-cover rounded-md"
              onError={(e) => {
                (e.target as HTMLImageElement).src = 'https://via.placeholder.com/400x300?text=Invalid+Image+URL';
              }}
            />
          </div>
        )}
      </div>
      
      <div>
        <label htmlFor="folder" className="block text-sm font-medium mb-1">
          Folder (optional)
        </label>
        <select
          id="folder"
          value={folderId || ''}
          onChange={(e) => setFolderId(e.target.value || undefined)}
          className="w-full px-3 py-2 border rounded-md"
        >
          <option value="">No folder</option>
          {folders.map((folder) => (
            <option key={folder.id} value={folder.id}>
              {folder.name}
            </option>
          ))}
        </select>
      </div>
      
      <div className="flex justify-end space-x-3">
        <button
          type="button"
          onClick={() => navigate('/')}
          className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-recipe-primary"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-recipe-primary hover:bg-recipe-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-recipe-primary"
        >
          {isEdit ? 'Update Recipe' : 'Create Recipe'}
        </button>
      </div>
    </form>
  );
};

export default RecipeForm;
