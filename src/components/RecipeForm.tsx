
import React, { useState } from 'react';
import { Recipe, DietaryRestriction, DifficultyLevel } from '../types/recipe';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { ChevronDown, Plus, Minus, X } from 'lucide-react';

// Define prop types for RecipeForm component
interface RecipeFormProps {
  initialData?: Recipe;
  onSubmit: (recipeData: Omit<Recipe, 'id' | 'ratings' | 'comments'> & { id?: string }) => void;
  isEdit?: boolean;
}

const RecipeForm: React.FC<RecipeFormProps> = ({ initialData, onSubmit, isEdit = false }) => {
  // Default values for a new recipe
  const defaultRecipe = {
    name: '',
    cuisine: '',
    dietaryRestrictions: [] as DietaryRestriction[],
    ingredients: [''],
    instructions: [''],
    image: '',
    difficulty: 'medium' as DifficultyLevel,
  };

  // Initialize state with initialData or default values
  const [name, setName] = useState(initialData?.name || defaultRecipe.name);
  const [cuisine, setCuisine] = useState(initialData?.cuisine || defaultRecipe.cuisine);
  const [dietaryRestrictions, setDietaryRestrictions] = useState<DietaryRestriction[]>(
    initialData?.dietaryRestrictions || defaultRecipe.dietaryRestrictions
  );
  const [ingredients, setIngredients] = useState<string[]>(
    initialData?.ingredients || defaultRecipe.ingredients
  );
  const [instructions, setInstructions] = useState<string[]>(
    initialData?.instructions || defaultRecipe.instructions
  );
  const [image, setImage] = useState(initialData?.image || defaultRecipe.image);
  const [difficulty, setDifficulty] = useState<DifficultyLevel>(
    initialData?.difficulty || defaultRecipe.difficulty
  );

  // Available dietary restrictions
  const availableDietaryRestrictions: DietaryRestriction[] = [
    'vegetarian',
    'vegan',
    'gluten-free',
    'carnivore',
  ];

  // Available difficulty levels
  const difficultyLevels: DifficultyLevel[] = ['easy', 'medium', 'hard'];

  // Handle dietary restriction toggle
  const handleDietaryRestrictionToggle = (restriction: DietaryRestriction) => {
    if (dietaryRestrictions.includes(restriction)) {
      setDietaryRestrictions(dietaryRestrictions.filter(r => r !== restriction));
    } else {
      setDietaryRestrictions([...dietaryRestrictions, restriction]);
    }
  };

  // Handle ingredient changes
  const handleIngredientChange = (index: number, value: string) => {
    const newIngredients = [...ingredients];
    newIngredients[index] = value;
    setIngredients(newIngredients);
  };

  // Add new ingredient field
  const addIngredientField = () => {
    setIngredients([...ingredients, '']);
  };

  // Remove ingredient field
  const removeIngredientField = (index: number) => {
    if (ingredients.length === 1) return;
    const newIngredients = [...ingredients];
    newIngredients.splice(index, 1);
    setIngredients(newIngredients);
  };

  // Handle instruction changes
  const handleInstructionChange = (index: number, value: string) => {
    const newInstructions = [...instructions];
    newInstructions[index] = value;
    setInstructions(newInstructions);
  };

  // Add new instruction field
  const addInstructionField = () => {
    setInstructions([...instructions, '']);
  };

  // Remove instruction field
  const removeInstructionField = (index: number) => {
    if (instructions.length === 1) return;
    const newInstructions = [...instructions];
    newInstructions.splice(index, 1);
    setInstructions(newInstructions);
  };

  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Filter out empty ingredients and instructions
    const filteredIngredients = ingredients.filter(ingredient => ingredient.trim() !== '');
    const filteredInstructions = instructions.filter(instruction => instruction.trim() !== '');

    const recipeData = {
      ...(isEdit && initialData ? { id: initialData.id } : {}),
      name,
      cuisine,
      dietaryRestrictions,
      ingredients: filteredIngredients.length > 0 ? filteredIngredients : [''],
      instructions: filteredInstructions.length > 0 ? filteredInstructions : [''],
      image,
      difficulty,
      // Add these properties for creation date if it's a new recipe
      ...(isEdit ? {} : {
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }),
      // Always update the updatedAt timestamp when editing
      ...(isEdit ? { updatedAt: new Date().toISOString() } : {})
    };

    onSubmit(recipeData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-4">
        <div>
          <Label htmlFor="name" className="block font-medium">Recipe Name</Label>
          <Input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter recipe name"
            required
            className="mt-1 w-full"
          />
        </div>

        <div>
          <Label htmlFor="cuisine" className="block font-medium">Cuisine</Label>
          <Input
            id="cuisine"
            type="text"
            value={cuisine}
            onChange={(e) => setCuisine(e.target.value)}
            placeholder="Enter cuisine type"
            required
            className="mt-1 w-full"
          />
        </div>

        <div>
          <Label htmlFor="image" className="block font-medium">Image URL</Label>
          <Input
            id="image"
            type="text"
            value={image}
            onChange={(e) => setImage(e.target.value)}
            placeholder="Enter image URL"
            className="mt-1 w-full"
          />
          {image && (
            <div className="mt-2 w-full h-40 relative">
              <img
                src={image}
                alt="Recipe preview"
                className="w-full h-full object-cover rounded-md"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = '/placeholder.svg';
                }}
              />
            </div>
          )}
        </div>

        <div>
          <span className="block font-medium mb-2">Difficulty Level</span>
          <div className="flex gap-4">
            {difficultyLevels.map((level) => (
              <div key={level} className="flex items-center gap-2">
                <input
                  type="radio"
                  id={`difficulty-${level}`}
                  name="difficulty"
                  checked={difficulty === level}
                  onChange={() => setDifficulty(level)}
                  className="h-4 w-4"
                />
                <Label htmlFor={`difficulty-${level}`} className="capitalize">
                  {level}
                </Label>
              </div>
            ))}
          </div>
        </div>

        <div>
          <span className="block font-medium mb-2">Dietary Restrictions</span>
          <div className="flex flex-wrap gap-4">
            {availableDietaryRestrictions.map((restriction) => (
              <div key={restriction} className="flex items-center gap-2">
                <Checkbox
                  id={`restriction-${restriction}`}
                  checked={dietaryRestrictions.includes(restriction)}
                  onCheckedChange={() => handleDietaryRestrictionToggle(restriction)}
                />
                <Label htmlFor={`restriction-${restriction}`} className="capitalize">
                  {restriction}
                </Label>
              </div>
            ))}
          </div>
        </div>

        <div>
          <Label htmlFor="ingredients" className="block font-medium">Ingredients</Label>
          <div className="space-y-2">
            {ingredients.map((ingredient, index) => (
              <div key={index} className="flex gap-2">
                <Input
                  value={ingredient}
                  onChange={(e) => handleIngredientChange(index, e.target.value)}
                  placeholder={`Ingredient ${index + 1}`}
                  className="flex-1"
                />
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={() => removeIngredientField(index)}
                  disabled={ingredients.length === 1}
                >
                  <Minus className="h-4 w-4" />
                </Button>
              </div>
            ))}
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={addIngredientField}
              className="flex items-center gap-1"
            >
              <Plus className="h-4 w-4" /> Add Ingredient
            </Button>
          </div>
        </div>

        <div>
          <Label htmlFor="instructions" className="block font-medium">Instructions</Label>
          <div className="space-y-2">
            {instructions.map((instruction, index) => (
              <div key={index} className="flex gap-2">
                <Textarea
                  value={instruction}
                  onChange={(e) => handleInstructionChange(index, e.target.value)}
                  placeholder={`Step ${index + 1}`}
                  className="flex-1"
                />
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={() => removeInstructionField(index)}
                  disabled={instructions.length === 1}
                >
                  <Minus className="h-4 w-4" />
                </Button>
              </div>
            ))}
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={addInstructionField}
              className="flex items-center gap-1"
            >
              <Plus className="h-4 w-4" /> Add Step
            </Button>
          </div>
        </div>
      </div>

      <div className="pt-4">
        <Button type="submit" className="w-full">
          {isEdit ? 'Update Recipe' : 'Create Recipe'}
        </Button>
      </div>
    </form>
  );
};

export default RecipeForm;
