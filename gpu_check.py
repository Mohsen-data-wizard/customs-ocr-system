#!/usr/bin/env python3
# Quick GPU test and fix
import torch
import sys

print("🔍 GPU Status Check:")
print(f"PyTorch Version: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"CUDA Version: {torch.version.cuda}")
    print(f"GPU Count: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
        print(f"GPU {i} Memory: {torch.cuda.get_device_properties(i).total_memory // 1024**3} GB")
else:
    print("❌ CUDA not available! Installing CUDA-enabled PyTorch...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "torch", "torchvision", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cu118"])
    print("✅ CUDA PyTorch installed. Please restart!")
