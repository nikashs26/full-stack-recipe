import { Recipe } from '../types/recipe';

export const initialRecipes: Recipe[] = [
  // Vegetarian Recipes
  {
    id: '1',
    name: 'Vegetarian Pasta Primavera',
    cuisine: 'Italian',
    mealType: 'dinner',
    dietaryRestrictions: ['vegetarian'],
    description: 'A light and fresh pasta dish bursting with the flavors of spring. Al dente pasta is tossed with a colorful medley of zucchini, bell peppers, and cherry tomatoes, all sautéed to perfection in garlic-infused olive oil. Finished with fresh basil and a sprinkle of parmesan, this dish is both satisfying and nutritious. (Per serving: 420 kcal, 14g protein, 72g carbs, 10g fat)',
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
    description: 'A classic French quiche featuring a buttery, flaky crust filled with a rich, creamy custard loaded with sautéed mushrooms, fresh spinach, and melted cheese. Perfect for brunch or a light dinner when served with a side salad. The earthy flavors of the mushrooms pair beautifully with the freshness of the spinach. (Per serving: 380 kcal, 16g protein, 22g carbs, 27g fat)',
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
    description: 'A quick and healthy stir-fry that comes together in minutes. Crisp-tender vegetables and pan-fried tofu are tossed in a savory garlic-ginger sauce, creating a perfect balance of textures and flavors. This versatile dish can be customized with your favorite seasonal vegetables and served over rice or noodles. (Per serving: 290 kcal, 18g protein, 35g carbs, 10g fat)',
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
    description: 'A rich and aromatic curry that showcases the depth of Indian spices. Tender vegetables and protein-rich chickpeas are simmered in a velvety coconut milk sauce, infused with turmeric, cumin, and coriander. This comforting dish is naturally gluten-free and packed with nutrients. Serve with basmati rice or warm naan for a complete meal. (Per serving: 350 kcal, 14g protein, 40g carbs, 18g fat)',
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
    description: 'A vibrant and nourishing bowl packed with plant-based goodness. This Buddha bowl combines protein-rich quinoa, roasted sweet potatoes, and chickpeas with fresh kale and a creamy tahini dressing. The perfect balance of textures and flavors, it\'s a satisfying meal that will keep you energized throughout the day. (Per serving: 450 kcal, 18g protein, 65g carbs, 15g fat)',
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
    description: 'A comforting and hearty plant-based twist on the classic shepherd\'s pie. Protein-packed lentils and vegetables are simmered in a rich, savory gravy and topped with creamy mashed potatoes. Baked to golden perfection, this dish is the ultimate comfort food that even meat-eaters will love. (Per serving: 380 kcal, 16g protein, 62g carbs, 8g fat)',
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
    description: 'A classic roasted chicken that turns out perfectly juicy on the inside with a golden, herb-infused skin. The combination of fresh rosemary, thyme, and garlic creates an aromatic dish that fills your kitchen with an irresistible fragrance. Simple enough for weeknight dinners yet impressive for special occasions. (Per serving: 380 kcal, 42g protein, 2g carbs, 22g fat)',
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
    description: 'Tender, juicy pork tenderloin coated in a sweet and tangy apple glaze with warm cinnamon notes. The natural sweetness of the apples perfectly complements the savory pork, creating a harmonious balance of flavors. This dish is surprisingly simple to make yet elegant enough for dinner parties. (Per serving: 320 kcal, 36g protein, 18g carbs, 12g fat)',
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
    description: 'Colorful bell peppers stuffed with a hearty mixture of protein-packed quinoa, black beans, sweet corn, and melted cheese. This nutritious dish is as visually appealing as it is delicious, with the quinoa providing a complete protein source. The peppers become perfectly tender in the oven while the cheese forms a golden, bubbly crust. (Per serving: 280 kcal, 12g protein, 42g carbs, 8g fat)',
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
    description: 'Perfectly grilled salmon fillets topped with a vibrant mango salsa that bursts with tropical flavors. The buttery richness of the salmon pairs beautifully with the sweet and tangy mango, while the red onion and cilantro add a refreshing crunch. This light yet satisfying dish comes together in under 30 minutes, making it ideal for busy weeknights. (Per serving: 350 kcal, 34g protein, 18g carbs, 16g fat)',
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
    description: 'The ultimate chocolate lover\'s dream - a warm, rich chocolate cake with a molten center that oozes out with every spoonful. The contrast between the slightly crispy exterior and the velvety interior is pure bliss. This impressive dessert is surprisingly simple to make yet always wows dinner guests. Serve with a scoop of vanilla ice cream for the perfect temperature contrast. (Per serving: 480 kcal, 7g protein, 45g carbs, 32g fat)',
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
    description: 'A comforting, wholesome dessert that celebrates the natural sweetness of apples. The tender, cinnamon-spiced apple filling is topped with a crunchy oat crumble that bakes to golden perfection. Made with coconut oil instead of butter, this vegan version is just as delicious as the classic. Serve warm with a scoop of dairy-free vanilla ice cream for the ultimate treat. (Per serving: 220 kcal, 2g protein, 42g carbs, 7g fat)',
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
    description: 'A velvety smooth cheesecake with a buttery gluten-free crust that no one will believe is gluten-free. The rich, creamy filling is perfectly balanced with the slight tang of cream cheese and a touch of vanilla. Topped with fresh berries, this dessert is as beautiful as it is delicious. The water bath baking method ensures a crack-free surface every time. (Per slice: 420 kcal, 8g protein, 35g carbs, 28g fat)',
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
    description: 'A rich and decadent custard that fits perfectly into a carnivore diet, using bone marrow for extra nutrition and creaminess. The vanilla bean adds a subtle sweetness without any sugar, while the eggs and cream create a silky smooth texture. Baked to perfection in a water bath, this custard is surprisingly light despite its rich ingredients. (Per serving: 320 kcal, 10g protein, 3g carbs, 30g fat)',
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
    description: 'A classic Italian dessert that translates to "pick me up" - and one bite will show you why. Layers of coffee-soaked ladyfingers alternate with a rich, creamy mascarpone mixture, all dusted with a generous coating of cocoa powder. The contrast between the strong coffee flavor, sweet cream, and bitter cocoa creates a perfect balance. Best made ahead to allow the flavors to meld together. (Per serving: 450 kcal, 9g protein, 45g carbs, 27g fat)',
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
            mealType: 'dinner',
            dietaryRestrictions: ["non-vegetarian"],
            description: 'A fiery and flavorful South Indian appetizer that packs a punch with its bold spices and crispy texture. Tender chicken pieces are marinated in a vibrant blend of yogurt and spices, then deep-fried to golden perfection. The final tempering of mustard seeds, curry leaves, and green chilies adds an aromatic finish that elevates the dish. Serve hot with mint chutney and lemon wedges for an authentic experience. (Per serving: 380 kcal, 35g protein, 12g carbs, 22g fat)',
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
    mealType: 'dinner',
    dietaryRestrictions: ["non-vegetarian"],
    description: 'The ultimate indulgence for cheese lovers, this burger takes comfort food to new heights. A perfectly grilled beef patty is smothered with a blend of melted cheddar, Swiss, and American cheeses, then topped with crispy bacon, caramelized onions, and a special sauce. Served on a toasted brioche bun with all the classic fixings, this burger is a messy, gooey, and utterly satisfying meal. (Per serving: 780 kcal, 45g protein, 42g carbs, 48g fat)',
    ingredients: ["1 lb ground beef (80/20 blend)", "4 brioche buns", "4 slices cheddar cheese", "4 slices Swiss cheese", "4 slices American cheese", "8 strips bacon, cooked", "1 large onion, caramelized", "Lettuce, tomato, pickles", "Special sauce (mayo, ketchup, mustard, relish)", "Salt and pepper to taste"],
    instructions: ["Form ground beef into 4 equal patties and season generously with salt and pepper",
    "Grill patties to desired doneness (3-4 minutes per side for medium)",
    "In the last minute of cooking, top each patty with cheddar, Swiss, and American cheeses",
    "Toast the brioche buns lightly",
    "Spread special sauce on both sides of the bun",
    "Build the burger with lettuce, tomato, and pickles",
    "Add the cheesy patty and top with bacon and caramelized onions",
    "Serve immediately with extra napkins!"],
    image: "https://www.foodandwine.com/thmb/kGduuYMiclM6OwXJsE4OuL2jBrw=/750x0/filters:no_upscale():max_bytes(150000):strip_icc():format(webp)/200707-r-xl-knuckle-sandwich-83f432a1769048a7a2ce887573b28fc9.jpg",
    ratings: [],
    comments: []
  }
  
];
