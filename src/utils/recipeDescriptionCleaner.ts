/**
 * Recipe Description Cleaner
 * 
 * This utility cleans up Spoonacular recipe descriptions by removing:
 * - HTML markup
 * - Pricing information
 * - Marketing text
 * - Spoonacular scores and links
 * - Unnecessary promotional content
 * 
 * It creates clean, simple descriptions focused on the recipe itself.
 */

export class RecipeDescriptionCleaner {
  private patternsToRemove: RegExp[] = [
    // HTML tags
    /<[^>]+>/g,
    
    // Pricing information
    /For <b>\$[\d.]+ per serving<\/b>/gi,
    /\$[\d.]+ per serving/gi,
    
    // Marketing percentages
    /<b>covers \d+%<\/b> of your daily requirements/gi,
    /covers \d+% of your daily requirements/gi,
    
    // Calorie and macro marketing
    /Watching your figure\? This .*? recipe has <b>[\d.]+ calories<\/b>, <b>[\d.]+g of protein<\/b>, and <b>[\d.]+g of fat<\/b> per serving\./gi,
    /This .*? recipe has <b>[\d.]+ calories<\/b>, <b>[\d.]+g of protein<\/b>, and <b>[\d.]+g of fat<\/b> per serving\./gi,
    
    // Serving and rating info
    /This recipe serves \d+\./gi,
    /\d+ people have tried and liked this recipe\./gi,
    
    // Cuisine marketing
    /This recipe is typical of .*? cuisine\./gi,
    
    // Spoonacular scores and links
    /Overall, this recipe earns a <b>solid spoonacular score of \d+%<\/b>/gi,
    /spoonacular score of \d+%/gi,
    /<a href="https:\/\/spoonacular\.com\/recipes\/.*?">.*?<\/a>/gi,
    /https:\/\/spoonacular\.com\/recipes\/.*?/gi,
    
    // Similar recipe links
    /.*? are very similar to this recipe\./gi,
    
    // Foodista attribution
    /It is brought to you by Foodista\./gi,
    
    // Generic marketing phrases
    /This .*? recipe/gi,
    /A mixture of .*? ingredients are all it takes to make this recipe so delicious\./gi,
    /From preparation to the plate, this recipe takes roughly <b>[\d.]+ minutes<\/b>\./gi,
  ];

  private extractPatterns: { [key: string]: RegExp } = {
    cookingTime: /<b>(\d+) minutes<\/b>/gi,
    cuisine: /typical of (\w+) cuisine/gi,
    ingredients: /A mixture of (.*?) ingredients/gi,
  };

  /**
   * Clean a recipe description by removing HTML and marketing content.
   */
  cleanDescription(description: string): string {
    if (!description) return "";

    // Decode HTML entities
    let cleaned = this.decodeHtmlEntities(description);

    // Remove only the most problematic patterns, keep more content
    const aggressivePatterns = [
      // HTML tags
      /<[^>]+>/g,
      
      // Most annoying marketing text
      /Watching your figure\?/gi,
      /For <b>\$[\d.]+ per serving<\/b>/gi,
      /covers \d+% of your daily requirements/gi,
      /It is brought to you by Foodista\./gi,
      /With a spoonacular score of \d+%/gi,
      /Users who liked this recipe also liked.*?\./gi,
      /This recipe is liked by \d+ foodies and cooks\./gi,
      /This dish is solid\./gi,
    ];

    // Apply aggressive cleaning
    for (const pattern of aggressivePatterns) {
      cleaned = cleaned.replace(pattern, '');
    }

    // Extract useful information (just cuisine and cooking time, no macros)
    const usefulInfo = this.extractUsefulInfo(description);

    // Create a clean description
    let cleanDesc = this.createCleanDescription(cleaned, usefulInfo);

    // Final cleanup
    cleanDesc = this.finalCleanup(cleanDesc);

    // If the cleaned description is too short, use fallback
    if (cleanDesc.length < 50 || cleanDesc.split(' ').length < 8) {
      cleanDesc = this.generateFallbackDescription(description, usefulInfo);
    }

    return cleanDesc;
  }

  /**
   * Clean multiple descriptions at once
   */
  cleanMultipleDescriptions(descriptions: string[]): string[] {
    return descriptions.map(desc => this.cleanDescription(desc)).filter(desc => desc);
  }

  private decodeHtmlEntities(text: string): string {
    const textarea = document.createElement('textarea');
    textarea.innerHTML = text;
    return textarea.value;
  }

