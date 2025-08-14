#!/usr/bin/env python3
"""
Recipe Description Cleaner

This utility cleans up Spoonacular recipe descriptions by removing:
- HTML markup
- Pricing information
- Marketing text
- Spoonacular scores and links
- Unnecessary promotional content

It creates clean, simple descriptions focused on the recipe itself.
"""

import re
import html
from typing import Optional

class RecipeDescriptionCleaner:
    """Clean and simplify recipe descriptions"""
    
    def __init__(self):
        # Patterns to remove from descriptions
        self.patterns_to_remove = [
            # HTML tags
            r'<[^>]+>',
            
            # Pricing information
            r'For <b>\$[\d.]+ per serving</b>',
            r'\$[\d.]+ per serving',
            
            # Marketing percentages
            r'<b>covers \d+%</b> of your daily requirements',
            r'covers \d+% of your daily requirements',
            
            # Calorie and macro marketing
            r'Watching your figure\? This .*? recipe has <b>[\d.]+ calories</b>, <b>[\d.]+g of protein</b>, and <b>[\d.]+g of fat</b> per serving\.',
            r'This .*? recipe has <b>[\d.]+ calories</b>, <b>[\d.]+g of protein</b>, and <b>[\d.]+g of fat</b> per serving\.',
            
            # Serving and rating info
            r'This recipe serves \d+\.',
            r'\d+ people have tried and liked this recipe\.',
            
            # Cuisine marketing
            r'This recipe is typical of .*? cuisine\.',
            
            # Spoonacular scores and links
            r'Overall, this recipe earns a <b>solid spoonacular score of \d+%</b>',
            r'spoonacular score of \d+%',
            r'<a href="https://spoonacular\.com/recipes/.*?">.*?</a>',
            r'https://spoonacular\.com/recipes/.*?',
            
            # Similar recipe links
            r'.*? are very similar to this recipe\.',
            
            # Foodista attribution
            r'It is brought to you by Foodista\.',
            
            # Generic marketing phrases
            r'This .*? recipe',
            r'A mixture of .*? ingredients are all it takes to make this recipe so delicious\.',
            r'From preparation to the plate, this recipe takes roughly <b>[\d.]+ minutes</b>\.',
        ]
        
        # Patterns to extract useful information
        self.extract_patterns = {
            'cooking_time': r'<b>(\d+) minutes</b>',
            'calories': r'<b>(\d+) calories</b>',
            'protein': r'<b>(\d+g) of protein</b>',
            'fat': r'<b>(\d+g) of fat</b>',
            'cuisine': r'typical of (\w+) cuisine',
            'ingredients': r'A mixture of (.*?) ingredients',
            'ingredients_alt': r'ingredients are all it takes to make this recipe so delicious',
        }
    
    def clean_description(self, description: str) -> str:
        """
        Clean a recipe description by removing HTML and marketing content.
        
        Args:
            description: Raw description from Spoonacular
            
        Returns:
            Clean, simple description
        """
        if not description:
            return ""
        
        # Decode HTML entities
        cleaned = html.unescape(description)
        
        # Remove all unwanted patterns
        for pattern in self.patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Extract useful information
        useful_info = self._extract_useful_info(description)
        
        # Create a clean description
        clean_desc = self._create_clean_description(cleaned, useful_info)
        
        # Final cleanup
        clean_desc = self._final_cleanup(clean_desc)
        
        # If the cleaned description is too short or doesn't make sense, use fallback
        if len(clean_desc) < 30 or clean_desc.count(' ') < 5:
            clean_desc = self._generate_fallback_description(description, useful_info)
        
        return clean_desc
    
    def _extract_useful_info(self, description: str) -> dict:
        """Extract useful information from the description"""
        info = {}
        
        for key, pattern in self.extract_patterns.items():
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                # Check if the pattern has capture groups
                if '(' in pattern and ')' in pattern:
                    try:
                        info[key] = match.group(1)
                    except IndexError:
                        # No capture group, skip this pattern
                        continue
                else:
                    # Pattern without capture groups, just mark as found
                    info[key] = True
        
        return info
    
    def _create_clean_description(self, cleaned_text: str, useful_info: dict) -> str:
        """Create a clean description using extracted information"""
        # Build a natural description
        description_parts = []
        
        # Start with recipe type
        if useful_info.get('cuisine'):
            description_parts.append(f"A classic {useful_info['cuisine']} dish")
        else:
            description_parts.append("A delicious homemade dish")
        
        # Add cooking time
        if useful_info.get('cooking_time'):
            description_parts.append(f"that takes approximately {useful_info['cooking_time']} minutes to prepare")
        
        # Add ingredient highlights
        if useful_info.get('ingredients'):
            ingredients = useful_info['ingredients']
            # Clean up ingredients
            ingredients = re.sub(r',+', ',', ingredients)
            ingredients = ingredients.strip(', ')
            if ingredients and len(ingredients) > 5:
                description_parts.append(f"featuring fresh {ingredients}")
        
        # Add nutrition summary
        nutrition_info = []
        if useful_info.get('calories'):
            nutrition_info.append(f"{useful_info['calories']} calories")
        if useful_info.get('protein'):
            nutrition_info.append(f"{useful_info['protein']} protein")
        if useful_info.get('fat'):
            nutrition_info.append(f"{useful_info['fat']}")
        
        if nutrition_info:
            description_parts.append(f"with {', '.join(nutrition_info)} per serving")
        
        # Combine all parts
        if description_parts:
            description = ' '.join(description_parts) + "."
        else:
            description = "A delicious homemade recipe perfect for any meal."
        
        # Ensure proper capitalization
        description = description[0].upper() + description[1:]
        
        return description
    
    def _final_cleanup(self, description: str) -> str:
        """Final cleanup of the description"""
        # Remove extra whitespace
        description = re.sub(r'\s+', ' ', description)
        
        # Remove leading/trailing whitespace
        description = description.strip()
        
        # Remove any remaining HTML-like content
        description = re.sub(r'<[^>]*>', '', description)
        
        # Remove any remaining URLs
        description = re.sub(r'https?://[^\s]+', '', description)
        
        # Clean up punctuation
        description = re.sub(r'\.+', '.', description)
        description = re.sub(r'\s+', ' ', description)
        
        # Ensure it ends with a period
        if description and not description.endswith('.'):
            description += '.'
        
        return description
    
    def _generate_fallback_description(self, original_description: str, useful_info: dict) -> str:
        """Generate a fallback description when cleaning doesn't work well"""
        parts = []
        
        # Try to extract recipe name from the beginning
        recipe_name_match = re.search(r'^([^.!?]+)', original_description)
        if recipe_name_match:
            recipe_name = recipe_name_match.group(1).strip()
            # Clean up the recipe name
            recipe_name = re.sub(r'<[^>]+>', '', recipe_name)
            recipe_name = re.sub(r'\s+', ' ', recipe_name).strip()
            if recipe_name and len(recipe_name) > 10:
                parts.append(f"{recipe_name}")
        
        # Add cuisine if available
        if useful_info.get('cuisine'):
            parts.append(f"is a classic {useful_info['cuisine']} dish")
        else:
            parts.append("is a delicious homemade dish")
        
        # Add cooking time if available
        if useful_info.get('cooking_time'):
            parts.append(f"that takes about {useful_info['cooking_time']} minutes to prepare")
        
        # Add nutrition info if available
        nutrition_parts = []
        if useful_info.get('calories'):
            nutrition_parts.append(f"{useful_info['calories']} calories")
        if useful_info.get('protein'):
            nutrition_parts.append(f"{useful_info['protein']} protein")
        if useful_info.get('fat'):
            nutrition_parts.append(f"{useful_info['fat']}")
        
        if nutrition_parts:
            parts.append(f"with {', '.join(nutrition_parts)} per serving")
        
        # Combine parts
        if parts:
            description = ' '.join(parts) + "."
        else:
            description = "A delicious homemade recipe perfect for any meal."
        
        # Capitalize first letter
        description = description[0].upper() + description[1:]
        
        return description
    
    def clean_multiple_descriptions(self, descriptions: list) -> list:
        """Clean multiple descriptions at once"""
        return [self.clean_description(desc) for desc in descriptions if desc]

