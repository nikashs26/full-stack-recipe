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
  
  // Split by periods that are followed by a space, to keep sentences together
  const sentences = cleanDescription.split(/\.(?:\s+|\s*$)/);
  
  // Build paragraphs by combining sentences
  const paragraphs: string[] = [];
  let currentParagraph = '';
  
  sentences.forEach(sentence => {
    // Add the period back (except if it's the last empty item)
    const formattedSentence = sentence.trim() ? sentence.trim() + '.' : '';
    
    // Skip empty sentences
    if (!formattedSentence) return;
    
    // If adding this sentence would make the paragraph too long, start a new one
    if (currentParagraph && (currentParagraph.length + formattedSentence.length > maxParaLength || 
        // Also create a new paragraph if there's a clear topic change indicator
        /^(moreover|furthermore|however|nevertheless|in addition|additionally|first|second|third|finally|lastly|next|then|after that)/i.test(sentence.trim()))) {
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
  
  // Split by periods followed by space, or by numbered steps
  const possibleSteps = cleanInstructions.split(/\.\s+|\d+\.\s+/).filter(step => step.trim().length > 0);
  
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
