#!/usr/bin/env python3
"""
Minerva AI Diagnostics Tool

This script checks the availability and functionality of all AI models integrated with Minerva.
"""

import os
import sys
import time
import json
import importlib
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("minerva_diagnostics")

def check_environment():
    """Check the Python environment and dependencies"""
    logger.info("Checking Python environment...")
    
    # Check Python version
    python_version = sys.version
    logger.info(f"Python version: {python_version}")
    
    # Check if running in a virtual environment
    in_venv = sys.prefix != sys.base_prefix
    logger.info(f"Running in virtual environment: {in_venv}")
    
    # Check key dependencies
    dependencies = [
        "flask", "flask_socketio", "eventlet", "torch", 
        "transformers", "gpt4all", "autogpt", "langchain",
        "psutil", "loguru", "huggingface_hub"
    ]
    
    available_deps = {}
    for dep in dependencies:
        try:
            module = importlib.import_module(dep)
            version = getattr(module, "__version__", "unknown")
            available_deps[dep] = {"available": True, "version": version}
        except ImportError:
            available_deps[dep] = {"available": False, "version": None}
    
    logger.info("Dependency check results:")
    for dep, status in available_deps.items():
        if status["available"]:
            logger.info(f"  ✅ {dep}: {status['version']}")
        else:
            logger.info(f"  ❌ {dep}: Not installed")
    
    return available_deps

def check_huggingface_models():
    """Check available HuggingFace models"""
    logger.info("Checking HuggingFace models...")
    
    try:
        # Import without loading models
        import transformers
        logger.info(f"Transformers version: {transformers.__version__}")
        
        # Check cache directory for downloaded models
        cache_dir = os.path.expanduser("~/.cache/huggingface/")
        if os.path.exists(cache_dir):
            logger.info(f"HuggingFace cache directory exists: {cache_dir}")
            
            # Count model files
            model_count = 0
            for root, dirs, files in os.walk(cache_dir):
                model_count += len(files)
            
            logger.info(f"Found {model_count} files in HuggingFace cache")
        else:
            logger.info("HuggingFace cache directory not found")
        
        result = {
            "available": True,
            "version": transformers.__version__,
            "cache_exists": os.path.exists(cache_dir),
            "cached_files": model_count if 'model_count' in locals() else 0
        }
    except ImportError:
        logger.warning("HuggingFace Transformers not installed")
        result = {
            "available": False
        }
    
    return result

def check_gpt4all():
    """Check GPT4All availability and models"""
    logger.info("Checking GPT4All...")
    
    try:
        import gpt4all
        logger.info(f"GPT4All version: {getattr(gpt4all, '__version__', 'unknown')}")
        
        # Check models directory
        models_dir = os.path.expanduser("~/.cache/gpt4all")
        models_found = []
        
        if os.path.exists(models_dir):
            logger.info(f"GPT4All models directory exists: {models_dir}")
            
            # List model files
            for file in os.listdir(models_dir):
                if file.endswith(".bin") or file.endswith(".gguf"):
                    models_found.append(file)
            
            if models_found:
                logger.info(f"Found {len(models_found)} GPT4All models:")
                for model in models_found:
                    logger.info(f"  - {model}")
            else:
                logger.info("No GPT4All models found")
        else:
            logger.info("GPT4All models directory not found")
        
        result = {
            "available": True,
            "version": getattr(gpt4all, "__version__", "unknown"),
            "models_dir_exists": os.path.exists(models_dir),
            "models_found": models_found
        }
    except ImportError:
        logger.warning("GPT4All not installed")
        result = {
            "available": False
        }
    
    return result

def check_autogpt():
    """Check AutoGPT availability"""
    logger.info("Checking AutoGPT...")
    
    try:
        import autogpt
        logger.info(f"AutoGPT package found: {getattr(autogpt, '__version__', 'unknown')}")
        
        result = {
            "available": True,
            "version": getattr(autogpt, "__version__", "unknown")
        }
    except ImportError:
        # Check for AutoGPT repositories
        autogpt_repos = []
        base_dirs = [
            os.path.join(os.path.expanduser("~"), "Desktop"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "frameworks")
        ]
        
        for base_dir in base_dirs:
            if os.path.exists(base_dir):
                for item in os.listdir(base_dir):
                    item_path = os.path.join(base_dir, item)
                    if os.path.isdir(item_path) and ("autogpt" in item.lower() or "auto-gpt" in item.lower()):
                        autogpt_repos.append(item_path)
        
        if autogpt_repos:
            logger.info(f"Found {len(autogpt_repos)} AutoGPT repositories:")
            for repo in autogpt_repos:
                logger.info(f"  - {repo}")
            
            result = {
                "available": False,
                "package_installed": False,
                "repositories_found": autogpt_repos
            }
        else:
            logger.warning("AutoGPT not found (neither as package nor repository)")
            result = {
                "available": False,
                "package_installed": False,
                "repositories_found": []
            }
    
    return result

