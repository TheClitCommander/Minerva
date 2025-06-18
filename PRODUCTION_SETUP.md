# Minerva Production Setup Guide

This document provides instructions for configuring Minerva to use real AI models in production.

## API Keys Configuration

Minerva requires the following API keys to function with real models:

1. **OpenAI API Key** (for GPT-4 models)
   - Environment variable: `OPENAI_API_KEY`
   - [Get API key from OpenAI](https://platform.openai.com/account/api-keys)

2. **Anthropic API Key** (for Claude-3 models)
   - Environment variable: `ANTHROPIC_API_KEY`
   - [Get API key from Anthropic](https://console.anthropic.com/keys)

3. **Mistral API Key** (for Mistral models)
   - Environment variable: `MISTRAL_API_KEY`
   - [Get API key from Mistral](https://console.mistral.ai/)

4. **Cohere API Key** (for Cohere models)
   - Environment variable: `COHERE_API_KEY`
   - [Get API key from Cohere](https://dashboard.cohere.ai/api-keys)

5. **HuggingFace API Token** (for HuggingFace models)
   - Environment variable: `HUGGINGFACE_API_TOKEN`
   - [Get API token from HuggingFace](https://huggingface.co/settings/tokens)

## Setting Up Environment Variables

1. Create or edit the `.env` file in the root directory:
   ```
   OPENAI_API_KEY=your_openai_key_here
   ANTHROPIC_API_KEY=your_anthropic_key_here
   MISTRAL_API_KEY=your_mistral_key_here
   COHERE_API_KEY=your_cohere_key_here
   HUGGINGFACE_API_TOKEN=your_huggingface_token_here
   ```

2. Restart Minerva to load the new environment variables.

## Verifying Production Mode

Minerva will now operate in production mode with real models. The following changes have been made:

1. Simulated processors have been completely disabled
2. The system will log warnings if API keys are missing
3. Think Tank mode will only use real models that are available
4. The system will not fall back to simulations even if no API keys are provided

## Troubleshooting

If Minerva doesn't seem to be using real models, check the following:

1. Verify the `.env` file exists and contains valid API keys
2. Check the logs for API connection errors
3. Make sure at least one API key (preferably more) is correctly configured

The log will contain warnings for any missing API keys, like:
```
[API_CHECK] No OpenAI API key found in environment
```

## Recommended Models

For optimal performance, we recommend configuring at least:
- OpenAI API key for GPT-4
- Anthropic API key for Claude-3

These two models provide a strong foundation for most capabilities.
