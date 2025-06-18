#!/bin/bash

# This script sets API keys for Minerva server
# Run with: source ./set_api_keys.sh 

# Clear previous echo
clear

echo "🔑 Setting API keys for Minerva..."

# OpenAI
if [ -z "$OPENAI_API_KEY" ]; then
  # Only prompt if not already set
  while true; do
    read -p "Enter OpenAI API key (or press Enter to skip): " OPENAI_API_KEY
    
    # Skip if empty
    if [ -z "$OPENAI_API_KEY" ]; then
      break
    fi
    
    # Validate format
    if [[ "$OPENAI_API_KEY" == sk-* ]] && [ ${#OPENAI_API_KEY} -gt 20 ]; then
      echo "✅ OpenAI API key format appears valid"
      break
    else
      echo "❌ Invalid format: OpenAI API keys should start with 'sk-'"
      echo "Try again or press Enter to skip"
      OPENAI_API_KEY=""
    fi
  done
fi

# Anthropic
if [ -z "$ANTHROPIC_API_KEY" ]; then
  # Only prompt if not already set
  while true; do
    read -p "Enter Anthropic API key (or press Enter to skip): " ANTHROPIC_API_KEY
    
    # Skip if empty
    if [ -z "$ANTHROPIC_API_KEY" ]; then
      break
    fi
    
    # Validate format
    if [[ "$ANTHROPIC_API_KEY" == sk-ant-* ]] && [ ${#ANTHROPIC_API_KEY} -gt 20 ]; then
      echo "✅ Anthropic API key format appears valid"
      break
    else
      echo "❌ Invalid format: Anthropic API keys should start with 'sk-ant-'"
      echo "Try again or press Enter to skip"
      ANTHROPIC_API_KEY=""
    fi
  done
fi

# Mistral
if [ -z "$MISTRAL_API_KEY" ]; then
  # Only prompt if not already set
  while true; do
    read -p "Enter Mistral API key (or press Enter to skip): " MISTRAL_API_KEY
    
    # Skip if empty
    if [ -z "$MISTRAL_API_KEY" ]; then
      break
    fi
    
    # Validate basic format (no specific prefix required)
    if [ ${#MISTRAL_API_KEY} -gt 20 ]; then
      echo "✅ Mistral API key length appears valid"
      break
    else
      echo "❌ Key appears too short for a Mistral API key"
      echo "Try again or press Enter to skip"
      MISTRAL_API_KEY=""
    fi
  done
fi

# HuggingFace
if [ -z "$HUGGINGFACE_API_KEY" ]; then
  # Only prompt if not already set
  while true; do
    read -p "Enter HuggingFace API key (or press Enter to skip): " HUGGINGFACE_API_KEY
    
    # Skip if empty
    if [ -z "$HUGGINGFACE_API_KEY" ]; then
      break
    fi
    
    # Validate format
    if [[ "$HUGGINGFACE_API_KEY" == hf_* ]] && [ ${#HUGGINGFACE_API_KEY} -gt 15 ]; then
      echo "✅ HuggingFace API key format appears valid"
      break
    else
      echo "❌ Invalid format: HuggingFace API keys should start with 'hf_'"
      echo "Try again or press Enter to skip"
      HUGGINGFACE_API_KEY=""
    fi
  done
fi

# Export the keys
export OPENAI_API_KEY=$OPENAI_API_KEY
export ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
export MISTRAL_API_KEY=$MISTRAL_API_KEY
export HUGGINGFACE_API_KEY=$HUGGINGFACE_API_KEY

# Helper function to mask keys for safe display
mask_key() {
  if [ -z "$1" ]; then
    echo "NOT SET"
    return
  fi
  
  local length=${#1}
  if [ $length -lt 8 ]; then
    echo "INVALID KEY"
    return
  fi
  
  local prefix=${1:0:7}
  local suffix=${1: -4}
  echo "${prefix}...${suffix}"
}

# Print status (safely masking keys)
echo ""
echo "API Key Status:"
echo "---------------"
if [ -n "$OPENAI_API_KEY" ]; then
  echo "✅ OpenAI API key: SET - $(mask_key $OPENAI_API_KEY)"
else
  echo "❌ OpenAI API key: NOT SET"
fi

if [ -n "$ANTHROPIC_API_KEY" ]; then
  echo "✅ Anthropic API key: SET - $(mask_key $ANTHROPIC_API_KEY)"  
else
  echo "❌ Anthropic API key: NOT SET"
fi

if [ -n "$MISTRAL_API_KEY" ]; then
  echo "✅ Mistral API key: SET - $(mask_key $MISTRAL_API_KEY)"
else
  echo "❌ Mistral API key: NOT SET"
fi

if [ -n "$HUGGINGFACE_API_KEY" ]; then
  echo "✅ HuggingFace API key: SET - $(mask_key $HUGGINGFACE_API_KEY)"
else
  echo "❌ HuggingFace API key: NOT SET"
fi

echo ""

# Check if any keys were set
if [ -n "$OPENAI_API_KEY" ] || [ -n "$ANTHROPIC_API_KEY" ] || [ -n "$MISTRAL_API_KEY" ] || [ -n "$HUGGINGFACE_API_KEY" ]; then
  echo "🚀 Ready to run the server with API keys!"
  echo "Run './run_minerva.sh' to start the server"
else
  echo "⚠️ No API keys set. Server will run in SIMULATION MODE."
  echo "You can still run './run_minerva.sh' but only simulated AI will be available."
fi
echo "---------------"

# Write keys to .env file if requested
echo ""
read -p "Would you like to save these API keys to .env file for future use? (y/n): " save_to_env
if [[ "$save_to_env" =~ ^[Yy]$ ]]; then
  # Create or update .env file
  echo "# Minerva Environment Configuration" > .env
  echo "# Generated on $(date)" >> .env
  echo "" >> .env
  
  # Add API keys
  if [ -n "$OPENAI_API_KEY" ]; then
    echo "OPENAI_API_KEY=$OPENAI_API_KEY" >> .env
  fi
  
  if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY" >> .env
  fi
  
  if [ -n "$MISTRAL_API_KEY" ]; then
    echo "MISTRAL_API_KEY=$MISTRAL_API_KEY" >> .env
  fi
  
  if [ -n "$HUGGINGFACE_API_KEY" ]; then
    echo "HUGGINGFACE_API_KEY=$HUGGINGFACE_API_KEY" >> .env
  fi
  
  # Add server config
  echo "" >> .env
  echo "# Server Configuration" >> .env
  echo "PORT=5505" >> .env
  echo "HOST=0.0.0.0" >> .env
  echo "FLASK_DEBUG=false" >> .env
  
  echo "✅ API keys saved to .env file"
  echo "⚠️ Make sure to keep this file secure and never commit it to version control"
fi 