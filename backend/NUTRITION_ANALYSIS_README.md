# Nutrition Analysis Agent

This utility provides an AI-powered agent that analyzes recipes using Large Language Models (LLMs) to extract nutritional information including calories, carbohydrates, fat, and protein per serving.

## Overview

The Nutrition Analysis Agent is designed to be run **once** to populate nutritional data for all recipes in your cache. It uses multiple LLM services as fallbacks to ensure reliable analysis:

1. **OpenAI GPT-3.5-turbo** (Primary - requires API key)
2. **Ollama** (Local LLM - free, runs locally)
3. **Hugging Face** (Fallback - requires API key)

## Features

- **Batch Processing**: Analyze multiple recipes efficiently with configurable batch sizes
- **Multiple LLM Support**: Automatic fallback between different LLM services
- **Data Validation**: Ensures nutritional data is reasonable and complete
- **Cache Integration**: Updates recipes in your existing ChromaDB cache
- **Comprehensive Logging**: Detailed logs for monitoring and debugging
- **Error Handling**: Graceful handling of failures with detailed error reporting

## Prerequisites

### Required Dependencies
The following packages are already included in your `requirements.txt`:
- `openai` - For OpenAI API integration
- `requests` - For HTTP requests to Ollama and Hugging Face
- `python-dotenv` - For environment variable management

### Environment Variables
Ensure these are set in your `.env` file:

```bash
# OpenAI API (recommended for best results)
OPENAI_API_KEY=your_openai_api_key_here

# Ollama (local, free)
OLLAMA_URL=http://localhost:11434

# Hugging Face (optional fallback)
HUGGING_FACE_API_KEY=your_hf_api_key_here
```

### Ollama Setup (Optional but Recommended)
If you want to use the free local LLM option:

1. Install Ollama: https://ollama.ai/
2. Pull a model: `ollama pull llama3.2:latest`
3. Start the service: `ollama serve`

## Usage

### 1. Test the Agent

Before running on all recipes, test the agent with sample data:

```bash
cd backend
python test_nutrition_agent.py
```

This will test the agent with sample recipes and verify all components are working.

### 2. Analyze All Recipes

To analyze all recipes in your cache and add nutritional information:

```bash
cd backend
python scripts/analyze_all_recipes_nutrition.py --all
```

This will:
- Load all recipes from your ChromaDB cache
- Analyze each recipe using available LLM services
- Update recipes in the cache with nutrition data
- Save detailed results to JSON files
- Generate a summary report

### 3. Analyze Specific Recipes

To analyze only specific recipes by ID:

```bash
cd backend
python scripts/analyze_all_recipes_nutrition.py --specific-ids recipe1 recipe2 recipe3
```

### 4. Programmatic Usage

You can also use the agent in your own scripts:

```python
from services.nutrition_analysis_agent import NutritionAnalysisAgent

# Initialize the agent
agent = NutritionAnalysisAgent()

# Analyze a single recipe
result = await agent.analyze_recipe_nutrition(recipe_data)

# Analyze multiple recipes
results = await agent.analyze_multiple_recipes(recipes_list, batch_size=5)
```

## Output Files

The analysis generates several output files:

### 1. Nutrition Analysis Results
- **File**: `nutrition_analysis_results_{N}_recipes.json`
- **Content**: Detailed results for each recipe including nutrition data and metadata
- **Format**: JSON with success/error status for each recipe

### 2. Summary Report
- **File**: `nutrition_analysis_summary.json`
- **Content**: Overall statistics including success rate and counts
- **Format**: JSON summary with analysis metrics

### 3. Log File
- **File**: `nutrition_analysis.log`
- **Content**: Detailed logs of the analysis process
- **Format**: Structured logging with timestamps

## Recipe Data Structure

The agent expects recipes in this format:

