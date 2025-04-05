/**
 * Concept Extractor for Minerva Conversations
 * Extracts the main concept or topic from a conversation
 */

class ConceptExtractor {
  /**
   * Extract a concept name from a conversation
   * @param {Array} messages - Array of conversation messages
   * @returns {String} - Extracted concept name
   */
  static extractConcept(messages) {
    if (!messages || messages.length === 0) {
      return this.generateFallbackTitle();
    }

    try {
      // Try to identify the main topic from the first few messages
      let combinedText = '';
      // Take up to first 3 messages to extract concept
      const sampleSize = Math.min(messages.length, 3);
      
      for (let i = 0; i < sampleSize; i++) {
        combinedText += messages[i].content + ' ';
      }
      
      // Extract key phrases and potential concepts
      const concepts = this.extractKeyPhrases(combinedText);
      
      if (concepts && concepts.length > 0) {
        // Use the most relevant concept as the title
        return this.formatConceptTitle(concepts[0]);
      }
      
      // If no concepts found, use the first user message as a basis
      const firstUserMsg = messages.find(msg => msg.role === 'user');
      if (firstUserMsg) {
        return this.titleFromUserMessage(firstUserMsg.content);
      }
      
      return this.generateFallbackTitle();
    } catch (error) {
      console.error('Error extracting concept:', error);
      return this.generateFallbackTitle();
    }
  }
  
  /**
   * Extract key phrases from text
   * @param {String} text - Text to analyze
   * @returns {Array} - List of potential concepts
   */
  static extractKeyPhrases(text) {
    // Simple implementation using keyword extraction
    const concepts = [];
    
    // Remove common words and punctuation
    const cleanText = text.toLowerCase()
      .replace(/[^\w\s]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
    
    // Split into words
    const words = cleanText.split(' ');
    
    // Filter out common stop words
    const stopWords = ['the', 'and', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'about', 'like', 'through'];
    const filteredWords = words.filter(word => !stopWords.includes(word) && word.length > 2);
    
    // Count word frequency
    const wordCounts = {};
    filteredWords.forEach(word => {
      wordCounts[word] = (wordCounts[word] || 0) + 1;
    });
    
    // Convert to array and sort by frequency
    const sortedWords = Object.entries(wordCounts)
      .sort((a, b) => b[1] - a[1])
      .map(entry => entry[0]);
    
    // Take the top 3 words
    const topWords = sortedWords.slice(0, 3);
    
    // If we have at least 2 words, combine the top 2 as a potential concept
    if (topWords.length >= 2) {
      concepts.push(`${topWords[0]} ${topWords[1]}`);
    }
    
    // Add the top word on its own
    if (topWords.length > 0) {
      concepts.push(topWords[0]);
    }
    
    return concepts;
  }
  
  /**
   * Format a concept into a title
   * @param {String} concept - Raw concept text
   * @returns {String} - Formatted title
   */
  static formatConceptTitle(concept) {
    // Capitalize words
    return concept.split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ') + ' Discussion';
  }
  
  /**
   * Generate a title from user message
   * @param {String} message - User message
   * @returns {String} - Generated title
   */
  static titleFromUserMessage(message) {
    // Take first 4-5 words of user message as title
    const words = message.split(' ');
    const titleWords = words.slice(0, Math.min(words.length, 5));
    
    // Add ellipsis if truncated
    let title = titleWords.join(' ');
    if (words.length > 5) {
      title += '...';
    }
    
    return title;
  }
  
  /**
   * Generate a fallback title with timestamp
   * @returns {String} - Fallback title
   */
  static generateFallbackTitle() {
    const now = new Date();
    return `Chat - ${now.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;
  }
}

// Make available globally
window.ConceptExtractor = ConceptExtractor;
