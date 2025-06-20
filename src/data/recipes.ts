import { Recipe } from '../types/recipe';

export const initialRecipes: Recipe[] = [
  // Vegetarian Recipes
  {
    id: '1',
    name: 'Vegetarian Pasta Primavera',
    cuisine: 'Italian',
    dietaryRestrictions: ['Vegetarian'],
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
    dietaryRestrictions: ['Vegetarian'],
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
    dietaryRestrictions: ['Vegetarian'],
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
    dietaryRestrictions: ['Vegan'],
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
    dietaryRestrictions: ['Vegan'],
    ingredients: ['quinoa', 'roasted sweet potato', 'kale', 'chickpeas', 'tahini dressing'],
    instructions: ['Cook quinoa', 'Roast vegetables', 'Prepare dressing', 'Assemble bowl'],
    image: 'https://images.unsplash.com/photo-1511690656952-34342bb7c2f2?ixlib=rb-4.0.3',
    ratings: [5, 5, 4],
    comments: []
  },

  // Fixed Shepherd's Pie Recipe
  {
    id: '6',
    name: "Shepherd's Pie",
    cuisine: 'British',
    dietaryRestrictions: ['Non-Vegetarian'],
    ingredients: ['ground beef', 'beef broth', 'Worcestershire sauce', 'salt', 'potatoes', 'butter', 'onions', 'chopped carrots', 'corn', 'peas'],
    instructions: [
      'Boil the potatoes: Place the peeled and quartered potatoes in medium sized pot. Cover with at least an inch of cold water. Add a teaspoon of salt. Bring to a boil, reduce to a simmer, and cook until tender (about 20 minutes).',
      'Sauté the vegetables: While the potatoes are cooking, melt 4 tablespoons of the butter in a large sauté pan on medium heat. Add the chopped onions and carrots and cook until tender, about 6 to 10 minutes.',
      'Add peas and corn at the end of the sauté if using.',
      'Add ground beef to the pan. Cook until no longer pink. Drain excess fat if necessary.',
      'Add Worcestershire sauce and beef broth. Simmer for 10 minutes. Add broth as needed to keep moist.',
      'Mash the cooked potatoes with the remaining butter. Season with salt and pepper.',
      'Layer meat mixture in a baking dish, then top with mashed potatoes.',
      'Rough up surface of potatoes with fork for texture.',
      'Bake at 400°F until browned and bubbling (about 30 minutes). Broil for a few minutes if needed to brown.'
    ],
    image: 'https://www.simplyrecipes.com/thmb/fviw6rJNW_LXdVykXA-tk6hr2II=/750x0/filters:no_upscale():max_bytes(150000):strip_icc():format(webp)/Simply-Recipes-Easy-Shepherds-Pie-Lead-2_SERP-fdf8883477354e85bd05f9243f71657f.jpg',
    ratings: [5, 4, 5],
    comments: []
  },

  // Carnivore Recipes
  {
    id: '7',
    name: 'Steak Dinner',
    cuisine: 'American',
    dietaryRestrictions: ['Carnivore'],
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
    dietaryRestrictions: ['Carnivore'],
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
    dietaryRestrictions: ['Carnivore'],
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
    dietaryRestrictions: ['Gluten-free', 'Vegetarian'],
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
    dietaryRestrictions: ['Gluten-free'],
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
    dietaryRestrictions: ['Vegetarian'],
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
    dietaryRestrictions: ['Vegan'],
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
    dietaryRestrictions: ['Gluten-free', 'Vegetarian'],
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
    dietaryRestrictions: ['Carnivore'],
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
    dietaryRestrictions: ['Vegetarian'],
    ingredients: ['mascarpone cheese', 'espresso', 'ladyfingers', 'eggs', 'sugar', 'cocoa powder'],
    instructions: ['Prepare espresso', 'Mix mascarpone with eggs and sugar', 'Dip ladyfingers in espresso', 'Layer and dust with cocoa powder', 'Chill for several hours'],
    image: 'https://images.unsplash.com/photo-1571877227200-a0d98ea2fda3?ixlib=rb-4.0.3',
    ratings: [5, 5, 4],
    comments: []
  }
];