```python
{
    'id': 'recipe_id',
    'title': 'Recipe Title',
    'servings': 4,
    'ingredients': [
        {'amount': 1, 'unit': 'cup', 'name': 'flour'},
        {'amount': 2, 'unit': 'eggs', 'name': 'eggs'}
    ],
    'instructions': [
        'Step 1: Mix ingredients',
        'Step 2: Bake at 350F'
    ]
}
```

## Nutrition Data Output

Successful analysis adds this structure to recipes:

```python
{
    'nutrition': {
        'calories': 350.0,
        'carbohydrates': 45.0,
        'fat': 12.0,
        'protein': 8.0
    },
    'nutrition_analyzed_at': '2024-01-15T10:30:00Z',
    'nutrition_llm_service': 'openai'
}
```

## Configuration Options

### Batch Size
Control how many recipes are processed simultaneously:

```python
# Default batch size is 3 (conservative)
results = await agent.analyze_multiple_recipes(recipes, batch_size=5)
```

### LLM Service Priority
The agent automatically tries services in this order:
1. OpenAI (best quality)
2. Ollama (free, local)
3. Hugging Face (fallback)

### Validation Settings
Nutrition data validation includes:
- Reasonable calorie ranges (0-5000 kcal per serving)
- Macro validation (carbs: 0-200g, fat: 0-100g, protein: 0-100g)
- Calorie-macro consistency (allowing 50% variance)

## Error Handling

The agent handles various error scenarios:

- **LLM Service Failures**: Automatic fallback to next available service
- **Invalid Responses**: Parsing and validation of LLM outputs
- **Network Issues**: Timeout handling and retry logic
- **Data Validation**: Ensures nutrition data is reasonable

## Performance Considerations

### Rate Limiting
- **OpenAI**: Respects API rate limits automatically
- **Ollama**: Local processing, no rate limits
- **Hugging Face**: Free tier rate limits apply

### Batch Processing
- Default batch size of 3 balances speed and reliability
- 1-second delay between batches to be respectful to services
- Concurrent processing within batches for efficiency

### Memory Usage
- Processes recipes in batches to manage memory
- No need to load all recipes into memory at once

## Troubleshooting

### Common Issues

1. **OpenAI API Errors**
   - Verify API key is valid and has sufficient credits
   - Check rate limits and usage quotas

2. **Ollama Connection Issues**
   - Ensure Ollama service is running: `ollama serve`
   - Verify the model is downloaded: `ollama list`
   - Check the URL in your `.env` file

3. **Hugging Face API Errors**
   - Verify API key is valid
   - Check free tier usage limits

4. **Recipe Data Issues**
   - Ensure recipes have required fields (id, title, ingredients, instructions)
   - Check that ingredients are properly formatted

### Debug Mode
Enable detailed logging by modifying the logging level in the script:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Integration with Existing Code

The nutrition data is automatically added to your existing recipe cache, so:

- **Recipe Service**: Will automatically include nutrition data when retrieving recipes
- **Search**: Nutrition data is included in recipe metadata for filtering
- **API Endpoints**: Nutrition information is available through existing recipe endpoints

## Cost Considerations

- **OpenAI**: ~$0.002 per recipe (GPT-3.5-turbo)
- **Ollama**: Free (local processing)
- **Hugging Face**: Free tier available

For 1000 recipes:
- OpenAI: ~$2.00
- Ollama: $0.00
- Hugging Face: $0.00 (within free tier limits)

## Best Practices

1. **Run Once**: This utility is designed to be run once to populate all recipes
2. **Test First**: Always test with a small batch before running on all recipes
3. **Monitor Logs**: Watch the log files for any issues during processing
4. **Backup Data**: Consider backing up your recipe cache before running
5. **Off-Peak Hours**: Run during off-peak hours to avoid rate limiting

## Support

If you encounter issues:

1. Check the log files for detailed error messages
2. Verify all environment variables are set correctly
3. Test with the sample script first
4. Check that LLM services are accessible

The agent is designed to be robust and will continue processing even if some recipes fail, providing detailed feedback on any issues encountered. 