# Example usage and testing
def test_description_cleaner():
    """Test the description cleaner with sample data"""
    cleaner = RecipeDescriptionCleaner()
    
    # Sample problematic description
    sample_description = """Easy Eggplant Parmesan might be a good recipe to expand your main course recipe box. For <b>$2.63 per serving</b>, this recipe <b>covers 21%</b> of your daily requirements of vitamins and minerals. Watching your figure? This gluten free, lacto ovo vegetarian, and primal recipe has <b>288 calories</b>, <b>21g of protein</b>, and <b>12g of fat</b> per serving. This recipe serves 4. 2 people have tried and liked this recipe. This recipe is typical of Mediterranean cuisine. A mixture of style cheese, onion, pasta sauce, and a handful of other ingredients are all it takes to make this recipe so delicious. From preparation to the plate, this recipe takes roughly <b>45 minutes</b>. It is brought to you by Foodista. Overall, this recipe earns a <b>solid spoonacular score of 64%</b>. <a href="https://spoonacular.com/recipes/easy-eggplant-parmesan-265330">Easy Eggplant Parmesan</a>, <a href="https://spoonacular.com/recipes/easy-eggplant-parmesan-1620099">Easy Eggplant Parmesan</a>, and <a href="https://spoonacular.com/recipes/easy-eggplant-parmesan-103890">Easy Eggplant Parmesan</a> are very similar to this recipe."""
    
    print("🧪 Testing Recipe Description Cleaner")
    print("=" * 50)
    
    print("\n📝 Original Description:")
    print(sample_description)
    
    print("\n✨ Cleaned Description:")
    cleaned = cleaner.clean_description(sample_description)
    print(cleaned)
    
    print("\n📊 Length Comparison:")
    print(f"Original: {len(sample_description)} characters")
    print(f"Cleaned: {len(cleaned)} characters")
    print(f"Reduction: {((len(sample_description) - len(cleaned)) / len(sample_description) * 100):.1f}%")

if __name__ == "__main__":
    test_description_cleaner()
