# Minerva AI Model Upgrade Guide

This document provides information about the recent upgrade to Minerva's AI model system and how to install the necessary dependencies.

## 🚀 What's New

Minerva now uses the powerful **Zephyr-7B-Beta** model from Hugging Face, which provides:
- More coherent and intelligent responses
- Better understanding of complex questions
- More accurate and relevant answers

The upgrade includes:
- 8-bit quantization for efficient operation on standard hardware
- Model-specific prompt engineering
- Optimized generation parameters
- Enhanced response extraction and validation

## 📋 Requirements

### Hardware Requirements

For optimal performance:
- **RAM**: At least 16GB (8GB minimum with more swapping)
- **Disk Space**: At least 10GB free for model storage
- **GPU**: Optional but recommended for faster inference (CUDA compatible)

### Installation

1. **Update Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **First-time Model Download**:
   When you first run Minerva after the upgrade, it will attempt to download the Zephyr model (approximately 4GB). This may take some time depending on your internet connection.

## ⚙️ Configuration Options

If you encounter memory issues or want to customize the model behavior:

### Using a Smaller Model

Edit `/web/app.py` and change:
```python
huggingface_model_name = "HuggingFaceH4/zephyr-7b-beta"
```

to a smaller model like:
```python
huggingface_model_name = "facebook/opt-350m"
```

### Disable 8-bit Quantization

If you have compatibility issues with bitsandbytes, you can disable quantization by editing the model loading code in `app.py`:

```python
model = AutoModelForCausalLM.from_pretrained(
    huggingface_model_name,
    device_map="auto",
    load_in_8bit=False  # Set to False to disable 8-bit quantization
)
```

## 🔍 Troubleshooting

If you encounter issues:

1. **Out of Memory Errors**:
   - Try using a smaller model
   - Ensure other memory-intensive applications are closed
   - Add more swap space to your system

2. **Slow Response Times**:
   - This is expected for the first few queries as the model warms up
   - Consider using a GPU if responses are consistently slow

3. **Installation Issues with bitsandbytes**:
   - On Windows: `pip install bitsandbytes-windows`
   - On older Linux: Try `pip install bitsandbytes==0.38.0`

4. **Model Download Failures**:
   - Check your internet connection
   - Try running with the fallback model by setting `huggingface_model_name = "distilgpt2"`

## 🧪 Testing the Upgrade

We've included a test script to validate the model upgrade without running the full application:

```bash
# Activate your virtual environment
source fresh_venv/bin/activate  # or your environment's activation command

# Run the test script with default settings
python test_model_upgrade.py

# Options:
# Disable 8-bit quantization if having compatibility issues
python test_model_upgrade.py --disable-8bit

# Force CPU usage instead of GPU 
python test_model_upgrade.py --use-cpu

# Test with a different model
python test_model_upgrade.py --model facebook/opt-350m
```

The test script will:
1. Load the model with your specified settings
2. Run a series of test questions through the model
3. Display the formatted prompts and responses
4. Help identify any issues with the upgrade

This is a good way to confirm the model works correctly before running the full application.

## 📬 Feedback

We're continuously improving Minerva! If you encounter issues or have suggestions, please report them.
