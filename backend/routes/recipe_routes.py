
import json
import requests
from flask import request, jsonify
import time
from bson import ObjectId
from datetime import datetime
from services.recipe_cache_service import RecipeCacheService

# Initialize recipe cache service
recipe_cache = RecipeCacheService()

# Large fallback recipe collection for when MongoDB is unavailable
FALLBACK_RECIPES = [
    # Italian Cuisine
    {
        "id": 10001,
        "title": "Classic Spaghetti Carbonara",
        "image": "https://images.unsplash.com/photo-1551892589-865f69869476?w=400",
        "cuisines": ["Italian"],
        "diets": ["dairy", "eggs"],
        "readyInMinutes": 25,
        "servings": 4,
        "summary": "Authentic Italian carbonara with eggs, cheese, and pancetta",
        "instructions": "Cook pasta, mix with eggs and cheese, add pancetta",
        "extendedIngredients": [
            {"name": "spaghetti", "amount": 400, "unit": "g"},
            {"name": "eggs", "amount": 4, "unit": "large"},
            {"name": "pancetta", "amount": 150, "unit": "g"},
            {"name": "parmesan cheese", "amount": 100, "unit": "g"}
        ]
    },
    {
        "id": 10002,
        "title": "Margherita Pizza",
        "image": "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=400",
        "cuisines": ["Italian"],
        "diets": ["vegetarian", "dairy", "gluten"],
        "readyInMinutes": 30,
        "servings": 4,
        "summary": "Traditional Neapolitan pizza with tomato, mozzarella, and basil",
        "extendedIngredients": [
            {"name": "pizza dough", "amount": 1, "unit": "ball"},
            {"name": "tomato sauce", "amount": 200, "unit": "ml"},
            {"name": "mozzarella", "amount": 200, "unit": "g"},
            {"name": "fresh basil", "amount": 10, "unit": "leaves"}
        ]
    },
    {
        "id": 10003,
        "title": "Chicken Risotto",
        "image": "https://images.unsplash.com/photo-1476124369491-e7addf5db371?w=400",
        "cuisines": ["Italian"],
        "diets": ["gluten-free", "dairy"],
        "readyInMinutes": 45,
        "servings": 6,
        "summary": "Creamy arborio rice with tender chicken and parmesan",
        "extendedIngredients": [
            {"name": "arborio rice", "amount": 300, "unit": "g"},
            {"name": "chicken breast", "amount": 500, "unit": "g"},
            {"name": "chicken stock", "amount": 1200, "unit": "ml"},
            {"name": "parmesan cheese", "amount": 100, "unit": "g"}
        ]
    },
    {
        "id": 10004,
        "title": "Lasagna Bolognese",
        "image": "https://images.unsplash.com/photo-1574894709920-11b28e7367e3?w=400",
        "cuisines": ["Italian"],
        "diets": ["dairy", "gluten"],
        "readyInMinutes": 90,
        "servings": 8,
        "summary": "Layered pasta with meat sauce, bechamel, and cheese",
        "extendedIngredients": [
            {"name": "lasagna sheets", "amount": 12, "unit": "pieces"},
            {"name": "ground beef", "amount": 500, "unit": "g"},
            {"name": "bechamel sauce", "amount": 500, "unit": "ml"},
            {"name": "mozzarella cheese", "amount": 300, "unit": "g"}
        ]
    },
    
    # Mexican Cuisine
    {
        "id": 10005,
        "title": "Beef Tacos with Guacamole",
        "image": "https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400",
        "cuisines": ["Mexican"],
        "diets": ["gluten-free", "dairy-free"],
        "readyInMinutes": 20,
        "servings": 4,
        "summary": "Spiced ground beef in corn tortillas with fresh guacamole",
        "extendedIngredients": [
            {"name": "ground beef", "amount": 500, "unit": "g"},
            {"name": "corn tortillas", "amount": 8, "unit": "pieces"},
            {"name": "avocados", "amount": 3, "unit": "large"},
            {"name": "lime", "amount": 2, "unit": "pieces"}
        ]
    },
    {
        "id": 10006,
        "title": "Chicken Enchiladas",
        "image": "https://images.unsplash.com/photo-1599974579688-8dbdd335c77f?w=400",
        "cuisines": ["Mexican"],
        "diets": ["dairy", "gluten"],
        "readyInMinutes": 35,
        "servings": 6,
        "summary": "Rolled tortillas filled with chicken and topped with spicy sauce",
        "extendedIngredients": [
            {"name": "chicken breast", "amount": 600, "unit": "g"},
            {"name": "flour tortillas", "amount": 8, "unit": "pieces"},
            {"name": "enchilada sauce", "amount": 400, "unit": "ml"},
            {"name": "cheddar cheese", "amount": 200, "unit": "g"}
        ]
    },
    {
        "id": 10007,
        "title": "Veggie Quesadillas",
        "image": "https://images.unsplash.com/photo-1618040996337-56904b7850b9?w=400",
        "cuisines": ["Mexican"],
        "diets": ["vegetarian", "dairy", "gluten"],
        "readyInMinutes": 15,
        "servings": 4,
        "summary": "Crispy tortillas filled with cheese and roasted vegetables",
        "extendedIngredients": [
            {"name": "flour tortillas", "amount": 4, "unit": "large"},
            {"name": "bell peppers", "amount": 2, "unit": "pieces"},
            {"name": "monterey jack cheese", "amount": 200, "unit": "g"},
            {"name": "red onion", "amount": 1, "unit": "medium"}
        ]
    },
    
    # Indian Cuisine
    {
        "id": 10008,
        "title": "Butter Chicken",
        "image": "https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=400",
        "cuisines": ["Indian"],
        "diets": ["gluten-free", "dairy"],
        "readyInMinutes": 40,
        "servings": 4,
        "summary": "Creamy tomato-based curry with tender chicken pieces",
        "extendedIngredients": [
            {"name": "chicken thighs", "amount": 800, "unit": "g"},
            {"name": "tomato puree", "amount": 400, "unit": "ml"},
            {"name": "heavy cream", "amount": 200, "unit": "ml"},
            {"name": "garam masala", "amount": 2, "unit": "tsp"}
        ]
    },
    {
        "id": 10009,
        "title": "Vegetable Biryani",
        "image": "https://images.unsplash.com/photo-1563379091339-03246963d719?w=400",
        "cuisines": ["Indian"],
        "diets": ["vegetarian", "vegan", "gluten-free", "dairy-free"],
        "readyInMinutes": 60,
        "servings": 6,
        "summary": "Fragrant basmati rice with mixed vegetables and aromatic spices",
        "extendedIngredients": [
            {"name": "basmati rice", "amount": 400, "unit": "g"},
            {"name": "mixed vegetables", "amount": 500, "unit": "g"},
            {"name": "saffron", "amount": 1, "unit": "pinch"},
            {"name": "biryani spice mix", "amount": 3, "unit": "tbsp"}
        ]
    },
    {
        "id": 10010,
        "title": "Chicken Tikka Masala",
        "image": "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=400",
        "cuisines": ["Indian"],
        "diets": ["gluten-free", "dairy"],
        "readyInMinutes": 50,
        "servings": 4,
        "summary": "Marinated chicken in a rich, creamy tomato curry sauce",
        "extendedIngredients": [
            {"name": "chicken breast", "amount": 700, "unit": "g"},
            {"name": "yogurt", "amount": 200, "unit": "ml"},
            {"name": "coconut milk", "amount": 400, "unit": "ml"},
            {"name": "tikka masala paste", "amount": 3, "unit": "tbsp"}
        ]
    },
    
    # Chinese Cuisine
    {
        "id": 10011,
        "title": "Sweet and Sour Pork",
        "image": "https://images.unsplash.com/photo-1562059390-a761a084768e?w=400",
        "cuisines": ["Chinese"],
        "diets": ["dairy-free"],
        "readyInMinutes": 25,
        "servings": 4,
        "summary": "Crispy pork pieces in a tangy sweet and sour sauce",
        "extendedIngredients": [
            {"name": "pork tenderloin", "amount": 600, "unit": "g"},
            {"name": "pineapple chunks", "amount": 200, "unit": "g"},
            {"name": "bell peppers", "amount": 2, "unit": "pieces"},
            {"name": "sweet and sour sauce", "amount": 250, "unit": "ml"}
        ]
    },
    {
        "id": 10012,
        "title": "Ma Po Tofu",
        "image": "https://images.unsplash.com/photo-1586190848861-99aa4a171e90?w=400",
        "cuisines": ["Chinese"],
        "diets": ["vegetarian", "gluten-free", "dairy-free"],
        "readyInMinutes": 20,
        "servings": 4,
        "summary": "Silky tofu in spicy Sichuan sauce with ground pork",
        "extendedIngredients": [
            {"name": "soft tofu", "amount": 400, "unit": "g"},
            {"name": "ground pork", "amount": 200, "unit": "g"},
            {"name": "fermented black beans", "amount": 2, "unit": "tbsp"},
            {"name": "sichuan peppercorns", "amount": 1, "unit": "tsp"}
        ]
    },
    {
        "id": 10013,
        "title": "Kung Pao Chicken",
        "image": "https://images.unsplash.com/photo-1583394838336-acd977736f90?w=400",
        "cuisines": ["Chinese"],
        "diets": ["gluten-free", "dairy-free", "nut-allergy"],
        "readyInMinutes": 15,
        "servings": 4,
        "summary": "Diced chicken with peanuts and vegetables in spicy sauce",
        "extendedIngredients": [
            {"name": "chicken breast", "amount": 500, "unit": "g"},
            {"name": "roasted peanuts", "amount": 100, "unit": "g"},
            {"name": "dried chilies", "amount": 6, "unit": "pieces"},
            {"name": "soy sauce", "amount": 3, "unit": "tbsp"}
        ]
    },
    
    # American Cuisine
    {
        "id": 10014,
        "title": "Classic Burger with Fries",
        "image": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400",
        "cuisines": ["American"],
        "diets": ["dairy", "gluten"],
        "readyInMinutes": 25,
        "servings": 4,
        "summary": "Juicy beef patty with cheese, lettuce, tomato, and crispy fries",
        "extendedIngredients": [
            {"name": "ground beef", "amount": 600, "unit": "g"},
            {"name": "burger buns", "amount": 4, "unit": "pieces"},
            {"name": "cheddar cheese", "amount": 4, "unit": "slices"},
            {"name": "potatoes", "amount": 500, "unit": "g"}
        ]
    },
    {
        "id": 10015,
        "title": "BBQ Ribs",
        "image": "https://images.unsplash.com/photo-1544025162-d76694265947?w=400",
        "cuisines": ["American"],
        "diets": ["gluten-free", "dairy-free"],
        "readyInMinutes": 180,
        "servings": 6,
        "summary": "Slow-cooked pork ribs with smoky BBQ sauce",
        "extendedIngredients": [
            {"name": "pork ribs", "amount": 1500, "unit": "g"},
            {"name": "bbq sauce", "amount": 300, "unit": "ml"},
            {"name": "brown sugar", "amount": 50, "unit": "g"},
            {"name": "smoked paprika", "amount": 2, "unit": "tsp"}
        ]
    },
    {
        "id": 10016,
        "title": "Caesar Salad",
        "image": "https://images.unsplash.com/photo-1546793665-c74683f339c1?w=400",
        "cuisines": ["American"],
        "diets": ["vegetarian", "dairy", "gluten"],
        "readyInMinutes": 10,
        "servings": 4,
        "summary": "Crisp romaine lettuce with caesar dressing and croutons",
        "extendedIngredients": [
            {"name": "romaine lettuce", "amount": 2, "unit": "heads"},
            {"name": "parmesan cheese", "amount": 100, "unit": "g"},
            {"name": "croutons", "amount": 100, "unit": "g"},
            {"name": "caesar dressing", "amount": 150, "unit": "ml"}
        ]
    },
    
    # Japanese Cuisine
    {
        "id": 10017,
        "title": "Chicken Teriyaki Bowl",
        "image": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400",
        "cuisines": ["Japanese"],
        "diets": ["gluten-free", "dairy-free"],
        "readyInMinutes": 20,
        "servings": 4,
        "summary": "Grilled chicken with teriyaki glaze over steamed rice",
        "extendedIngredients": [
            {"name": "chicken thighs", "amount": 600, "unit": "g"},
            {"name": "teriyaki sauce", "amount": 150, "unit": "ml"},
            {"name": "jasmine rice", "amount": 300, "unit": "g"},
            {"name": "broccoli", "amount": 200, "unit": "g"}
        ]
    },
    {
        "id": 10018,
        "title": "Vegetable Sushi Rolls",
        "image": "https://images.unsplash.com/photo-1579584425555-c3ce17fd4351?w=400",
        "cuisines": ["Japanese"],
        "diets": ["vegetarian", "vegan", "gluten-free", "dairy-free"],
        "readyInMinutes": 30,
        "servings": 4,
        "summary": "Fresh cucumber, avocado, and carrot sushi rolls",
        "extendedIngredients": [
            {"name": "sushi rice", "amount": 300, "unit": "g"},
            {"name": "nori sheets", "amount": 6, "unit": "pieces"},
            {"name": "cucumber", "amount": 1, "unit": "large"},
            {"name": "avocado", "amount": 2, "unit": "pieces"}
        ]
    },
    {
        "id": 10019,
        "title": "Miso Soup",
        "image": "https://images.unsplash.com/photo-1607301405390-d831c6df3f0f?w=400",
        "cuisines": ["Japanese"],
        "diets": ["vegetarian", "vegan", "gluten-free", "dairy-free"],
        "readyInMinutes": 10,
        "servings": 4,
        "summary": "Traditional Japanese soup with tofu and seaweed",
        "extendedIngredients": [
            {"name": "miso paste", "amount": 3, "unit": "tbsp"},
            {"name": "silken tofu", "amount": 200, "unit": "g"},
            {"name": "wakame seaweed", "amount": 15, "unit": "g"},
            {"name": "green onions", "amount": 2, "unit": "stalks"}
        ]
    },
    
    # Thai Cuisine
    {
        "id": 10020,
        "title": "Pad Thai",
        "image": "https://images.unsplash.com/photo-1559314809-0f31657def5e?w=400",
        "cuisines": ["Thai"],
        "diets": ["gluten-free", "dairy-free"],
        "readyInMinutes": 15,
        "servings": 4,
        "summary": "Stir-fried rice noodles with shrimp, tofu, and peanuts",
        "extendedIngredients": [
            {"name": "rice noodles", "amount": 300, "unit": "g"},
            {"name": "shrimp", "amount": 300, "unit": "g"},
            {"name": "firm tofu", "amount": 200, "unit": "g"},
            {"name": "bean sprouts", "amount": 150, "unit": "g"}
        ]
    },
    {
        "id": 10021,
        "title": "Green Curry with Chicken",
        "image": "https://images.unsplash.com/photo-1455619452474-d2be8b1e70cd?w=400",
        "cuisines": ["Thai"],
        "diets": ["gluten-free", "dairy-free"],
        "readyInMinutes": 25,
        "servings": 4,
        "summary": "Spicy green curry with chicken and vegetables",
        "extendedIngredients": [
            {"name": "chicken breast", "amount": 500, "unit": "g"},
            {"name": "green curry paste", "amount": 3, "unit": "tbsp"},
            {"name": "coconut milk", "amount": 400, "unit": "ml"},
            {"name": "thai basil", "amount": 20, "unit": "leaves"}
        ]
    },
    {
        "id": 10022,
        "title": "Tom Yum Soup",
        "image": "https://images.unsplash.com/photo-1569562211093-4ed0d0758f12?w=400",
        "cuisines": ["Thai"],
        "diets": ["gluten-free", "dairy-free"],
        "readyInMinutes": 20,
        "servings": 4,
        "summary": "Spicy and sour Thai soup with shrimp and mushrooms",
        "extendedIngredients": [
            {"name": "shrimp", "amount": 400, "unit": "g"},
            {"name": "mushrooms", "amount": 200, "unit": "g"},
            {"name": "lemongrass", "amount": 2, "unit": "stalks"},
            {"name": "lime leaves", "amount": 4, "unit": "pieces"}
        ]
    },
    
    # Mediterranean Cuisine
    {
        "id": 10023,
        "title": "Greek Moussaka",
        "image": "https://images.unsplash.com/photo-1563379091339-03246963d719?w=400",
        "cuisines": ["Mediterranean", "Greek"],
        "diets": ["dairy", "gluten"],
        "readyInMinutes": 90,
        "servings": 8,
        "summary": "Layered eggplant casserole with meat sauce and bechamel",
        "extendedIngredients": [
            {"name": "eggplant", "amount": 2, "unit": "large"},
            {"name": "ground lamb", "amount": 500, "unit": "g"},
            {"name": "bechamel sauce", "amount": 500, "unit": "ml"},
            {"name": "feta cheese", "amount": 200, "unit": "g"}
        ]
    },
    {
        "id": 10024,
        "title": "Hummus with Vegetables",
        "image": "https://images.unsplash.com/photo-1571197119282-621c2694b15c?w=400",
        "cuisines": ["Mediterranean"],
        "diets": ["vegetarian", "vegan", "gluten-free", "dairy-free"],
        "readyInMinutes": 10,
        "servings": 6,
        "summary": "Creamy chickpea dip with fresh vegetables and pita",
        "extendedIngredients": [
            {"name": "chickpeas", "amount": 400, "unit": "g"},
            {"name": "tahini", "amount": 3, "unit": "tbsp"},
            {"name": "olive oil", "amount": 4, "unit": "tbsp"},
            {"name": "fresh vegetables", "amount": 500, "unit": "g"}
        ]
    },
    {
        "id": 10025,
        "title": "Mediterranean Fish",
        "image": "https://images.unsplash.com/photo-1544943910-4c1d10e74134?w=400",
        "cuisines": ["Mediterranean"],
        "diets": ["gluten-free", "dairy-free"],
        "readyInMinutes": 30,
        "servings": 4,
        "summary": "Grilled fish with herbs, olive oil, and lemon",
        "extendedIngredients": [
            {"name": "white fish fillets", "amount": 600, "unit": "g"},
            {"name": "olive oil", "amount": 4, "unit": "tbsp"},
            {"name": "fresh herbs", "amount": 30, "unit": "g"},
            {"name": "lemon", "amount": 2, "unit": "pieces"}
        ]
    },
    
    # French Cuisine
    {
        "id": 10026,
        "title": "Beef Bourguignon",
        "image": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400",
        "cuisines": ["French"],
        "diets": ["dairy-free"],
        "readyInMinutes": 150,
        "servings": 6,
        "summary": "Slow-braised beef in red wine with vegetables",
        "extendedIngredients": [
            {"name": "beef chuck", "amount": 1000, "unit": "g"},
            {"name": "red wine", "amount": 500, "unit": "ml"},
            {"name": "pearl onions", "amount": 300, "unit": "g"},
            {"name": "mushrooms", "amount": 250, "unit": "g"}
        ]
    },
    {
        "id": 10027,
        "title": "Ratatouille",
        "image": "https://images.unsplash.com/photo-1572441402740-96ba86b57c66?w=400",
        "cuisines": ["French"],
        "diets": ["vegetarian", "vegan", "gluten-free", "dairy-free"],
        "readyInMinutes": 45,
        "servings": 6,
        "summary": "Traditional French vegetable stew with herbs",
        "extendedIngredients": [
            {"name": "eggplant", "amount": 1, "unit": "large"},
            {"name": "zucchini", "amount": 2, "unit": "medium"},
            {"name": "bell peppers", "amount": 2, "unit": "pieces"},
            {"name": "tomatoes", "amount": 4, "unit": "large"}
        ]
    },
    {
        "id": 10028,
        "title": "Coq au Vin",
        "image": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400",
        "cuisines": ["French"],
        "diets": [],
        "readyInMinutes": 120,
        "servings": 4,
        "summary": "Chicken braised in white wine with vegetables",
        "extendedIngredients": [
            {"name": "chicken pieces", "amount": 1200, "unit": "g"},
            {"name": "white wine", "amount": 400, "unit": "ml"},
            {"name": "bacon", "amount": 150, "unit": "g"},
            {"name": "mushrooms", "amount": 200, "unit": "g"}
        ]
    },
    
    # Korean Cuisine
    {
        "id": 10029,
        "title": "Bibimbap",
        "image": "https://images.unsplash.com/photo-1553056061-7b7b07b44d8a?w=400",
        "cuisines": ["Korean"],
        "diets": ["vegetarian", "gluten-free", "dairy-free"],
        "readyInMinutes": 30,
        "servings": 4,
        "summary": "Mixed rice bowl with vegetables, egg, and gochujang",
        "extendedIngredients": [
            {"name": "short grain rice", "amount": 300, "unit": "g"},
            {"name": "mixed vegetables", "amount": 400, "unit": "g"},
            {"name": "eggs", "amount": 4, "unit": "large"},
            {"name": "gochujang", "amount": 3, "unit": "tbsp"}
        ]
    },
    {
        "id": 10030,
        "title": "Korean Fried Chicken",
        "image": "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=400",
        "cuisines": ["Korean"],
        "diets": ["dairy-free"],
        "readyInMinutes": 45,
        "servings": 4,
        "summary": "Crispy fried chicken with sweet and spicy glaze",
        "extendedIngredients": [
            {"name": "chicken wings", "amount": 1000, "unit": "g"},
            {"name": "potato starch", "amount": 100, "unit": "g"},
            {"name": "gochujang", "amount": 3, "unit": "tbsp"},
            {"name": "rice vinegar", "amount": 2, "unit": "tbsp"}
        ]
    },
    
    # Healthy/Vegetarian Options
    {
        "id": 10031,
        "title": "Quinoa Buddha Bowl",
        "image": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400",
        "cuisines": ["Healthy"],
        "diets": ["vegetarian", "vegan", "gluten-free", "dairy-free"],
        "readyInMinutes": 25,
        "servings": 4,
        "summary": "Nutritious bowl with quinoa, roasted vegetables, and tahini dressing",
        "extendedIngredients": [
            {"name": "quinoa", "amount": 200, "unit": "g"},
            {"name": "sweet potato", "amount": 300, "unit": "g"},
            {"name": "kale", "amount": 150, "unit": "g"},
            {"name": "tahini", "amount": 3, "unit": "tbsp"}
        ]
    },
    {
        "id": 10032,
        "title": "Lentil Curry",
        "image": "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=400",
        "cuisines": ["Indian", "Healthy"],
        "diets": ["vegetarian", "vegan", "gluten-free", "dairy-free"],
        "readyInMinutes": 35,
        "servings": 6,
        "summary": "Protein-rich red lentils in aromatic curry sauce",
        "extendedIngredients": [
            {"name": "red lentils", "amount": 300, "unit": "g"},
            {"name": "coconut milk", "amount": 400, "unit": "ml"},
            {"name": "curry powder", "amount": 2, "unit": "tbsp"},
            {"name": "spinach", "amount": 200, "unit": "g"}
        ]
    },
    {
        "id": 10033,
        "title": "Avocado Toast",
        "image": "https://images.unsplash.com/photo-1541519227354-08fa5d50c44d?w=400",
        "cuisines": ["Healthy"],
        "diets": ["vegetarian", "vegan", "dairy-free"],
        "readyInMinutes": 5,
        "servings": 2,
        "summary": "Smashed avocado on whole grain toast with toppings",
        "extendedIngredients": [
            {"name": "whole grain bread", "amount": 4, "unit": "slices"},
            {"name": "avocados", "amount": 2, "unit": "large"},
            {"name": "cherry tomatoes", "amount": 150, "unit": "g"},
            {"name": "lemon juice", "amount": 2, "unit": "tbsp"}
        ]
    },
    
    # Vegan Options
    {
        "id": 10034,
        "title": "Vegan Mac and Cheese",
        "image": "https://images.unsplash.com/photo-1547558840-2891b5aa4e3b?w=400",
        "cuisines": ["American"],
        "diets": ["vegetarian", "vegan", "dairy-free"],
        "readyInMinutes": 20,
        "servings": 4,
        "summary": "Creamy pasta with cashew-based cheese sauce",
        "extendedIngredients": [
            {"name": "macaroni pasta", "amount": 300, "unit": "g"},
            {"name": "cashews", "amount": 150, "unit": "g"},
            {"name": "nutritional yeast", "amount": 4, "unit": "tbsp"},
            {"name": "unsweetened almond milk", "amount": 300, "unit": "ml"}
        ]
    },
    {
        "id": 10035,
        "title": "Chickpea Tikka Masala",
        "image": "https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=400",
        "cuisines": ["Indian"],
        "diets": ["vegetarian", "vegan", "gluten-free", "dairy-free"],
        "readyInMinutes": 30,
        "servings": 4,
        "summary": "Creamy tomato curry with protein-rich chickpeas",
        "extendedIngredients": [
            {"name": "chickpeas", "amount": 400, "unit": "g"},
            {"name": "coconut milk", "amount": 400, "unit": "ml"},
            {"name": "tomato paste", "amount": 3, "unit": "tbsp"},
            {"name": "garam masala", "amount": 2, "unit": "tsp"}
        ]
    },
    
    # Gluten-Free Options
    {
        "id": 10036,
        "title": "Grilled Salmon with Quinoa",
        "image": "https://images.unsplash.com/photo-1467003909585-2f8a72700288?w=400",
        "cuisines": ["Healthy"],
        "diets": ["gluten-free", "dairy-free"],
        "readyInMinutes": 25,
        "servings": 4,
        "summary": "Herb-crusted salmon with fluffy quinoa and vegetables",
        "extendedIngredients": [
            {"name": "salmon fillets", "amount": 600, "unit": "g"},
            {"name": "quinoa", "amount": 200, "unit": "g"},
            {"name": "asparagus", "amount": 300, "unit": "g"},
            {"name": "olive oil", "amount": 3, "unit": "tbsp"}
        ]
    },
    {
        "id": 10037,
        "title": "Stuffed Bell Peppers",
        "image": "https://images.unsplash.com/photo-1563379091339-03246963d719?w=400",
        "cuisines": ["Mediterranean"],
        "diets": ["gluten-free", "dairy"],
        "readyInMinutes": 45,
        "servings": 4,
        "summary": "Bell peppers stuffed with rice, vegetables, and cheese",
        "extendedIngredients": [
            {"name": "bell peppers", "amount": 4, "unit": "large"},
            {"name": "brown rice", "amount": 200, "unit": "g"},
            {"name": "ground turkey", "amount": 300, "unit": "g"},
            {"name": "mozzarella cheese", "amount": 150, "unit": "g"}
        ]
    },
    
    # Nut-Free Options
    {
        "id": 10038,
        "title": "Turkey Meatballs",
        "image": "https://images.unsplash.com/photo-1529692236671-f1f6cf9683ba?w=400",
        "cuisines": ["Italian"],
        "diets": ["gluten-free", "dairy", "nut-free"],
        "readyInMinutes": 30,
        "servings": 4,
        "summary": "Lean turkey meatballs in marinara sauce",
        "extendedIngredients": [
            {"name": "ground turkey", "amount": 500, "unit": "g"},
            {"name": "marinara sauce", "amount": 400, "unit": "ml"},
            {"name": "parmesan cheese", "amount": 100, "unit": "g"},
            {"name": "fresh basil", "amount": 20, "unit": "g"}
        ]
    },
    {
        "id": 10039,
        "title": "Vegetable Stir Fry",
        "image": "https://images.unsplash.com/photo-1512058454905-6b841e7ad132?w=400",
        "cuisines": ["Asian"],
        "diets": ["vegetarian", "vegan", "gluten-free", "dairy-free", "nut-free"],
        "readyInMinutes": 15,
        "servings": 4,
        "summary": "Quick stir-fried vegetables with ginger and garlic",
        "extendedIngredients": [
            {"name": "mixed vegetables", "amount": 500, "unit": "g"},
            {"name": "brown rice", "amount": 300, "unit": "g"},
            {"name": "soy sauce", "amount": 3, "unit": "tbsp"},
            {"name": "fresh ginger", "amount": 15, "unit": "g"}
        ]
    },
    
    # Quick & Easy Options
    {
        "id": 10040,
        "title": "Caprese Salad",
        "image": "https://images.unsplash.com/photo-1608897013039-887f21d8c804?w=400",
        "cuisines": ["Italian"],
        "diets": ["vegetarian", "gluten-free", "dairy", "nut-free"],
        "readyInMinutes": 10,
        "servings": 4,
        "summary": "Fresh mozzarella, tomatoes, and basil with balsamic",
        "extendedIngredients": [
            {"name": "fresh mozzarella", "amount": 250, "unit": "g"},
            {"name": "tomatoes", "amount": 3, "unit": "large"},
            {"name": "fresh basil", "amount": 20, "unit": "leaves"},
            {"name": "balsamic glaze", "amount": 3, "unit": "tbsp"}
        ]
    }
]

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