  private extractUsefulInfo(description: string): { [key: string]: string } {
    const info: { [key: string]: string } = {};

    for (const [key, pattern] of Object.entries(this.extractPatterns)) {
      const match = pattern.exec(description);
      if (match && match[1]) {
        info[key] = match[1];
      }
    }

    return info;
  }

  private createCleanDescription(cleanedText: string, usefulInfo: { [key: string]: string }): string {
    // Instead of creating a very short description, let's clean the original text
    // and make it more natural while keeping more content
    
    let description = cleanedText;
    
    // Clean up common issues
    description = description.replace(/\s+/g, ' '); // Fix multiple spaces
    description = description.replace(/\.+/g, '.'); // Fix multiple periods
    description = description.replace(/,\s*,/g, ','); // Fix double commas
    
    // Remove any remaining marketing phrases
    description = description.replace(/Head to the store and pick up.*?today\./gi, '');
    description = description.replace(/This recipe is liked by \d+ foodies and cooks\./gi, '');
    description = description.replace(/This dish is solid\./gi, '');
    
    // Clean up the beginning to make it more natural
    description = description.replace(/^([^.!?]+) - ([^.!?]+) requires about/gi, '$1 ($2) takes about');
    description = description.replace(/^([^.!?]+) requires about/gi, '$1 takes about');
    
    // Make it more natural
    description = description.replace(/This lacto ovo vegetarian recipe has/gi, 'This vegetarian recipe features');
    description = description.replace(/This recipe has/gi, 'This recipe features');
    
    // Clean up the end
    description = description.replace(/\.\s*$/, ''); // Remove trailing period if exists
    
    // Ensure it ends with a period
    if (description && !description.endsWith('.')) {
      description += '.';
    }
    
    // If the description is still too short, add some context
    if (description.length < 100) {
      if (usefulInfo.cuisine) {
        description = `A classic ${usefulInfo.cuisine} dish. ${description}`;
      } else {
        description = `A delicious homemade recipe. ${description}`;
      }
    }
    
    return description;
  }

  private generateFallbackDescription(originalDescription: string, usefulInfo: { [key: string]: string }): string {
    // Create a more natural description from the original text
    let description = originalDescription;
    
    // Remove HTML tags but keep the text content
    description = description.replace(/<[^>]+>/g, '');
    
    // Remove the most problematic marketing text
    description = description.replace(/Watching your figure\?/gi, '');
    description = description.replace(/For \$\d+\.\d+ per serving/gi, '');
    description = description.replace(/\$\d+\.\d+ per serving/gi, '');
    description = description.replace(/covers \d+% of your daily requirements/gi, '');
    description = description.replace(/It is brought to you by Foodista\./gi, '');
    description = description.replace(/With a spoonacular score of \d+%/gi, '');
    description = description.replace(/Users who liked this recipe also liked.*?\./gi, '');
    description = description.replace(/This recipe is liked by \d+ foodies and cooks\./gi, '');
    description = description.replace(/This dish is solid\./gi, '');
    
    // Clean up the text
    description = description.replace(/\s+/g, ' ').trim();
    description = description.replace(/\.+/g, '.');
    
    // Make it more natural
    description = description.replace(/This recipe serves \d+\./gi, '');
    description = description.replace(/This recipe is typical of (.*?) cuisine\./gi, 'This is a classic $1 dish.');
    
    // Ensure it ends with a period
    if (description && !description.endsWith('.')) {
      description += '.';
    }
    
    // If the description is still too short, add some context
    if (description.length < 80) {
      if (usefulInfo.cuisine) {
        description = `A classic ${usefulInfo.cuisine} dish. ${description}`;
      } else {
        description = `A delicious homemade recipe. ${description}`;
      }
    }
    
    return description;
  }

  private finalCleanup(description: string): string {
    // Remove extra whitespace
    description = description.replace(/\s+/g, ' ');

    // Remove leading/trailing whitespace
    description = description.trim();

    // Remove any remaining HTML-like content
    description = description.replace(/<[^>]*>/g, '');

    // Remove any remaining URLs
    description = description.replace(/https?:\/\/[^\s]+/g, '');

    // Clean up punctuation
    description = description.replace(/\.+/g, '.');
    description = description.replace(/\s+/g, ' ');

    // Ensure it ends with a period
    if (description && !description.endsWith('.')) {
      description += '.';
    }

    return description;
  }
}

// Create a singleton instance
export const recipeDescriptionCleaner = new RecipeDescriptionCleaner();

// Convenience function
export const cleanRecipeDescription = (description: string): string => {
  return recipeDescriptionCleaner.cleanDescription(description);
};
