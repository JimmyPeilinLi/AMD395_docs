#!/usr/bin/env python3
import torch
import sys

print("=" * 60)
print("PyTorch ROCm GPU Detection Test")
print("=" * 60)

print(f"\nPyTorch version: {torch.__version__}")

# Check for HIP (ROCm's CUDA equivalent)
if hasattr(torch.version, 'hip'):
    print(f"ROCm compiled: {torch.version.hip}")
else:
    print("ROCm compiled: Not available")

print(f"\nCUDA/ROCm available: {torch.cuda.is_available()}")

if not torch.cuda.is_available():
    print("\n❌ ERROR: CUDA/ROCm not available!")
    print("\nPossible causes:")
    print("  1. ROCm not installed properly")
    print("  2. GPU not detected by ROCm (check rocminfo)")
    print("  3. LD_LIBRARY_PATH not set correctly")
    print("  4. HSA_OVERRIDE_GFX_VERSION not set")
    sys.exit(1)

print(f"GPU count: {torch.cuda.device_count()}")
print(f"Current device: {torch.cuda.current_device()}")
print(f"GPU name: {torch.cuda.get_device_name(0)}")

props = torch.cuda.get_device_properties(0)
print(f"\nGPU Properties:")
print(f"  Total memory: {props.total_memory / 1e9:.2f} GB")
print(f"  Compute capability: {props.major}.{props.minor}")
print(f"  Multi-processor count: {props.multi_processor_count}")

# Test tensor operations
print("\n" + "=" * 60)
print("Testing GPU Tensor Operations")
print("=" * 60)

try:
    print("\n1. Creating random tensors on GPU...")
    x = torch.rand(1000, 1000, device='cuda')
    y = torch.rand(1000, 1000, device='cuda')
    print("   ✅ Tensor creation successful!")

    print("\n2. Testing matrix multiplication...")
    z = torch.matmul(x, y)
    print("   ✅ Matrix multiplication successful!")

    print("\n3. Testing ReLU activation...")
    result = torch.nn.functional.relu(z)
    print("   ✅ ReLU activation successful!")

    print("\n4. Testing reduction operation...")
    sum_result = torch.sum(result)
    print(f"   ✅ Sum result: {sum_result.item():.2f}")

    print("\n" + "=" * 60)
    print("🎉 All tests passed! PyTorch with ROCm is working!")
    print("=" * 60)

except Exception as e:
    print(f"\n❌ Error during tensor operations: {e}")
    sys.exit(1)
