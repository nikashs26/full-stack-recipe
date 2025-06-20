import { Recipe } from '../types/recipe';

export const initialRecipes: Recipe[] = [
  // Vegetarian Recipes
  {
    id: '1',
    name: 'Vegetarian Pasta Primavera',
    cuisine: 'Italian',
    dietaryRestrictions: ['vegetarian'],
    ingredients: ['pasta', 'zucchini', 'bell peppers', 'cherry tomatoes', 'basil', 'olive oil'],
    instructions: ['Chop vegetables', 'Sauté vegetables', 'Cook pasta', 'Combine and serve'],
    image: 'https://images.unsplash.com/photo-1473093295043-cdd812d0e601?ixlib=rb-4.0.3',
    ratings: [4, 5, 4],
    comments: []
  },
  {
    id: '2',
    name: 'Spinach and Mushroom Quiche',
    cuisine: 'French',
    dietaryRestrictions: ['vegetarian'],
    ingredients: ['eggs', 'spinach', 'mushrooms', 'cheese', 'pie crust'],
    instructions: ['Prepare crust', 'Sauté vegetables', 'Mix with eggs', 'Bake until golden'],
    image: 'https://images.unsplash.com/photo-1623428187969-5da2dcea5ebf?ixlib=rb-4.0.3',
    ratings: [5, 4, 5],
    comments: []
  },
  {
    id: '3',
    name: 'Vegetable Stir Fry',
    cuisine: 'Asian',
    dietaryRestrictions: ['vegetarian', 'vegan'],
    ingredients: ['tofu', 'broccoli', 'carrots', 'snap peas', 'soy sauce', 'rice'],
    instructions: ['Press tofu', 'Chop vegetables', 'Stir fry', 'Serve over rice'],
    image: 'https://images.unsplash.com/photo-1512003867696-6d5ce6835040?ixlib=rb-4.0.3',
    ratings: [4, 4, 5],
    comments: []
  },

  // Vegan Recipes
  {
    id: '4',
    name: 'Vegan Curry',
    cuisine: 'Indian',
    dietaryRestrictions: ['vegan', 'vegetarian'],
    ingredients: ['coconut milk', 'vegetables', 'curry paste', 'tofu'],
    instructions: ['Chop vegetables', 'Simmer in coconut milk', 'Add curry paste', 'Add tofu'],
    image: 'https://images.unsplash.com/photo-1565557623262-b51c2513a641?ixlib=rb-4.0.3',
    ratings: [5, 4, 5],
    comments: []
  },
  {
    id: '5',
    name: 'Vegan Buddha Bowl',
    cuisine: 'Modern',
    dietaryRestrictions: ['vegan', 'vegetarian'],
    ingredients: ['quinoa', 'roasted sweet potato', 'kale', 'chickpeas', 'tahini dressing'],
    instructions: ['Cook quinoa', 'Roast vegetables', 'Prepare dressing', 'Assemble bowl'],
    image: 'https://images.unsplash.com/photo-1511690656952-34342bb7c2f2?ixlib=rb-4.0.3',
    ratings: [5, 5, 4],
    comments: []
  },


  {
    id: '6',
    name: 'Lentil Shepherd\'s Pie',
    cuisine: 'British',
    dietaryRestrictions: ['vegan', 'vegetarian'],
    ingredients: ['lentils', 'vegetables', 'mashed potatoes', 'nutritional yeast'],
    instructions: ['Cook lentils', 'Prepare vegetable base', 'Top with mashed potatoes', 'Bake'],
    image: 'https://images.unsplash.com/photo-1619480079718-9180a92adb05?ixlib=rb-4.0.3',
    ratings: [4, 5, 5],
    comments: []
  },

  // Carnivore Recipes
  {
    id: '7',
    name: 'Dinner',
    cuisine: 'American',
    dietaryRestrictions: ['carnivore'],
    ingredients: ['beef steak', 'salt', 'pepper', 'butter'],
    instructions: ['Season steak', 'Grill to desired doneness', 'Rest and serve'],
    image: 'https://images.unsplash.com/photo-1600891964092-4316c288032e?ixlib=rb-4.0.3',
    ratings: [5, 5, 4],
    comments: []
  },
  {
    id: '8',
    name: 'Roasted Chicken with Herbs',
    cuisine: 'Mediterranean',
    dietaryRestrictions: ['carnivore'],
    ingredients: ['whole chicken', 'rosemary', 'thyme', 'garlic', 'olive oil'],
    instructions: ['Prepare herb rub', 'Coat chicken', 'Roast until golden', 'Rest before serving'],
    image: 'https://images.unsplash.com/photo-1598103442097-8b74394b95c6?ixlib=rb-4.0.3',
    ratings: [4, 5, 5],
    comments: []
  },
  {
    id: '9',
    name: 'Pork Tenderloin with Apple Glaze',
    cuisine: 'American',
    dietaryRestrictions: ['carnivore'],
    ingredients: ['pork tenderloin', 'apples', 'honey', 'cinnamon'],
    instructions: ['Sear tenderloin', 'Prepare apple glaze', 'Roast', 'Glaze and serve'],
    image: 'https://images.unsplash.com/photo-1432139555190-58524dae6a55?ixlib=rb-4.0.3',
    ratings: [5, 4, 5],
    comments: []
  },

  // Gluten-Free Recipes
  {
    id: '10',
    name: 'Quinoa Stuffed Bell Peppers',
    cuisine: 'Mexican',
    dietaryRestrictions: ['gluten-free', 'vegetarian'],
    ingredients: ['quinoa', 'bell peppers', 'black beans', 'corn', 'cheese'],
    instructions: ['Cook quinoa', 'Prepare filling', 'Stuff peppers', 'Bake until peppers are soft'],
    image: 'https://images.unsplash.com/photo-1608164368481-77294a65efb8?ixlib=rb-4.0.3',
    ratings: [4, 5, 4],
    comments: []
  },
  {
    id: '11',
    name: 'Grilled Salmon with Mango Salsa',
    cuisine: 'Fusion',
    dietaryRestrictions: ['gluten-free'],
    ingredients: ['salmon', 'mango', 'red onion', 'cilantro', 'lime'],
    instructions: ['Prepare salsa', 'Grill salmon', 'Top with salsa', 'Serve'],
    image: 'https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?ixlib=rb-4.0.3',
    ratings: [5, 5, 4],
    comments: []
  },

  // Dessert Recipes
  {
    id: '12',
    name: 'Chocolate Lava Cake',
    cuisine: 'French',
    dietaryRestrictions: ['vegetarian'],
    ingredients: ['dark chocolate', 'butter', 'eggs', 'sugar', 'flour', 'vanilla extract'],
    instructions: ['Melt chocolate and butter', 'Mix with other ingredients', 'Pour into ramekins', 'Bake until edges are set but center is soft'],
    image: 'https://images.unsplash.com/photo-1563805042-7684c019e1cb?ixlib=rb-4.0.3',
    ratings: [5, 5, 5],
    comments: []
  },
  {
    id: '13',
    name: 'Vegan Apple Crisp',
    cuisine: 'American',
    dietaryRestrictions: ['vegan', 'vegetarian'],
    ingredients: ['apples', 'cinnamon', 'oats', 'brown sugar', 'coconut oil', 'lemon juice'],
    instructions: ['Slice apples', 'Mix with lemon juice and cinnamon', 'Create oat topping', 'Bake until golden and bubbly'],
    image: 'https://images.unsplash.com/photo-1621236378699-8597faf6a11a?ixlib=rb-4.0.3',
    ratings: [4, 5, 4],
    comments: []
  },
  {
    id: '14',
    name: 'Gluten-Free Cheesecake',
    cuisine: 'American',
    dietaryRestrictions: ['gluten-free', 'vegetarian'],
    ingredients: ['gluten-free graham crackers', 'cream cheese', 'eggs', 'sugar', 'vanilla extract', 'berries'],
    instructions: ['Make gluten-free crust', 'Prepare filling', 'Bake in water bath', 'Chill and top with berries'],
    image: 'https://images.unsplash.com/photo-1533134242443-d4fd215305ad?ixlib=rb-4.0.3',
    ratings: [5, 4, 5],
    comments: []
  },
  {
    id: '15',
    name: 'Carnivore Custard',
    cuisine: 'French',
    dietaryRestrictions: ['carnivore'],
    ingredients: ['eggs', 'heavy cream', 'vanilla bean', 'bone marrow'],
    instructions: ['Whisk eggs and cream', 'Add melted bone marrow', 'Pour into ramekins', 'Bake in water bath until set'],
    image: 'https://images.unsplash.com/photo-1488477181946-6428a0291777?ixlib=rb-4.0.3',
    ratings: [4, 3, 4],
    comments: []
  },
  {
    id: '16',
    name: 'Tiramisu',
    cuisine: 'Italian',
    dietaryRestrictions: ['vegetarian'],
    ingredients: ['mascarpone cheese', 'espresso', 'ladyfingers', 'eggs', 'sugar', 'cocoa powder'],
    instructions: ['Prepare espresso', 'Mix mascarpone with eggs and sugar', 'Dip ladyfingers in espresso', 'Layer and dust with cocoa powder', 'Chill for several hours'],
    image: 'https://images.unsplash.com/photo-1571877227200-a0d98ea2fda3?ixlib=rb-4.0.3',
    ratings: [5, 5, 4],
    comments: []
  }
];