def check_frameworks_manager():
    """Check the FrameworkManager and available frameworks"""
    logger.info("Checking Framework Manager and registered frameworks...")
    
    try:
        # Add the project root to the Python path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.append(project_root)
        
        from integrations.framework_manager import FrameworkManager
        
        # Initialize the framework manager
        manager = FrameworkManager()
        
        # Get loaded frameworks
        loaded_frameworks = manager.loaded_frameworks
        framework_capabilities = manager.framework_capabilities
        
        if loaded_frameworks:
            logger.info(f"Found {len(loaded_frameworks)} loaded frameworks:")
            for name, framework in loaded_frameworks.items():
                capabilities = framework_capabilities.get(name, [])
                logger.info(f"  - {name}: {', '.join(capabilities) if capabilities else 'No capabilities'}")
        else:
            logger.info("No frameworks loaded")
        
        result = {
            "available": True,
            "loaded_frameworks": {name: framework_capabilities.get(name, []) for name in loaded_frameworks}
        }
    except Exception as e:
        logger.error(f"Error checking framework manager: {str(e)}")
        result = {
            "available": False,
            "error": str(e)
        }
    
    return result

def check_integrations_config():
    """Check the integrations.json configuration file"""
    logger.info("Checking integrations configuration...")
    
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "config/integrations.json"
    )
    
    if not os.path.exists(config_path):
        logger.warning(f"Integrations configuration not found: {config_path}")
        return {
            "available": False
        }
    
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        
        enabled_integrations = []
        for integration_type, settings in config.get("integrations", {}).items():
            if settings.get("enabled", False):
                paths = settings.get("paths", [])
                existing_paths = [p for p in paths if os.path.exists(p)]
                enabled_integrations.append({
                    "type": integration_type,
                    "paths": existing_paths,
                    "total_paths": len(paths),
                    "existing_paths": len(existing_paths)
                })
        
        if enabled_integrations:
            logger.info(f"Found {len(enabled_integrations)} enabled integrations:")
            for integration in enabled_integrations:
                logger.info(f"  - {integration['type']}: {integration['existing_paths']}/{integration['total_paths']} paths exist")
        else:
            logger.info("No enabled integrations found in configuration")
        
        result = {
            "available": True,
            "enabled_integrations": enabled_integrations
        }
    except Exception as e:
        logger.error(f"Error reading integrations configuration: {str(e)}")
        result = {
            "available": False,
            "error": str(e)
        }
    
    return result

