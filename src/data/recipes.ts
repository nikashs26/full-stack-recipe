import { Recipe } from '../types/recipe';

export const initialRecipes: Recipe[] = [
  // Vegetarian Recipes
  {
    id: '1',
    name: 'Vegetarian Pasta Primavera',
    cuisine: 'Italian',
    mealType: 'dinner',
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
    mealType: 'breakfast',
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
    mealType: 'dinner',
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
    mealType: 'dinner',
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
    mealType: 'lunch',
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
    mealType: 'dinner',
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
    mealType: 'dinner',
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
    mealType: 'dinner',
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
    mealType: 'dinner',
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
    mealType: 'lunch',
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
    mealType: 'dinner',
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
    mealType: 'dessert',
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
    mealType: 'dessert',
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
    mealType: 'dessert',
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
    mealType: 'dessert',
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
    mealType: 'dessert',
    dietaryRestrictions: ['vegetarian'],
    ingredients: ['mascarpone cheese', 'espresso', 'ladyfingers', 'eggs', 'sugar', 'cocoa powder'],
    instructions: ['Prepare espresso', 'Mix mascarpone with eggs and sugar', 'Dip ladyfingers in espresso', 'Layer and dust with cocoa powder', 'Chill for several hours'],
    image: 'https://images.unsplash.com/photo-1571877227200-a0d98ea2fda3?ixlib=rb-4.0.3',
    ratings: [5, 5, 4],
    comments: []
  },
  {
      id: '17',
            name: "Chicken 65",
            
            cuisine: "Indian",
            dietaryRestrictions: ["non-vegetarian"],
            ingredients: ["Boneless chicken", "Yogurt", "Ginger garlic paste", "Red chili powder", "Turmeric powder", "Coriander powder", "Cumin powder", "Garam masala", "Lemon juice", "Corn flour", "All-purpose flour", "Egg", "Curry leaves", "Green chilies", "Mustard seeds", "Salt", "Oil for frying"],
            instructions: ["Cut the boneless chicken into bite-sized pieces",
            "Marinate the chicken with yogurt, ginger garlic paste, red chili powder, turmeric powder, coriander powder, cumin powder, garam masala, lemon juice, and salt",
            "Let the chicken marinate for at least 30 minutes or up to 4 hours",
            "Add corn flour, all-purpose flour, and egg to the marinated chicken and mix well",
            "Heat oil in a deep pan for frying",
            "Fry the chicken pieces in batches until golden brown and crispy",
            "Remove the chicken and drain on paper towels",
            "In a separate pan, heat a little oil and add mustard seeds",
            "Once they splutter, add curry leaves and slit green chilies",
            "Toss in the fried chicken and sauté for a couple of minutes to coat with the tempered spices",
            "Serve hot as an appetizer or side dish"],
            image: "https://popmenucloud.com/cdn-cgi/image/width%3D3840%2Cheight%3D3840%2Cfit%3Dscale-down%2Cformat%3Dauto%2Cquality%3D60/zvmbjaxg/1f1b9169-865a-47f1-b9b0-092c8f7549d4.png",
            ratings: [],
            comments: []
  },
  {
    id: '18',
          name: "Super Cheesy Burger",
          
          cuisine: "American",
          dietaryRestrictions: ["non-vegetarian"],
          ingredients: ["Boneless chicken", "Yogurt", "Ginger garlic paste", "Red chili powder", "Turmeric powder", "Coriander powder", "Cumin powder", "Garam masala", "Lemon juice", "Corn flour", "All-purpose flour", "Egg", "Curry leaves", "Green chilies", "Mustard seeds", "Salt", "Oil for frying"],
          instructions: ["Cut the boneless chicken into bite-sized pieces",
          "Marinate the chicken with yogurt, ginger garlic paste, red chili powder, turmeric powder, coriander powder, cumin powder, garam masala, lemon juice, and salt",
          "Let the chicken marinate for at least 30 minutes or up to 4 hours",
          "Add corn flour, all-purpose flour, and egg to the marinated chicken and mix well",
          "Heat oil in a deep pan for frying",
          "Fry the chicken pieces in batches until golden brown and crispy",
          "Remove the chicken and drain on paper towels",
          "In a separate pan, heat a little oil and add mustard seeds",
          "Once they splutter, add curry leaves and slit green chilies",
          "Toss in the fried chicken and sauté for a couple of minutes to coat with the tempered spices",
          "Serve hot as an appetizer or side dish"],
          image: "https://www.foodandwine.com/thmb/kGduuYMiclM6OwXJsE4OuL2jBrw=/750x0/filters:no_upscale():max_bytes(150000):strip_icc():format(webp)/200707-r-xl-knuckle-sandwich-83f432a1769048a7a2ce887573b28fc9.jpg",
          ratings: [],
          comments: []
         
    

}
  
];
