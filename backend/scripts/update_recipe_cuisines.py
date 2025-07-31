import chromadb
from services.recipe_search_service import RecipeSearchService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_recipe_cuisines():
    try:
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(path="./chroma_db")
        collection = client.get_collection('recipe_details_cache')
        
        # Get all recipes
        all_recipes = collection.get(include=['metadatas', 'documents'])
        
        # Initialize search service for cuisine detection
        search_service = RecipeSearchService()
        
        updated_count = 0
        
        for i, (recipe_id, metadata, document) in enumerate(zip(
            all_recipes['ids'], 
            all_recipes['metadatas'], 
            all_recipes['documents']
        )):
            try:
                # Skip if already has a specific cuisine
                current_cuisine = metadata.get('cuisine', '').lower()
                if current_cuisine and current_cuisine not in ['', 'other', 'none', 'null']:
                    continue
                
                # Parse recipe data
                try:
                    recipe_data = {
                        'title': metadata.get('title', ''),
                        'ingredients': metadata.get('ingredients', '').split(',') if metadata.get('ingredients') else [],
                        **metadata
                    }
                except Exception as e:
                    logger.warning(f"Error parsing recipe {recipe_id}: {e}")
                    continue
                
                # Get normalized cuisine
                new_cuisine = search_service._normalize_cuisine('', recipe_data)
                
                # Update metadata
                metadata['cuisine'] = new_cuisine
                
                # Update in database
                collection.update(
                    ids=[recipe_id],
                    metadatas=[metadata]
                )
                
                updated_count += 1
                if updated_count % 10 == 0:
                    logger.info(f"Updated {updated_count} recipes so far...")
                
            except Exception as e:
                logger.error(f"Error processing recipe {recipe_id}: {e}")
                continue
        
        logger.info(f"Successfully updated cuisines for {updated_count} recipes")
        
    except Exception as e:
        logger.error(f"Error updating recipe cuisines: {e}")
        raise

if __name__ == "__main__":
    update_recipe_cuisines()