def generate_report(results):
    """Generate a formatted diagnostic report"""
    report = [
        "========================================================",
        "               MINERVA AI DIAGNOSTIC REPORT              ",
        "========================================================",
        "",
        f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Python: {sys.version.split()[0]}",
        f"OS: {sys.platform}",
        ""
    ]
    
    # Environment report
    report.append("1. ENVIRONMENT CHECK")
    report.append("--------------------")
    deps = results["dependencies"]
    core_deps = ["flask", "flask_socketio", "torch", "transformers"]
    for dep in core_deps:
        status = deps.get(dep, {})
        if status.get("available"):
            report.append(f"✅ {dep}: {status.get('version', 'unknown')}")
        else:
            report.append(f"❌ {dep}: Not installed")
    report.append("")
    
    # HuggingFace report
    report.append("2. HUGGINGFACE CHECK")
    report.append("--------------------")
    hf = results["huggingface"]
    if hf.get("available"):
        report.append(f"✅ Transformers: {hf.get('version', 'unknown')}")
        report.append(f"✅ Cache directory: {'Exists' if hf.get('cache_exists') else 'Not found'}")
        report.append(f"✅ Cached files: {hf.get('cached_files', 0)}")
    else:
        report.append("❌ HuggingFace Transformers: Not installed")
    report.append("")
    
    # GPT4All report
    report.append("3. GPT4ALL CHECK")
    report.append("----------------")
    g4a = results["gpt4all"]
    if g4a.get("available"):
        report.append(f"✅ GPT4All: {g4a.get('version', 'unknown')}")
        report.append(f"✅ Models directory: {'Exists' if g4a.get('models_dir_exists') else 'Not found'}")
        models = g4a.get("models_found", [])
        if models:
            report.append(f"✅ Models found: {len(models)}")
            for model in models[:3]:  # Show only first 3
                report.append(f"  - {model}")
            if len(models) > 3:
                report.append(f"  - ... and {len(models) - 3} more")
        else:
            report.append("❌ No GPT4All models found")
    else:
        report.append("❌ GPT4All: Not installed")
    report.append("")
    
    # AutoGPT report
    report.append("4. AUTOGPT CHECK")
    report.append("----------------")
    ag = results["autogpt"]
    if ag.get("available"):
        report.append(f"✅ AutoGPT: {ag.get('version', 'unknown')}")
    else:
        repos = ag.get("repositories_found", [])
        if repos:
            report.append(f"⚠️ AutoGPT: Not installed as package, but {len(repos)} repositories found")
            for repo in repos[:3]:  # Show only first 3
                report.append(f"  - {os.path.basename(repo)}")
            if len(repos) > 3:
                report.append(f"  - ... and {len(repos) - 3} more")
        else:
            report.append("❌ AutoGPT: Not found")
    report.append("")
    
    # Frameworks report
    report.append("5. FRAMEWORKS CHECK")
    report.append("-------------------")
    fm = results["frameworks_manager"]
    if fm.get("available"):
        frameworks = fm.get("loaded_frameworks", {})
        if frameworks:
            report.append(f"✅ Loaded frameworks: {len(frameworks)}")
            for name, capabilities in frameworks.items():
                report.append(f"  - {name}: {', '.join(capabilities) if capabilities else 'No capabilities'}")
        else:
            report.append("⚠️ No frameworks loaded")
    else:
        report.append(f"❌ Framework Manager error: {fm.get('error', 'Unknown error')}")
    report.append("")
    
    # Integrations config report
    report.append("6. INTEGRATIONS CONFIG CHECK")
    report.append("----------------------------")
    ic = results["integrations_config"]
    if ic.get("available"):
        integrations = ic.get("enabled_integrations", [])
        if integrations:
            report.append(f"✅ Enabled integrations: {len(integrations)}")
            for integration in integrations:
                report.append(f"  - {integration['type']}: {integration['existing_paths']}/{integration['total_paths']} paths exist")
        else:
            report.append("⚠️ No enabled integrations found in configuration")
    else:
        report.append(f"❌ Integrations config error: {ic.get('error', 'File not found')}")
    report.append("")
    
    # Summary
    report.append("7. SUMMARY")
    report.append("---------")
    
    # Count available models
    available_models = 0
    if hf.get("available"):
        available_models += 1
    if g4a.get("available") and g4a.get("models_found"):
        available_models += 1
    if ag.get("available") or ag.get("repositories_found"):
        available_models += 1
    
    if available_models >= 2:
        report.append("✅ GOOD: Multiple AI models available for multi-model integration")
    elif available_models == 1:
        report.append("⚠️ LIMITED: Only one AI model available, limited multi-model capabilities")
    else:
        report.append("❌ POOR: No AI models available, system will use fallback templates only")
    
    # Overall system status
    if "transformers" in deps and deps["transformers"].get("available"):
        report.append("✅ Minerva core functionality available (HuggingFace)")
    else:
        report.append("❌ Minerva core functionality compromised (HuggingFace not available)")
    
    report.append("")
    report.append("========================================================")
    
    return "\n".join(report)

def main():
    """Run the diagnostics and display results"""
    print("Starting Minerva AI Diagnostics...")
    
    results = {
        "dependencies": check_environment(),
        "huggingface": check_huggingface_models(),
        "gpt4all": check_gpt4all(),
        "autogpt": check_autogpt(),
        "frameworks_manager": check_frameworks_manager(),
        "integrations_config": check_integrations_config()
    }
    
    # Generate report
    report = generate_report(results)
    
    # Save report to file
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "minerva_diagnostic_report.txt")
    with open(report_path, "w") as f:
        f.write(report)
    
    print("\n" + report)
    print(f"\nDiagnostic report saved to: {report_path}")

if __name__ == "__main__":
    main()
