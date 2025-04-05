/**
 * Mock Think Tank API
 * This file provides a simple mock API for the Think Tank
 * It responds to API requests when the actual Think Tank is unavailable
 */

// Create express server
const express = require('express');
const app = express();
const port = process.env.PORT || 3030;
const cors = require('cors');
const bodyParser = require('body-parser');

// Enable CORS for all routes
app.use(cors());
app.use(bodyParser.json());

// Sample conversation memory
const conversations = {};

// Health check endpoint
app.get('/api/think-tank/health', (req, res) => {
  res.json({ status: 'ok', version: '1.0.0' });
});

// Main API endpoint
app.post('/api/think-tank', (req, res) => {
  const { message, conversation_id, project } = req.body;
  
  console.log('Received message:', message);
  console.log('Conversation ID:', conversation_id);
  
  // Create or retrieve conversation
  if (!conversations[conversation_id]) {
    conversations[conversation_id] = [];
  }
  
  // Store the user message
  conversations[conversation_id].push({
    role: 'user',
    content: message,
    timestamp: Date.now()
  });
  
  // Generate response
  const response = generateResponse(message, conversations[conversation_id]);
  
  // Store the assistant response
  conversations[conversation_id].push({
    role: 'assistant',
    content: response,
    timestamp: Date.now() + 100
  });
  
  // Simulate some processing time
  setTimeout(() => {
    res.json({
      response: response,
      conversation_id: conversation_id,
      model_info: {
        models: [
          { name: 'mock-gpt4', contribution: 40 },
          { name: 'mock-claude', contribution: 30 },
          { name: 'mock-gemini', contribution: 30 }
        ]
      },
      project: project || 'general'
    });
  }, 500);
});

// Function to generate responses
function generateResponse(message, conversation) {
  // Simple keyword-based responses
  if (message.toLowerCase().includes('hello') || message.toLowerCase().includes('hi')) {
    return "Hello! I'm the Minerva Assistant. How can I help you today?";
  } else if (message.toLowerCase().includes('project')) {
    return "I can help you organize and manage your projects in Minerva. Would you like me to create a new project or help you with an existing one?";
  } else if (message.toLowerCase().includes('help')) {
    return "I'm here to assist you with your Minerva experience. I can help with project management, answer questions, or provide guidance on using the system.";
  } else if (message.toLowerCase().includes('thanks') || message.toLowerCase().includes('thank you')) {
    return "You're welcome! If you need anything else, just let me know.";
  } else {
    // More contextual response based on conversation history
    const conversationLength = conversation.length;
    
    if (conversationLength <= 2) {
      return `I've received your message: "${message}". How can I assist you further with this topic?`;
    } else if (conversationLength <= 4) {
      return `Based on our conversation so far, I think I understand what you're looking for. Can you provide more details about your specific needs regarding "${message.substring(0, 30)}..."?`;
    } else {
      return `I'm continuing to learn about your needs. Regarding "${message.substring(0, 30)}...", let me suggest a few approaches we could take to address this...`;
    }
  }
}

// Start server
app.listen(port, () => {
  console.log(`Mock Think Tank API listening at http://localhost:${port}`);
});
