# AMD Ryzen AI MAX+ 395 - Installation Notes & Technical References

**Date Created**: 2026-01-12
**Purpose**: Technical details, commands, references, and troubleshooting info
**System**: AMD Ryzen AI MAX+ 395 w/ Radeon 8060S (gfx1151)

---

## Table of Contents
1. [Quick Reference](#1-quick-reference)
2. [ROCm 7.9 Details](#2-rocm-79-details)
3. [Kernel Parameters](#3-kernel-parameters)
4. [gfx1151 Specific Notes](#4-gfx1151-specific-notes)
5. [PyTorch ROCm Compatibility](#5-pytorch-rocm-compatibility)
6. [Troubleshooting Guide](#6-troubleshooting-guide)
7. [Useful Commands](#7-useful-commands)
8. [Documentation Links](#8-documentation-links)
9. [Community Resources](#9-community-resources)

---

## 1. Quick Reference

### System Specifications
```
CPU: AMD Ryzen AI MAX+ 395
  - Architecture: Zen 5 (Family 26, Model 112)
  - Cores/Threads: 16C/32T
  - Base/Boost: 3.0 GHz / 5.1 GHz

GPU: AMD Radeon 8060S
  - Architecture: RDNA 3.5 (gfx1151)
  - Compute Units: 40 CUs
  - Max Clock: 2.9 GHz
  - PCI ID: 1002:1586
  - PCI Address: c6:00.0

NPU: AMD XDNA 2
  - AI Performance: 50+ INT8 TOPS
  - PCI ID: 1022:17f0
  - PCI Address: c7:00.1

Memory: 128GB LPDDR5X (unified across CPU/GPU/NPU)
```

### Target Software Versions
```
OS: Ubuntu 24.10 (Oracular Oriole)
Kernel: 6.11.x or 6.14.x
ROCm: 7.9.0 preview (gfx1151 specific)
PyTorch: Latest with ROCm 6.3 wheel
sglang: Docker image or latest pip
LLaMA-Factory: Latest from GitHub
```

---

## 2. ROCm 7.9 Details

### Official Links
- **Documentation**: https://rocm.docs.amd.com/en/7.9.0-preview/
- **Release Notes**: https://rocm.docs.amd.com/en/7.9.0-preview/about/release-notes.html
- **Installation**: https://rocm.docs.amd.com/en/7.9.0-preview/install/rocm.html

### Download Information

**Tarball for gfx1151**:
```bash
URL: https://repo.amd.com/rocm/tarball/therock-dist-linux-gfx1151-7.9.0rc1.tar.gz
Architecture: x86_64
Platform: gfx1151 (Strix Halo - Ryzen AI Max+ series)
Format: tar.gz
Size: ~several GB (exact size TBD after download)
```

### Installation Commands

```bash
# Download tarball
cd /home/quings/lpl/install_driver/
wget https://repo.amd.com/rocm/tarball/therock-dist-linux-gfx1151-7.9.0rc1.tar.gz

# Create installation directory
sudo mkdir -p /opt/rocm

# Extract (--strip-components=1 removes top-level directory)
sudo tar -xf therock-dist-linux-gfx1151-7.9.0rc1.tar.gz -C /opt/rocm --strip-components=1

# Verify extraction
ls -la /opt/rocm/
# Should see: bin/ include/ lib/ lib64/ share/ etc.

# Set permissions (if needed)
sudo chown -R root:root /opt/rocm
sudo chmod -R 755 /opt/rocm
```

### Environment Variables

Add to `~/.bashrc`:
```bash
# ROCm Environment Variables
export ROCM_HOME=/opt/rocm
export PATH=$ROCM_HOME/bin:$PATH
export LD_LIBRARY_PATH=$ROCM_HOME/lib:$ROCM_HOME/lib64:$LD_LIBRARY_PATH

# GFX1151 Override (may be needed for compatibility)
export HSA_OVERRIDE_GFX_VERSION=11.5.1

# Optional: Enable ROCm debugging
# export HSA_ENABLE_DEBUG=1
# export AMD_LOG_LEVEL=3
```

Apply changes:
```bash
source ~/.bashrc
# Or: logout and login again
```

### Verification Commands

```bash
# Check ROCm path
echo $ROCM_HOME
# Expected: /opt/rocm

# Check rocminfo
rocminfo
# Expected: Should show CPU and GPU agents

# Check rocm-smi
/opt/rocm/bin/rocm-smi
# Expected: GPU information

# Check amd-smi (if included)
amd-smi static
# Expected: CPU and GPU information

# Check HIP runtime
/opt/rocm/bin/hipcc --version
# Expected: HIP version info

# List installed ROCm tools
ls /opt/rocm/bin/
```

### Known Issues with ROCm 7.9 Preview

1. **Experimental Status**:
   - Technology preview, not production-ready
   - May have bugs or instability
   - Use at own risk

2. **gfx1151 Support**:
   - Officially supported but limited testing
   - Some libraries may not be fully optimized (e.g., hipBLASLt)
   - FlashAttention may have issues

3. **Package Format**:
   - No deb/rpm packages, tarball only
   - Manual environment setup required
   - No automatic updates

### Fallback: ROCm 7.0

If ROCm 7.9 is too unstable:

```bash
# Community reports ROCm 7.0 works with gfx1151
# May need HSA override:
export HSA_OVERRIDE_GFX_VERSION=11.5.1

# Check AMD ROCm GitHub releases for 7.0 packages
# https://github.com/ROCm/ROCm/releases
```

---

## 3. Kernel Parameters

### Recommended GRUB Parameters

Edit `/etc/default/grub`:

```bash
# Open with editor
sudo nano /etc/default/grub

# Find line:
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"

# Change to:
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash amdgpu.dpm=1 amdgpu.ppfeaturemask=0xffffffff"
```

**Parameter Explanations**:
- `amdgpu.dpm=1`: Enable Dynamic Power Management for GPU
- `amdgpu.ppfeaturemask=0xffffffff`: Enable all PowerPlay features

### Alternative/Additional Parameters

If issues occur, try these:

```bash
# If GPU still not detected:
amdgpu.dc=1          # Enable Display Core (newer display engine)

# If simple-framebuffer conflict:
modprobe.blacklist=simplefb

# If boot hangs:
nomodeset            # Disable kernel mode setting (use only for debugging)

# For better power management:
amdgpu.gpu_recovery=1
amdgpu.lockup_timeout=10000
```

### Update GRUB

```bash
# Update GRUB configuration
sudo update-grub

# Verify changes
cat /etc/default/grub | grep GRUB_CMDLINE_LINUX_DEFAULT

# Reboot
sudo reboot
```

### Verify Parameters Active

After reboot:
```bash
cat /proc/cmdline
# Should see your amdgpu parameters
```

---

## 4. gfx1151 Specific Notes

### Architecture Information

- **Marketing Name**: Radeon 8060S
- **Codename**: Strix Halo iGPU
- **GFX Version**: gfx1151 (11.5.1)
- **Architecture**: RDNA 3.5
- **Launch**: February 2025 (very new!)

### Compute Specifications

```
Compute Units: 40 CUs
Stream Processors: 2560 (40 CUs × 64 SPs/CU)
Clock Speed: Up to 2900 MHz
FP32 Performance: ~14.8 TFLOPS (theoretical)
Memory: Shared LPDDR5X (128GB unified)
Memory Bandwidth: ~273 GB/s
```

### HSA Override

Some software may not recognize gfx1151 yet:

```bash
export HSA_OVERRIDE_GFX_VERSION=11.5.1
```

This tells ROCm to treat it as gfx1151 (or sometimes 11.0.0 for wider compatibility).

### Compatibility Notes

**What Works**:
- ROCm 7.9 preview (official support)
- ROCm 7.0 (community tested)
- PyTorch with ROCm 6.3+ wheels
- sglang (Docker image rocm630)
- LLaMA-Factory (tested with ROCm 6.3)
- Llama.cpp with ROCm backend

**Known Issues**:
- hipBLASLt may fall back to hipBLAS (slower)
- FlashAttention may need specific builds
- Some older ROCm versions don't recognize gfx1151
- Limited optimization compared to MI300/Instinct GPUs

### Performance Expectations

As an APU (integrated graphics), performance is:
- **Not comparable** to discrete GPUs like RX 7900 XTX or MI300
- **Suitable for**:
  - Small to medium LLM inference (7B-13B models)
  - LoRA fine-tuning
  - Development and testing
  - Edge AI applications
- **Advantages**:
  - Unified 128GB memory (can load large models)
  - Low power consumption
  - No PCIe bandwidth bottleneck

---

## 5. PyTorch ROCm Compatibility

### Installation

**Recommended** (ROCm 6.3 wheels):
```bash
# Create virtual environment
python3 -m venv ~/pytorch-rocm-env
source ~/pytorch-rocm-env/bin/activate

# Install PyTorch with ROCm support
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.3
```

**Alternative** (ROCm 6.2):
```bash
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.2
```

### Version Compatibility Matrix

| PyTorch | ROCm Backend | gfx1151 Support | Status |
|---------|-------------|-----------------|--------|
| 2.5+    | ROCm 6.3    | ✅ Yes (with override) | Recommended |
| 2.4+    | ROCm 6.2    | ⚠️ Maybe | Fallback |
| 2.3+    | ROCm 6.1    | ❌ Unlikely | Not recommended |
| < 2.3   | ROCm 5.x    | ❌ No | Too old |

### Verification Script

Save as `test_pytorch_rocm.py`:
```python
#!/usr/bin/env python3
import torch
import sys

print(f"PyTorch version: {torch.__version__}")
print(f"ROCm compiled: {torch.version.hip if hasattr(torch.version, 'hip') else 'N/A'}")
print(f"CUDA available: {torch.cuda.is_available()}")

if not torch.cuda.is_available():
    print("❌ ERROR: CUDA/ROCm not available!")
    print("Possible causes:")
    print("  1. ROCm not installed properly")
    print("  2. GPU not detected by ROCm (check rocminfo)")
    print("  3. LD_LIBRARY_PATH not set correctly")
    print("  4. HSA_OVERRIDE_GFX_VERSION not set (try: export HSA_OVERRIDE_GFX_VERSION=11.5.1)")
    sys.exit(1)

print(f"GPU count: {torch.cuda.device_count()}")
print(f"Current device: {torch.cuda.current_device()}")
print(f"GPU name: {torch.cuda.get_device_name(0)}")

props = torch.cuda.get_device_properties(0)
print(f"GPU memory: {props.total_memory / 1e9:.2f} GB")
print(f"Compute capability: {props.major}.{props.minor}")

# Test tensor operations
print("\n🧪 Testing tensor operations...")
try:
    x = torch.rand(1000, 1000, device='cuda')
    y = torch.rand(1000, 1000, device='cuda')
    z = torch.matmul(x, y)
    print("✅ Matrix multiplication successful!")

    # Test more operations
    _ = torch.nn.functional.relu(z)
    print("✅ ReLU activation successful!")

    _ = torch.sum(z)
    print("✅ Reduction operation successful!")

    print("\n🎉 All tests passed! PyTorch with ROCm is working!")
except Exception as e:
    print(f"❌ Error during tensor operations: {e}")
    sys.exit(1)
```

Run with:
```bash
python3 test_pytorch_rocm.py
```

### Common PyTorch Issues

**Issue 1: CUDA not available**
```bash
# Check ROCm detection
rocminfo | grep -i gpu

# Check environment
echo $LD_LIBRARY_PATH
# Should include /opt/rocm/lib

# Set HSA override
export HSA_OVERRIDE_GFX_VERSION=11.5.1
```

**Issue 2: Import errors**
```bash
# Missing dependencies
pip install numpy pillow

# Check PyTorch installation
python3 -c "import torch; print(torch.__file__)"
```

**Issue 3: Performance slow**
```bash
# Enable TF32 for faster compute
export TORCH_ALLOW_TF32=1

# Set optimal memory allocation
export PYTORCH_HIP_ALLOC_CONF=garbage_collection_threshold:0.7
```

---

## 6. Troubleshooting Guide

### GPU Not Detected

**Symptoms**:
- `rocminfo` only shows CPU
- `amd-smi static` shows nothing
- PyTorch `torch.cuda.is_available()` returns `False`

**Solutions**:

1. **Check if GPU visible to system**:
   ```bash
   lspci | grep -i display
   # Should show: c6:00.0 Display controller: Advanced Micro Devices...
   ```

2. **Check driver binding**:
   ```bash
   lspci -k | grep -A 3 "c6:00.0"
   # Should show: "Kernel driver in use: amdgpu"
   # If shows "simple-framebuffer", driver not bound!
   ```

3. **Force amdgpu binding**:
   ```bash
   # Check if module loaded
   lsmod | grep amdgpu

   # If not loaded:
   sudo modprobe amdgpu

   # Reboot
   sudo reboot
   ```

4. **Blacklist simple-framebuffer**:
   ```bash
   sudo nano /etc/modprobe.d/blacklist-framebuffer.conf
   # Add:
   blacklist simplefb

   # Update initramfs
   sudo update-initramfs -u

   # Reboot
   sudo reboot
   ```

5. **Check kernel messages**:
   ```bash
   sudo dmesg | grep -i amdgpu | tail -50
   # Look for errors or initialization messages
   ```

### NPU Not Working

**Symptoms**:
- NPU device disabled in lspci
- No `/dev/accel/` directory
- amdxdna module not found

**Solutions**:

1. **Check kernel version**:
   ```bash
   uname -r
   # Must be >= 6.11 for amdxdna support
   # Preferably >= 6.14 (driver mainlined)
   ```

2. **Check if driver available**:
   ```bash
   modinfo amdxdna
   # If "not found", kernel too old or driver not built
   ```

3. **Install from source** (if not in kernel):
   ```bash
   git clone https://github.com/amd/xdna-driver.git
   cd xdna-driver
   # Follow installation instructions in README
   ```

4. **Load module**:
   ```bash
   sudo modprobe amdxdna
   lsmod | grep amdxdna
   ```

**Note**: NPU is optional for our goals (AI workloads use GPU primarily)

### amd-smi Shows Nothing

**Likely Causes**:
1. GPU not detected by ROCm → Fix GPU detection first
2. Old amd-smi version → Install from ROCm 7.9
3. Library path issues → Check LD_LIBRARY_PATH

**Solutions**:
```bash
# Check if amd-smi is from ROCm
which amd-smi
# Should be /opt/rocm/bin/amd-smi

# If not, add to PATH
export PATH=/opt/rocm/bin:$PATH

# Check library path
export LD_LIBRARY_PATH=/opt/rocm/lib:/opt/rocm/lib64:$LD_LIBRARY_PATH

# Try again
amd-smi static
```

### PyTorch Can't See GPU

**Symptoms**:
- `torch.cuda.is_available()` returns `False`
- "HIP not available" errors

**Solutions**:

1. **Verify ROCm working**:
   ```bash
   rocminfo | grep -i "agent"
   # Must show GPU agent
   ```

2. **Check PyTorch ROCm version**:
   ```python
   import torch
   print(torch.version.hip)
   # Should show HIP version (e.g., 6.3.x)
   ```

3. **Set environment**:
   ```bash
   export HSA_OVERRIDE_GFX_VERSION=11.5.1
   export ROCM_HOME=/opt/rocm
   export LD_LIBRARY_PATH=/opt/rocm/lib:$LD_LIBRARY_PATH
   ```

4. **Reinstall PyTorch**:
   ```bash
   pip uninstall torch torchvision torchaudio
   pip cache purge
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.3
   ```

### sglang Errors

**Common Issues**:

1. **Model download fails**:
   ```bash
   # Set HuggingFace cache
   export HF_HOME=/home/quings/.cache/huggingface
   mkdir -p $HF_HOME

   # Login if needed (for gated models)
   huggingface-cli login
   ```

2. **Out of memory**:
   ```bash
   # Use smaller model
   # Try Llama-3.2-1B instead of larger models

   # Or enable offloading
   # Check sglang docs for offload options
   ```

3. **Docker GPU access**:
   ```bash
   # Ensure correct device passthrough
   docker run ... --device=/dev/kfd --device=/dev/dri --group-add video ...
   ```

### Boot Issues After GRUB Changes

**If system won't boot**:

1. **At GRUB menu**:
   - Press 'e' to edit boot entry
   - Remove problematic parameters
   - Press Ctrl+X to boot

2. **Boot with old kernel**:
   - Select "Advanced options for Ubuntu"
   - Choose previous kernel version
   - Boot normally

3. **Revert GRUB changes**:
   ```bash
   sudo nano /etc/default/grub
   # Remove problematic parameters
   sudo update-grub
   sudo reboot
   ```

---

## 7. Useful Commands

### Hardware Detection
```bash
# List all AMD PCI devices
lspci | grep -i amd

# Detailed GPU info
lspci -vnn | grep -A 20 "Display"

# Check GPU driver
lspci -k | grep -A 3 "Display"

# List DRM devices
ls -la /dev/dri/

# Check GPU uevent
cat /sys/class/drm/card0/device/uevent
```

### Kernel & Modules
```bash
# Current kernel
uname -r

# Loaded AMD modules
lsmod | grep -iE "amdgpu|kfd|drm"

# Module info
modinfo amdgpu

# Kernel messages (amdgpu)
sudo dmesg | grep -i amdgpu | tail -50

# Boot parameters
cat /proc/cmdline
```

### ROCm Utilities
```bash
# ROCm info (detailed)
rocminfo

# GPU monitoring
/opt/rocm/bin/rocm-smi

# AMD SMI static info
amd-smi static

# AMD SMI live metrics
amd-smi metric --watch

# GPU topology
amd-smi topology

# HIP info
hipconfig
```

### Performance Monitoring
```bash
# GPU utilization (ROCm)
watch -n 1 'rocm-smi | grep -E "(GPU|Temperature|Memory)"'

# GPU utilization (AMD SMI)
watch -n 1 'amd-smi metric'

# CPU info
lscpu
htop

# Memory info
free -h
vmstat 1

# Disk I/O
iostat -x 1
```

### Package Management
```bash
# List ROCm packages
dpkg -l | grep rocm

# List AMD packages
dpkg -l | grep amd

# Save package list
dpkg --get-selections > packages-$(date +%Y%m%d).list

# Check package version
dpkg -l | grep package-name
```

---

## 8. Documentation Links

### AMD Official

**ROCm**:
- ROCm 7.9 Preview: https://rocm.docs.amd.com/en/7.9.0-preview/
- ROCm Installation: https://rocm.docs.amd.com/projects/install-on-linux/en/latest/
- AMD SMI: https://rocm.docs.amd.com/projects/amdsmi/en/latest/

**Ryzen AI**:
- Ryzen AI Software: https://ryzenai.docs.amd.com/
- NPU Driver (XDNA): https://github.com/amd/xdna-driver
- Linux Setup: https://ryzenai.docs.amd.com/en/latest/linux.html

**Product Info**:
- Ryzen AI Max+ 395: https://www.amd.com/en/products/processors/laptop/ryzen/ai-300-series/amd-ryzen-ai-max-plus-395.html

### AI Frameworks

**sglang**:
- AMD Blog: https://rocm.blogs.amd.com/artificial-intelligence/sglang/README.html
- GitHub: https://github.com/sgl-project/sglang
- Docker Hub: https://hub.docker.com/r/lmsysorg/sglang

**LLaMA-Factory**:
- AMD Tutorial: https://rocm.docs.amd.com/projects/ai-developer-hub/en/latest/notebooks/fine_tune/llama_factory_llama3.html
- GitHub: https://github.com/hiyouga/LLaMA-Factory

**PyTorch**:
- ROCm Installation: https://pytorch.org/get-started/locally/
- ROCm Wheels: https://download.pytorch.org/whl/rocm6.3/

---

## 9. Community Resources

### Forums & Discussions
- **ROCm GitHub Issues**: https://github.com/ROCm/ROCm/issues
  - Search for "gfx1151" or "Strix Halo"
- **TheRock Discussions**: https://github.com/ROCm/TheRock/discussions
  - ROCm 7.9 specific discussions
- **AMD Community**: https://community.amd.com/
- **Reddit r/ROCm**: https://reddit.com/r/ROCm

### Community Guides
- **Framework Strix Halo Setup**: https://github.com/Gygeek/Framework-strix-halo-llm-setup
  - Complete guide for Strix Halo ROCm installation
  - Includes BIOS configs, kernel setup, known issues

### News & Benchmarks
- **Phoronix - Strix Halo ROCm Testing**: https://www.phoronix.com/review/amd-rocm-7-strix-halo
- **Phoronix Forums**: https://www.phoronix.com/forums/
- **TweakTown - Strix Halo Coverage**: https://www.tweaktown.com/
- **VideoCardz**: https://videocardz.com/

### Useful GitHub Issues (Examples)
- gfx1151 PyTorch Wheels: https://github.com/ROCm/TheRock/discussions/655
- Strix Halo Clock Issues: https://github.com/ROCm/ROCm/issues/5750
- hipBLASLt gfx1151: https://github.com/ROCm/ROCm/issues/5643

---

## 10. Notes Section

### (To be filled during installation)

**Date**: YYYY-MM-DD
**Event**: (What happened)
**Details**: (Technical details, commands used, results)
**Resolution**: (How it was resolved, if applicable)

---

**Document Status**: ✅ COMPLETE (Initial version)
**Last Updated**: 2026-01-12
**Next Update**: During and after installation with actual commands and results
