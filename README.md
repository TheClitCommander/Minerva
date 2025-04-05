# Minerva

An advanced AI assistant that integrates multiple AI frameworks to provide enhanced capabilities for task automation, code generation, and autonomous execution.

## Project Overview

Minerva is built upon the foundation of the original Minerva AI project, focusing on enhanced framework integration and advanced capabilities. The system is designed to provide a unified interface for working with various AI frameworks, allowing you to leverage their strengths while maintaining a consistent interaction model.

## Features

- **Multi-Framework Integration**: Seamlessly integrates with multiple AI frameworks
  - AutoGPT Integration
  - LangChain Integration
  - HuggingFace Integration
  - GPT4All Integration
- **Multi-Model Architecture**: Intelligently selects the best model for each query
  - Parallel model processing
  - Quality-based response selection
  - Fallback mechanisms for model failures
- **Enhanced Model Selection**:
  - Zephyr-7B-Beta and Mistral-7B support
  - Automatic quantization for efficient memory usage
  - Device detection for GPU acceleration
- **Advanced Memory System**: Persistent memory for conversations and user preferences 
- **Voice Interface**: Optional voice command capabilities
- **CLI Interface**: Powerful command-line interface for all capabilities
- **Framework Selection**: Automatically selects the best framework for each task
- **Dynamic Response Formatting**: Customizable response styles based on user preferences
  - Adjustable response length, tone, and structure
  - Flexible response structure (paragraphs, bullet points, numbered lists, summaries)
  - Immediate preference changes via commands or settings panel
- **Multi-AI Coordination**: Real-time feedback syncing across AI instances
  - Centralized feedback collection and distribution
  - Cross-model preference sharing
  - Coordinated response generation
- **Feedback-Driven Refinements**: Self-improving responses based on user feedback
  - Feedback pattern analysis for identifying common issues
  - Adaptive response optimization based on feedback signals
  - UI adaptability for enhanced user experience
  - Response quality analytics dashboard
- **AI Decision-Making Enhancements**: Improved response selection and optimization
  - Context-aware decision trees for dynamic response tuning
  - Real-time AI model switching based on query complexity
  - Enhanced multi-AI coordination for optimal decisions
- **Modular Architecture**: Easy to extend with new capabilities
- **Web Interface**: Interactive web-based interface for user interaction
- **User Preference Manager**: Personalized settings for retrieval depth and response formatting
- **Dynamic Response Formatting**: Customizable response structures and tones based on user preferences

## Quick Start

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/minerva.git
   cd minerva
   ```

2. Run the setup script to install all dependencies:
   ```bash
   ./setup_minerva.sh
   ```

3. Verify the installation:
   ```bash
   ./verify_models.py
   ```

4. Start Minerva:
   ```bash
   source fresh_venv/bin/activate
   python run_minerva.py
   ```

### Testing the Multi-Model System

To test the multi-model integration:

```bash
./test_multi_model.py
```

This will run a series of test queries through each available model and evaluate the performance of the multi-model selection system.

## Project Structure

```
Minerva/
├── core/               # Core Minerva functionality
├── integrations/       # Framework integration modules
│   ├── base_integration.py      # Base class for all integrations
│   ├── framework_manager.py     # Framework management system
│   ├── autogpt_integration.py   # AutoGPT integration
│   ├── langchain_integration.py # LangChain integration
│   ├── huggingface_integration.py # HuggingFace integration
│   └── ...
├── interfaces/         # User interface modules
│   ├── cli_interface.py        # Command-line interface
│   ├── voice_interface.py      # Voice interface
│   ├── web_interface.py        # Web interface
│   └── ...
├── memory/             # Memory and state management
├── utils/              # Utility functions
├── minerva_logs/       # Log directory
├── minerva_cli.py      # Command-line interface
├── minerva_main.py     # Main entry point
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Components

### Framework Integrations

Minerva can integrate with multiple AI frameworks to leverage their strengths:

- **AutoGPT**: For autonomous task execution and problem-solving
- **LangChain**: For building applications with LLMs through composable chains
- **HuggingFace**: For accessing state-of-the-art transformer models

Each integration implements a common interface but can provide specialized capabilities.

### Memory System

Minerva includes a sophisticated persistent memory system that allows it to:

- Store and retrieve user preferences
- Remember important facts and context
- Maintain conversation history
- Extract insights from interactions

The memory system uses importance ratings, categories, and tags to organize information for efficient retrieval.

### User Preference Management

Minerva features a comprehensive User Preference Manager that allows personalization of:

- **Retrieval Depth**: Choose between Concise, Standard, and Deep Dive modes to control
  the amount of information retrieved and detail level in responses
