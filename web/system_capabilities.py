"""
System Capabilities Module for Minerva

This module provides functions to detect system capabilities and available resources
for optimal AI model loading and performance tuning.
"""

import os
import sys
import logging
import platform
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

class SystemCapabilities:
    """Class to detect and report system capabilities for Minerva"""
    
    def __init__(self):
        """Initialize the system capabilities detector"""
        self.os_type = platform.system()
        self.os_version = platform.version()
        self.python_version = platform.python_version()
        self.cpu_count = os.cpu_count() or 1
        
        # Will be populated by detection methods
        self.has_cuda = False
        self.has_mps = False  # Apple Metal Performance Shaders
        self.gpu_info = {}
        self.total_memory_gb = 0
        self.available_memory_gb = 0
        self.recommended_model = "distilgpt2"  # Default conservative model
        self.can_use_quantization = False
        self.optimal_device = "cpu"
        
        # Perform detection
        self._detect_capabilities()
        
    def _detect_capabilities(self):
        """Detect system capabilities and resources"""
        self._detect_memory()
        self._detect_gpu()
        self._determine_optimal_settings()
        
    def _detect_memory(self):
        """Detect available system memory"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            self.total_memory_gb = memory.total / (1024**3)
            self.available_memory_gb = memory.available / (1024**3)
            logger.info(f"[SYSTEM] Detected {self.total_memory_gb:.2f}GB total memory, "
                       f"{self.available_memory_gb:.2f}GB available")
        except ImportError:
            logger.warning("[SYSTEM] Could not import psutil to detect memory")
            # Make a conservative estimate
            self.total_memory_gb = 4.0
            self.available_memory_gb = 2.0
    
    def _detect_gpu(self):
        """Detect GPU availability and type"""
        # Try to detect CUDA (NVIDIA)
        try:
            import torch
            self.has_cuda = torch.cuda.is_available()
            
            if self.has_cuda:
                self.optimal_device = "cuda"
                cuda_device_count = torch.cuda.device_count()
                self.gpu_info["cuda_count"] = cuda_device_count
                self.gpu_info["cuda_names"] = [torch.cuda.get_device_name(i) for i in range(cuda_device_count)]
                
                logger.info(f"[SYSTEM] CUDA available: {cuda_device_count} device(s)")
                for i, name in enumerate(self.gpu_info["cuda_names"]):
                    logger.info(f"[SYSTEM] CUDA device {i}: {name}")
            
            # Try to detect MPS (Apple Silicon)
            if not self.has_cuda and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self.has_mps = True
                self.optimal_device = "mps"
                self.gpu_info["mps"] = "Apple Silicon"
                logger.info("[SYSTEM] Apple Metal Performance Shaders (MPS) available")
            
        except ImportError:
            logger.warning("[SYSTEM] Could not import torch to detect GPU")
    
    def _determine_optimal_settings(self):
        """Determine the optimal model and settings based on detected capabilities"""
        # Check if bitsandbytes is available for quantization
        try:
            import bitsandbytes
            self.can_use_quantization = True
            logger.info("[SYSTEM] bitsandbytes library available for 8-bit quantization")
        except ImportError:
            self.can_use_quantization = False
            logger.info("[SYSTEM] bitsandbytes library not available, 8-bit quantization disabled")
        
        # Choose model based on available resources
        if self.has_cuda:
            gpu_memory = 0
            try:
                import torch
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                self.gpu_info["cuda_memory_gb"] = gpu_memory
                logger.info(f"[SYSTEM] CUDA memory: {gpu_memory:.2f}GB")
            except:
                pass
            
            if gpu_memory >= 10 or self.available_memory_gb >= 10:
                self.recommended_model = "HuggingFaceH4/zephyr-7b-beta"
                logger.info("[SYSTEM] Sufficient resources for advanced model detected")
            elif gpu_memory >= 4 or self.available_memory_gb >= 6:
                self.recommended_model = "google/flan-t5-base"
                logger.info("[SYSTEM] Moderate resources detected, using medium-sized model")
            else:
                logger.info("[SYSTEM] Limited resources detected, using small model")
        
        elif self.has_mps and self.available_memory_gb >= 6:
            self.recommended_model = "google/flan-t5-base"
            logger.info("[SYSTEM] Apple Silicon with sufficient memory detected")
        
        else:
            # CPU only or limited resources
            if self.available_memory_gb >= 8:
                self.recommended_model = "google/flan-t5-base"
                logger.info("[SYSTEM] CPU-only with sufficient memory, using medium-sized model")
            else:
                logger.info("[SYSTEM] CPU-only with limited memory, using small model")

    def get_recommendations(self):
        """Get recommended settings as a dictionary"""
        return {
            "device": self.optimal_device,
            "model": self.recommended_model,
            "use_8bit": self.can_use_quantization and (self.has_cuda or self.has_mps),
            "use_half_precision": self.has_cuda or self.has_mps,
            "available_memory_gb": self.available_memory_gb,
            "gpu_available": self.has_cuda or self.has_mps
        }
    
    def __str__(self):
        """String representation of system capabilities"""
        gpu_str = "None detected"
        if self.has_cuda:
            gpu_str = f"CUDA: {', '.join(self.gpu_info.get('cuda_names', []))}"
        elif self.has_mps:
            gpu_str = "Apple Silicon (MPS)"
        
        memory_str = f"{self.total_memory_gb:.1f}GB total, {self.available_memory_gb:.1f}GB available"
        
        return (f"System Capabilities:\n"
                f"  OS: {self.os_type} {self.os_version}\n"
                f"  Python: {self.python_version}\n"
                f"  CPU Cores: {self.cpu_count}\n"
                f"  Memory: {memory_str}\n"
                f"  GPU: {gpu_str}\n"
                f"  Optimal Device: {self.optimal_device}\n"
                f"  Recommended Model: {self.recommended_model}\n"
                f"  8-bit Quantization: {'Available' if self.can_use_quantization else 'Not available'}")

def get_capabilities():
    """Get system capabilities instance"""
    return SystemCapabilities()

if __name__ == "__main__":
    # Set up basic logging if run directly
    logging.basicConfig(level=logging.INFO)
    
    # Print capabilities
    capabilities = get_capabilities()
    print(capabilities)
    
    # Print recommendations
    print("\nRecommended Settings:")
    for key, value in capabilities.get_recommendations().items():
        print(f"  {key}: {value}")