def register_recipe_routes(app, recipes_collection, mongo_available, in_memory_recipes):
    SPOONACULAR_API_KEY = "01f12ed117584307b5cba262f43a8d49"
    SPOONACULAR_URL = "https://api.spoonacular.com/recipes/complexSearch"
    
    # Initialize in-memory recipes with fallback data if empty and MongoDB not available
    if not mongo_available and len(in_memory_recipes) == 0:
        in_memory_recipes.extend(FALLBACK_RECIPES)
        print(f"Initialized in-memory storage with {len(FALLBACK_RECIPES)} fallback recipes")
    
    @app.route("/get_recipes", methods=["GET"])
    def get_recipes():
        start_time = time.time()
        query = request.args.get("query", "").strip()
        ingredient = request.args.get("ingredient", "").strip()
        
        # Check ChromaDB cache first
        cached_recipes = recipe_cache.get_cached_recipes(query, ingredient)
        if cached_recipes:
            print(f"Returning {len(cached_recipes)} cached recipes for query: '{query}', ingredient: '{ingredient}'")
            return jsonify({"results": cached_recipes})
        
        # If no search parameters, return some default popular recipes
        if not query and not ingredient:
            # First try MongoDB if available
            if mongo_available:
                try:
                    popular_recipes = list(recipes_collection.find().limit(12))
                    if popular_recipes:
                        print(f"Found {len(popular_recipes)} popular recipes from MongoDB")
                        recipe_cache.cache_recipes(popular_recipes, query, ingredient)
                        return JSONEncoder().encode({"results": popular_recipes})
                except Exception as e:
                    print(f"Error fetching popular recipes from MongoDB: {e}")
            
            # Fallback to in-memory recipes
            if in_memory_recipes:
                popular_fallback = in_memory_recipes[:12]  # Return first 12 as popular
                print(f"Found {len(popular_fallback)} popular recipes from fallback")
                recipe_cache.cache_recipes(popular_fallback, query, ingredient)
                return jsonify({"results": popular_fallback})
            
            # Last resort: try Spoonacular API
            try:
                params = {
                    "apiKey": SPOONACULAR_API_KEY,
                    "number": 12,
                    "addRecipeInformation": "true",
                    "sort": "popularity"
                }
                
                response = requests.get(SPOONACULAR_URL, params=params, timeout=5)
                if response.ok and 'application/json' in response.headers.get('Content-Type', ''):
                    data = response.json()
                    if "results" in data:
                        # Cache the results
                        recipe_cache.cache_recipes(data["results"], query, ingredient)
                        return jsonify(data)
            except Exception as e:
                print(f"Error fetching popular recipes from API: {e}")
            
            # If all fails, return empty results
            return jsonify({"results": []}), 200

        # Search with parameters
        results = []
        
        # First check MongoDB if available
        if mongo_available:
            try:
                search_query = {}
                if query:
                    search_query["title"] = {"$regex": query, "$options": "i"}
                if ingredient:
                    search_query["$or"] = [
                        {"extendedIngredients.name": {"$regex": ingredient, "$options": "i"}},
                        {"ingredients": {"$regex": ingredient, "$options": "i"}}
                    ]
                
                print(f"Searching MongoDB with query: {search_query}")
                db_results = list(recipes_collection.find(search_query).limit(10))
                print(f"MongoDB search returned {len(db_results)} results")
                
                if db_results:
                    print(f"Found {len(db_results)} recipes in database in {time.time() - start_time:.2f}s")
                    # Cache the MongoDB results
                    recipe_cache.cache_recipes(db_results, query, ingredient)
                    return JSONEncoder().encode({"results": db_results})
                else:
                    print("No results found in MongoDB, checking in-memory storage")
            except Exception as e:
                print(f"Error querying MongoDB: {e}")
        else:
            print("MongoDB not available, checking in-memory storage")
        
        # Search in-memory storage
        if in_memory_recipes:
            query_lower = query.lower() if query else ""
            ingredient_lower = ingredient.lower() if ingredient else ""
            
            for recipe in in_memory_recipes:
                title_match = not query or query_lower in recipe.get("title", "").lower()
                cuisine_match = not query or any(query_lower in cuisine.lower() for cuisine in recipe.get("cuisines", []))
                diet_match = not query or any(query_lower in diet.lower() for diet in recipe.get("diets", []))
                ingredient_match = not ingredient or any(
                    ingredient_lower in ing.get("name", "").lower() 
                    for ing in recipe.get("extendedIngredients", [])
                )
                
                if (title_match or cuisine_match or diet_match) and ingredient_match:
                    results.append(recipe)
                    
            if results:
                # Limit results and cache them
                results = results[:10]
                print(f"Found {len(results)} recipes in in-memory storage")
                recipe_cache.cache_recipes(results, query, ingredient)
                return jsonify({"results": results})
            else:
                print("No results found in in-memory storage")

        # If no local results, try Spoonacular API
        print("No results found locally, calling Spoonacular API")
        params = {
            "apiKey": SPOONACULAR_API_KEY,
            "number": 10,  # Limit to 10 results
            "addRecipeInformation": "true",
        }
        
        if query:
            params["query"] = query
        if ingredient:
            params["includeIngredients"] = ingredient

        try:
            # Use a short timeout to avoid hanging
            print(f"Calling Spoonacular API with params: {params}")
            response = requests.get(SPOONACULAR_URL, params=params, timeout=5)
            
            # Check if content type is JSON
            if 'application/json' not in response.headers.get('Content-Type', ''):
                return jsonify({
                    "error": f"API returned non-JSON response. Status: {response.status_code}",
                    "message": response.text[:100] + "..." # Show part of the response for debugging
                }), 500
                
            response.raise_for_status()  # Raise an error for HTTP failures
            data = response.json()

            if "results" not in data:
                return jsonify({"error": "Invalid response from Spoonacular"}), 500

            # Enhanced validation and processing for recipe titles
            for recipe in data["results"]:
                # Normalize diet names for consistent filtering
                if "diets" in recipe:
                    normalized_diets = []
                    for diet in recipe["diets"]:
                        diet_lower = diet.lower()
                        if "vegetarian" in diet_lower:
                            normalized_diets.append("vegetarian")
                        if "vegan" in diet_lower:
                            normalized_diets.append("vegan")
                        if "gluten" in diet_lower and "free" in diet_lower:
                            normalized_diets.append("gluten-free")
                        if "dairy" in diet_lower and "free" in diet_lower:
                            normalized_diets.append("dairy-free")
                        if "ketogenic" in diet_lower or "keto" in diet_lower:
                            normalized_diets.append("keto")
                        if "paleo" in diet_lower or "paleolithic" in diet_lower:
                            normalized_diets.append("paleo")
                        if "carnivore" in diet_lower or "meat" in diet_lower:
                            normalized_diets.append("carnivore")
                        # Keep the original diet as well
                        normalized_diets.append(diet)
                    recipe["diets"] = normalized_diets

                # Enhanced title validation and fixing with better logic
                title = recipe.get("title", "").strip()
                if not title or title.lower() in ["untitled", "untitled recipe", "", "recipe"] or "untitled" in title.lower():
                    # Generate a better title with multiple fallback strategies
                    new_title = None
                    
                    # Strategy 1: Use cuisines + dish types for more specific titles
                    if "cuisines" in recipe and recipe["cuisines"] and len(recipe["cuisines"]) > 0:
                        cuisine = recipe["cuisines"][0]
                        
                        # Check if we have dish types to make it more specific
                        if "dishTypes" in recipe and recipe["dishTypes"] and len(recipe["dishTypes"]) > 0:
                            dish_type = recipe["dishTypes"][0]
                            # Create more specific titles like "Italian Pasta" or "Mexican Main Course"
                            if dish_type.lower() not in cuisine.lower():
                                new_title = f"{cuisine} {dish_type.title()}"
                            else:
                                new_title = f"Classic {cuisine} {dish_type.title()}"
                        else:
                            # Use diet + cuisine if no dish types
                            if "diets" in recipe and recipe["diets"] and len(recipe["diets"]) > 0:
                                diet = recipe["diets"][0]
                                # Only use diet if it's descriptive (not technical)
                                if diet.lower() not in ["gluten free", "dairy free", "ketogenic"]:
                                    new_title = f"{diet.title()} {cuisine} Recipe"
                                else:
                                    new_title = f"Authentic {cuisine} Dish"
                            else:
                                new_title = f"Traditional {cuisine} Recipe"
                    
                    # Strategy 2: Use main ingredient from extendedIngredients
                    elif "extendedIngredients" in recipe and recipe["extendedIngredients"] and len(recipe["extendedIngredients"]) > 0:
                        main_ingredient = recipe["extendedIngredients"][0].get("name", "").strip()
                        if main_ingredient and len(main_ingredient) > 2:
                            # Clean up ingredient name and capitalize
                            clean_ingredient = main_ingredient.split(',')[0].split('(')[0].strip()
                            words = clean_ingredient.split()
                            if len(words) <= 3:  # Only use if it's not too long
                                formatted_ingredient = ' '.join(word.capitalize() for word in words)
                                
                                # Add cooking method if available in dishTypes
                                if "dishTypes" in recipe and recipe["dishTypes"]:
                                    cooking_style = recipe["dishTypes"][0]
                                    if any(method in cooking_style.lower() for method in ["grilled", "roasted", "baked", "fried", "steamed"]):
                                        new_title = f"{cooking_style.title()} {formatted_ingredient}"
                                    else:
                                        new_title = f"{formatted_ingredient} {cooking_style.title()}"
                                else:
                                    new_title = f"Homestyle {formatted_ingredient}"
                    
                    # Strategy 3: Use dishTypes with descriptive prefixes
                    elif "dishTypes" in recipe and recipe["dishTypes"] and len(recipe["dishTypes"]) > 0:
                        dish_type = recipe["dishTypes"][0]
                        new_title = f"Signature {dish_type.title()}"
                    
                    # Strategy 4: Generate appealing names based on recipe ID and available data
                    if not new_title:
                        recipe_id = recipe.get("id", "0")
                        
                        # Use diets to create appealing titles
                        if "diets" in recipe and recipe["diets"]:
                            diet = recipe["diets"][0]
                            if diet.lower() == "vegetarian":
                                new_title = f"Garden Fresh Recipe #{recipe_id}"
                            elif diet.lower() == "vegan":
                                new_title = f"Plant-Based Delight #{recipe_id}"
                            elif "mediterranean" in diet.lower():
                                new_title = f"Mediterranean Specialty #{recipe_id}"
                            else:
                                new_title = f"{diet.title()} Creation #{recipe_id}"
                        else:
                            # Generic but appealing fallbacks
                            appealing_prefixes = [
                                "Chef's Special", "Home Kitchen Favorite", "Comfort Food Classic",
                                "Family Recipe", "Restaurant Style", "Gourmet Creation"
                            ]
                            prefix = appealing_prefixes[int(str(recipe_id)[-1]) % len(appealing_prefixes)]
                            new_title = f"{prefix} #{recipe_id}"
                    
                    recipe["title"] = new_title
                    print(f"✨ Fixed recipe title: '{title}' → '{new_title}'")
                
                # Ensure consistent and organized cuisine data
                if "cuisines" not in recipe or not recipe["cuisines"]:
                    # Try to infer cuisine from title or dish types
                    inferred_cuisine = None
                    recipe_title = recipe.get("title", "").lower()
                    
                    # Map common cuisine indicators in titles
                    cuisine_indicators = {
                        "italian": ["pasta", "pizza", "risotto", "italian", "parmesan", "mozzarella"],
                        "mexican": ["taco", "burrito", "mexican", "salsa", "guacamole", "enchilada"],
                        "asian": ["stir fry", "teriyaki", "soy sauce", "ginger", "asian"],
                        "chinese": ["kung pao", "sweet and sour", "chow mein", "chinese"],
                        "indian": ["curry", "tikka", "masala", "indian", "turmeric", "cumin"],
                        "thai": ["pad thai", "thai", "coconut milk", "lemongrass"],
                        "japanese": ["sushi", "miso", "teriyaki", "japanese"],
                        "mediterranean": ["olive oil", "feta", "mediterranean", "greek"],
                        "american": ["burger", "bbq", "american", "classic"],
                        "french": ["french", "coq au vin", "bouillabaisse", "ratatouille"]
                    }
                    
                    for cuisine, indicators in cuisine_indicators.items():
                        if any(indicator in recipe_title for indicator in indicators):
                            inferred_cuisine = cuisine.title()
                            break
                    
                    # Set the inferred cuisine or default
                    recipe["cuisines"] = [inferred_cuisine or "International"]
                    print(f"🌍 Set cuisine for '{recipe.get('title')}': {recipe['cuisines']}")
                
                # Normalize cuisine names for consistency
                normalized_cuisines = []
                for cuisine in recipe.get("cuisines", []):
                    if cuisine:
                        # Standardize cuisine names
                        cuisine_lower = cuisine.lower().strip()
                        if cuisine_lower in ["italian", "italy"]:
                            normalized_cuisines.append("Italian")
                        elif cuisine_lower in ["mexican", "mexico"]:
                            normalized_cuisines.append("Mexican")
                        elif cuisine_lower in ["chinese", "china"]:
                            normalized_cuisines.append("Chinese")
                        elif cuisine_lower in ["indian", "india"]:
                            normalized_cuisines.append("Indian")
                        elif cuisine_lower in ["thai", "thailand"]:
                            normalized_cuisines.append("Thai")
                        elif cuisine_lower in ["japanese", "japan"]:
                            normalized_cuisines.append("Japanese")
                        elif cuisine_lower in ["american", "usa", "united states"]:
                            normalized_cuisines.append("American")
                        elif cuisine_lower in ["french", "france"]:
                            normalized_cuisines.append("French")
                        elif cuisine_lower in ["mediterranean", "greek", "greece"]:
                            normalized_cuisines.append("Mediterranean")
                        elif cuisine_lower in ["asian"]:
                            normalized_cuisines.append("Asian")
                        else:
                            # Capitalize the first letter for other cuisines
                            normalized_cuisines.append(cuisine.title())
                
                if normalized_cuisines:
                    recipe["cuisines"] = normalized_cuisines
                else:
                    recipe["cuisines"] = ["International"]

            # Cache the API results in ChromaDB
            recipe_cache.cache_recipes(data["results"], query, ingredient)

            # Store results in MongoDB for future queries
            api_store_count = 0
            try:
                if mongo_available:
                    for recipe in data["results"]:
                        # Ensure recipe has all necessary fields
                        if "title" not in recipe:
                            recipe["title"] = "Untitled Recipe"
                        if "cuisines" not in recipe or not recipe["cuisines"]:
                            recipe["cuisines"] = ["Misc"]
                            
                        # Check if recipe already exists in the database
                        try:
                            # Try with recipe ID as integer
                            existing = recipes_collection.find_one({"id": recipe["id"]})
                        except:
                            # If not an integer, try as string
                            existing = recipes_collection.find_one({"id": str(recipe["id"])})
                            
                        if not existing:
                            # Insert to MongoDB and ensure proper indexing
                            recipes_collection.insert_one(recipe)
                            api_store_count += 1
                    print(f"Stored {api_store_count} new recipes in MongoDB Atlas")
                else:
                    # Store in in-memory cache if MongoDB not available
                    for recipe in data["results"]:
                        if not any(r.get("id") == recipe["id"] for r in in_memory_recipes):
                            in_memory_recipes.append(recipe)
                    print(f"Stored {len(data['results'])} recipes in in-memory storage")
            except Exception as e:
                print(f"Error storing recipes: {e}")

            print(f"API request completed in {time.time() - start_time:.2f}s")
            return jsonify(data)  # Send results to frontend

        except requests.exceptions.Timeout:
            return jsonify({"error": "Request to Spoonacular API timed out", "results": []}), 504
        except ValueError as e:  # JSON parsing error
            return jsonify({
                "error": "Failed to parse API response as JSON",
                "message": str(e),
                "results": []
            }), 500
        except requests.exceptions.RequestException as e:
            return jsonify({"error": str(e), "results": []}), 500

    # Add a route to test specific queries and show cache usage
    @app.route("/test/query", methods=["GET"])
    def test_query():
        query = request.args.get("q", "")
        
        # Check cache first
        cached_recipes = recipe_cache.get_cached_recipes(query, "")
        if cached_recipes:
            return jsonify({
                "source": "cache",
                "query": query,
                "results": cached_recipes[:5],  # Return first 5 for testing
                "total_cached": len(cached_recipes)
            })
        
        # If not in cache, return message
        return jsonify({
            "source": "not_cached",
            "query": query,
            "message": f"Query '{query}' not found in cache. Try calling /get_recipes?query={query} first."
        })

    # Add a route to clear the cache
    @app.route("/cache/clear", methods=["POST"])
    def clear_cache():
        success = recipe_cache.clear_cache()
        if success:
            return jsonify({"message": "Cache cleared successfully"})
        else:
            return jsonify({"error": "Failed to clear cache"}), 500

    # Add a route to get cache statistics
    @app.route("/cache/stats", methods=["GET"])
    def get_cache_stats():
        stats = recipe_cache.get_cache_stats()
        return jsonify(stats)

    @app.route("/get_recipe_by_id", methods=["GET"])
    def get_recipe_by_id():
        recipe_id = request.args.get("id")
        if not recipe_id:
            return jsonify({"error": "Recipe ID is required"}), 400
        
        # First check if we have this recipe in MongoDB
        if mongo_available:
            try:
                # Try to find as integer ID (for external recipes)
                try:
                    db_recipe = recipes_collection.find_one({"id": int(recipe_id)})
                except ValueError:
                    # If not an integer, look for it as a string (for local recipes)
                    db_recipe = recipes_collection.find_one({"id": recipe_id})
                    
                if db_recipe:
                    print(f"Found recipe {recipe_id} in MongoDB database")
                    return JSONEncoder().encode(db_recipe)
            except Exception as e:
                print(f"Error querying MongoDB for recipe {recipe_id}: {e}")
        else:
            # Check in-memory storage
            for recipe in in_memory_recipes:
                if str(recipe.get("id")) == str(recipe_id):
                    print(f"Found recipe {recipe_id} in in-memory storage")
                    return jsonify(recipe)
        
        # If not in storage, call the Spoonacular API
        api_url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
        params = {"apiKey": SPOONACULAR_API_KEY}
        
        try:
            print(f"Calling Spoonacular API for recipe {recipe_id}")
            response = requests.get(api_url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            # Ensure recipe has all necessary fields
            if "title" not in data:
                data["title"] = "Untitled Recipe"
            if "cuisines" not in data or not data["cuisines"]:
                data["cuisines"] = ["Misc"]
            
            # Normalize diets for consistent filtering
            if "diets" in data:
                normalized_diets = []
                for diet in data["diets"]:
                    diet_lower = diet.lower()
                    if "vegetarian" in diet_lower:
                        normalized_diets.append("vegetarian")
                    if "vegan" in diet_lower:
                        normalized_diets.append("vegan")
                    if "gluten" in diet_lower and "free" in diet_lower:
                        normalized_diets.append("gluten-free")
                    if "carnivore" in diet_lower or "meat" in diet_lower:
                        normalized_diets.append("carnivore")
                    # Keep the original diet as well
                    normalized_diets.append(diet)
                data["diets"] = normalized_diets
                
            # Store in MongoDB for future queries
            try:
                if mongo_available:
                    existing = recipes_collection.find_one({"id": data["id"]})
                    if not existing:
                        recipes_collection.insert_one(data)
                        print(f"Stored recipe {recipe_id} in MongoDB Atlas")
                else:
                    # Store in in-memory cache
                    if not any(r.get("id") == data["id"] for r in in_memory_recipes):
                        in_memory_recipes.append(data)
                        print(f"Stored recipe {recipe_id} in in-memory storage")
            except Exception as e:
                print(f"Error storing recipe {recipe_id}: {e}")
            
            return jsonify(data)
        except requests.exceptions.Timeout:
            return jsonify({"error": "Request to Spoonacular API timed out"}), 504
        except requests.exceptions.RequestException as e:
            return jsonify({"error": str(e)}), 500

    # Endpoints for direct MongoDB CRUD operations
    @app.route("/recipes", methods=["GET"])
    def get_all_recipes():
        if not mongo_available:
            # Return fallback data when MongoDB is not available
            return jsonify({"results": in_memory_recipes}), 200
        
        try:
            recipes = list(recipes_collection.find())
            return JSONEncoder().encode({"results": recipes})
        except Exception as e:
            # If MongoDB query fails, return fallback data
            return jsonify({"results": in_memory_recipes}), 200

    @app.route("/recipes/<recipe_id>", methods=["GET"])
    def get_recipe_from_db(recipe_id):
        try:
            # First try MongoDB if available
            if mongo_available:
                try:
                    # Try first as ObjectId
                    try:
                        recipe = recipes_collection.find_one({"_id": ObjectId(recipe_id)})
                    except:
                        # Then try as regular id
                        recipe = recipes_collection.find_one({"id": recipe_id})
                        if not recipe:
                            try:
                                recipe = recipes_collection.find_one({"id": int(recipe_id)})
                            except ValueError:
                                pass
                                
                    if recipe:
                        return JSONEncoder().encode(recipe)
                except Exception as e:
                    print(f"MongoDB query failed: {e}")
            
            # If MongoDB not available or recipe not found, check fallback recipes
            try:
                recipe_id_int = int(recipe_id)
                for recipe in FALLBACK_RECIPES:
                    if recipe["id"] == recipe_id_int:
                        print(f"Found recipe {recipe_id} in fallback collection")
                        return jsonify(recipe)
            except ValueError:
                pass
            
            # If not in fallback, try Spoonacular API
            try:
                api_url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
                response = requests.get(api_url, params={
                    'apiKey': SPOONACULAR_API_KEY
                }, timeout=10)
                
                if response.status_code == 200:
                    recipe_data = response.json()
                    print(f"Found recipe {recipe_id} via Spoonacular API")
                    return jsonify(recipe_data)
                elif response.status_code == 402:
                    print(f"Spoonacular API quota exceeded for recipe {recipe_id}")
                else:
                    print(f"Spoonacular API error for recipe {recipe_id}: {response.status_code}")
            except Exception as e:
                print(f"Error calling Spoonacular API for recipe {recipe_id}: {e}")
            
            return jsonify({"error": "Recipe not found"}), 404
            
        except Exception as e:
            print(f"Error in get_recipe_from_db: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/recipes", methods=["POST"])
    def add_recipe_to_db():
        if not mongo_available:
            return jsonify({"error": "MongoDB not available"}), 503
        
        try:
            recipe = request.json
            if not recipe:
                return jsonify({"error": "Recipe data is required"}), 400
            
            # Ensure recipe has all necessary fields
            if "title" not in recipe:
                recipe["title"] = "Untitled Recipe"
                
            # If no ID is provided, generate one
            if "id" not in recipe:
                recipe["id"] = str(ObjectId())
                
            # Check if recipe already exists
            existing = None
            if "id" in recipe:
                try:
                    existing = recipes_collection.find_one({"id": recipe["id"]})
                except:
                    # Try as integer if string fails
                    try:
                        existing = recipes_collection.find_one({"id": int(recipe["id"])})
                    except ValueError:
                        pass
            
            if existing:
                recipes_collection.update_one({"id": recipe["id"]}, {"$set": recipe})
                return jsonify({"message": "Recipe updated", "id": recipe["id"]})
            else:
                result = recipes_collection.insert_one(recipe)
                return jsonify({"message": "Recipe added", "id": recipe["id"] if "id" in recipe else str(result.inserted_id)})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/recipes/<recipe_id>", methods=["PUT"])
    def update_recipe_in_db(recipe_id):
        if not mongo_available:
            return jsonify({"error": "MongoDB not available"}), 503
        
        try:
            recipe = request.json
            if not recipe:
                return jsonify({"error": "Recipe data is required"}), 400
            
            # Try to update by ObjectId first
            try:
                result = recipes_collection.update_one({"_id": ObjectId(recipe_id)}, {"$set": recipe})
            except:
                # Then try by regular id
                result = recipes_collection.update_one({"id": recipe_id}, {"$set": recipe})
                
            if result.matched_count == 0:
                return jsonify({"error": "Recipe not found"}), 404
            
            return jsonify({"message": "Recipe updated"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/recipes/<recipe_id>", methods=["DELETE"])
    def delete_recipe_from_db(recipe_id):
        if not mongo_available:
            return jsonify({"error": "MongoDB not available"}), 503
        
        try:
            # Try to delete by ObjectId first
            try:
                result = recipes_collection.delete_one({"_id": ObjectId(recipe_id)})
            except:
                # Then try by regular id
                result = recipes_collection.delete_one({"id": recipe_id})
                if result.deleted_count == 0:
                    try:
                        result = recipes_collection.delete_one({"id": int(recipe_id)})
                    except ValueError:
                        pass
                    
            if result.deleted_count == 0:
                return jsonify({"error": "Recipe not found"}), 404
            
            return jsonify({"message": "Recipe deleted"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