- **Response Tone**: Select from Formal, Casual, or Neutral tones to match your communication style
- **Response Structure**: Format responses as Paragraphs, Bullet Points, Numbered Lists, or Summaries
  based on your reading preferences

User preferences are stored persistently and automatically applied to all interactions.

### Web Interface

Minerva includes a web-based user interface that provides:

- **Dashboard**: Overview of framework availability and recent memories
- **Chat Interface**: Interactive conversation with Minerva
- **Memory Management**: Add, search, and visualize memories
- **Settings Management**: Configure API keys, framework preferences, and interface options
- **User Preferences**: Control for retrieval depth, response tone, and response structure
- **Quick Preference Commands**: Use inline commands like `/concise`, `/formal`, or `/bullets` to adjust preferences during conversation

The web interface is built using:
- Flask for the backend server
- Bootstrap for responsive styling
- Socket.IO for real-time chat functionality

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Minerva.git
   cd Minerva
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. For optional features, install the relevant dependencies:
   
   a. For LangChain support:
   ```bash
   pip install langchain langchain_openai
   ```
   
   b. For HuggingFace support:
   ```bash
   pip install transformers huggingface_hub diffusers accelerate
   ```
   
   c. For voice interface:
   ```bash
   pip install SpeechRecognition pyttsx3 pyaudio
   ```

4. Set up your API keys (for OpenAI, HuggingFace, etc.) in a `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key
   HF_API_TOKEN=your_huggingface_token
   ```

5. Run the setup script:
   ```bash
   python setup.py install
   ```

## Usage

### Command Line Interface

Minerva provides a robust command-line interface for all its capabilities:

```bash
# Get help
minerva --help

# Generate code
minerva generate-code "Create a function to calculate Fibonacci numbers"

# Execute a task
minerva execute-task "Download the latest Covid data and create a visualization"

# Use a specific framework
minerva --framework langchain generate-code "Create an API for user authentication"

# List available frameworks
minerva list-frameworks

# List available capabilities
minerva list-capabilities
```

### Memory System Commands

```bash
# Add a memory
minerva memory add --content "User prefers dark mode" --category preference --tag ui --tag theme

# Search memories
minerva memory search --category preference
minerva memory search --tag ui
minerva memory search --query "dark mode"

# Start a conversation
minerva conversation start --user-id "user123"
# Output: Conversation started with ID: 3f4g5h6j

# Add messages to a conversation
minerva conversation add-message --conversation-id 3f4g5h6j --role user --content "Hello Minerva"
minerva conversation add-message --conversation-id 3f4g5h6j --role assistant --content "Hello! How can I help you today?"
```

### Web Interface

To start the web interface:

```bash
# Start with default settings (localhost:5000)
python run_web_interface.py

# Specify a different port
python run_web_interface.py --port 8080

# Run on all network interfaces
python run_web_interface.py --host 0.0.0.0

# Run in debug mode
python run_web_interface.py --debug
```

Then navigate to `http://localhost:5000` (or your custom host/port) in your web browser.

### Using Framework Integrations

Each integration offers different capabilities:

#### AutoGPT Integration

```python
from minerva_main import MinervaAI

minerva = MinervaAI()
result = minerva.execute_with_framework("AutoGPT", "execute_task", 
    "Analyze the sentiment of recent tweets about AI")
print(result)
```

#### LangChain Integration

```python
from minerva_main import MinervaAI

minerva = MinervaAI()
result = minerva.execute_with_framework("LangChain", "generate_code", 
    "Create a web scraper for news articles",
    context="language: python")
print(result["code"])
```

#### HuggingFace Integration

```python
from minerva_main import MinervaAI

minerva = MinervaAI()
result = minerva.execute_with_framework("HuggingFace", "execute_task", 
    "Summarize the following text",
    context="This is a long article about artificial intelligence...")
print(result["result"])
```

### Running the Demo

To see all the advanced features in action, run the demo script:

```bash
python demo_advanced_features.py
```

## Framework Integration

Minerva supports a variety of AI frameworks. To add your own:

1. Create a new integration file in the `integrations` directory
2. Inherit from the `BaseIntegration` class
3. Implement the required methods
4. Register your framework using the CLI or programmatically

## Roadmap

Future enhancements planned for Minerva include:

1. **Multi-Modal Interface Layer**: Add voice recognition and response capabilities
2. **Context and Memory Enhancement**: Implement persistent memory across sessions
3. **Hardware Integration**: Connect with smart home devices and sensors
4. **Advanced Cognitive Capabilities**: Enhance planning and reasoning abilities
5. **Self-Improvement Mechanisms**: Create automated feedback loops for learning
6. **User Experience & Trust Features**: Add personalization and explainability

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built upon the foundation of the original Minerva AI project
- Integrates with multiple open-source AI frameworks
