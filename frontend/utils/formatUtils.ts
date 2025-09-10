/**
 * Formats a text description into paragraphs for better readability
 * This will create paragraph breaks at natural points in the text
 * @param description The text to format
 * @param maxParaLength Maximum length for each paragraph
 * @returns Formatted HTML with paragraph tags
 */
export const formatDescriptionIntoParagraphs = (description: string, maxParaLength: number = 150): string => {
  if (!description) return '';
  
  // First, clean any HTML tags
  const cleanDescription = description.replace(/<\/?[^>]+(>|$)/g, '');
  
  // Look for natural paragraph breaks first
  let paragraphs: string[] = cleanDescription.split(/\n+/).filter(p => p.trim().length > 0);
  
  // If no natural breaks or paragraphs are too long, split by periods
  if (paragraphs.length <= 1 || paragraphs.some(p => p.length > maxParaLength * 1.5)) {
    paragraphs = [];
    // Split by periods that are followed by a space, to keep sentences together
    const sentences = cleanDescription.split(/\.(?:\s+|\s*$)/);
    
    let currentParagraph = '';
    
    sentences.forEach(sentence => {
      // Add the period back (except if it's the last empty item)
      const formattedSentence = sentence.trim() ? sentence.trim() + '.' : '';
      
      // If adding this sentence would make the paragraph too long, start a new one
      if (currentParagraph && currentParagraph.length + formattedSentence.length > maxParaLength) {
        paragraphs.push(currentParagraph);
        currentParagraph = formattedSentence;
      } else {
        // Otherwise, add to the current paragraph with a space if needed
        currentParagraph += (currentParagraph && formattedSentence ? ' ' : '') + formattedSentence;
      }
    });
    
    // Add the last paragraph if it's not empty
    if (currentParagraph) {
      paragraphs.push(currentParagraph);
    }
  }
  
  // Convert to HTML paragraphs
  return paragraphs.map(p => `<p>${p}</p>`).join('');
};

/**
 * Format instructions into cleaner, more readable steps
 * @param instructions Raw instructions string
 * @returns Array of formatted instruction steps
 */
export const formatInstructions = (instructions: string): string[] => {
  if (!instructions) return [];
  
  // Clean HTML tags
  const cleanInstructions = instructions.replace(/<[^>]*>/g, '');
  
  // More intelligent splitting that looks for actual step numbers, not just any number
  // Look for numbers at the beginning of lines or after periods, but not in the middle of sentences
  const stepPattern = /(?:\b(?:Step\s*)?\d+[.)]|\n\s*\d+[.)]|^\s*\d+[.)])/;
  const possibleSteps = cleanInstructions.split(stepPattern).filter(step => step.trim().length > 0);
  
  // If we have very few steps, try to further split long steps
  if (possibleSteps.length < 3 && possibleSteps.some(step => step.length > 100)) {
    return possibleSteps.flatMap(step => {
      if (step.length > 100) {
        // Try to split by common conjunctions that might indicate a new step
        return step.split(/\s+(?:Then|Next|After that|Finally),?\s+/i)
          .filter(s => s.trim().length > 0)
          .map(s => s.trim());
      }
      return step.trim();
    });
  }
  
  return possibleSteps.map(step => step.trim());
};
