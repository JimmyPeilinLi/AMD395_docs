# AMD Ryzen AI MAX+ 395 - Functional Requirements

**Document Version**: 1.0
**Date Created**: 2026-01-12
**Target System**: AMD Ryzen AI MAX+ 395 w/ Radeon 8060S
**Primary Objective**: Enable AI/ML workloads (sglang, LLaMA-Factory)

---

## 1. Hardware Detection Requirements

### 1.1 CPU Detection
- **Requirement**: System must fully recognize and report all CPU specifications
- **Expected Output**:
  - Model: AMD Ryzen AI MAX+ 395
  - Cores: 16 physical cores
  - Threads: 32 threads
  - Architecture: Zen 5
  - Base Frequency: 3.0 GHz
  - Boost Frequency: Up to 5.1 GHz
  - Cache: 64MB L3 cache

### 1.2 GPU Detection
- **Requirement**: Integrated GPU must be recognized and accessible by ROCm stack
- **Expected Output**:
  - Model: AMD Radeon 8060S
  - Architecture: RDNA 3.5 (gfx1151)
  - Compute Units: 40 CUs
  - Clock Speed: Up to 2.9 GHz
  - Memory: Shared unified memory (LPDDR5X)
  - Driver: amdgpu (not simple-framebuffer)
  - Device nodes: `/dev/dri/card0`, `/dev/dri/renderD128`

### 1.3 NPU Detection
- **Requirement**: Neural Processing Unit must be detected and accessible
- **Expected Output**:
  - Model: XDNA 2 NPU
  - Performance: 50+ INT8 TOPS
  - PCI Device: c7:00.1 (Device ID 1022:17f0)
  - Driver: amdxdna
  - Device node: `/dev/accel/accel0`
- **Note**: NPU is "nice to have" - AI workloads primarily use GPU

---

## 2. System Monitoring Tools Requirements

### 2.1 amd-smi Tool
- **Requirement**: `amd-smi` command must be functional and display complete system information
- **Expected Commands & Output**:

  ```bash
  amd-smi static
  ```
  - Should display: CPU model, GPU model, NPU model (if available)
  - Should display: PCI bus info, device IDs
  - Should display: VRAM size, memory type

  ```bash
  amd-smi metric
  ```
  - Should display: GPU temperature (°C)
  - Should display: GPU utilization (%)
  - Should display: GPU power consumption (W)
  - Should display: GPU clock speeds (MHz)
  - Should display: Memory usage (MB/GB)

### 2.2 rocminfo Tool
- **Requirement**: `rocminfo` must enumerate both CPU and GPU agents
- **Expected Output**:
  - HSA Runtime version
  - Agent 1: CPU (AMD Ryzen AI MAX+ 395)
  - Agent 2: GPU (gfx1151, Radeon 8060S)
  - Memory pools for each agent
  - ISA info for GPU

### 2.3 rocm-smi Tool
- **Requirement**: `/opt/rocm/bin/rocm-smi` must display GPU metrics
- **Expected Output**:
  - GPU ID and model
  - Temperature, fan speed
  - GPU utilization
  - Memory usage
  - SCLK/MCLK frequencies

---

## 3. AI Framework Requirements

### 3.1 PyTorch with ROCm Backend
- **Requirement**: PyTorch must detect GPU and support CUDA operations via ROCm
- **Minimum Version**: PyTorch 2.0+ with ROCm 6.3+ support
- **Expected Functionality**:

  ```python
  import torch
  torch.cuda.is_available()  # Must return True
  torch.cuda.device_count()  # Must return >= 1
  torch.cuda.get_device_name(0)  # Should show GPU name
  ```

  - Must be able to allocate tensors on GPU
  - Must be able to perform matrix operations on GPU
  - Must be able to run basic inference (forward pass)

### 3.2 sglang Serving Framework
- **Requirement**: sglang must successfully serve LLM models
- **Minimum Test**: Serve Llama-3.2-1B model successfully
- **Expected Functionality**:
  - Server starts without errors
  - Model loads to GPU memory
  - Can generate text via API requests
  - Reasonable inference speed (> 10 tokens/sec for small models)
- **Installation Method**: Docker (preferred) or pip install
- **Documentation**: https://rocm.blogs.amd.com/artificial-intelligence/sglang/README.html

### 3.3 LLaMA-Factory Training Framework
- **Requirement**: LLaMA-Factory must launch and support training/fine-tuning
- **Minimum Test**: Launch WebUI and run LoRA fine-tuning on small dataset
- **Expected Functionality**:
  - WebUI launches successfully (`llamafactory-cli webui`)
  - Can load models from HuggingFace
  - Can initiate training jobs
  - Training runs without CUDA/ROCm errors
  - GPU utilization visible during training
- **Documentation**: https://rocm.docs.amd.com/projects/ai-developer-hub/en/latest/notebooks/fine_tune/llama_factory_llama3.html

---

## 4. Performance Metrics Requirements

### 4.1 GPU Metrics
Must be able to monitor in real-time:
- **Temperature**: GPU core temperature
- **Utilization**: GPU compute utilization percentage
- **Memory Usage**: VRAM allocated/used
- **Clock Speeds**: Current SCLK (core) and MCLK (memory) frequencies
- **Power Consumption**: Current power draw in Watts

### 4.2 CPU Metrics
Nice to have (via amd-smi or system tools):
- Per-core frequencies
- Temperature sensors
- Power consumption
- Cache usage

### 4.3 NPU Metrics
Future goal (if amdxdna supports):
- NPU utilization
- NPU power consumption
- AI operations per second

---

## 5. Workload Requirements

### 5.1 Inference Workloads
- **Requirement**: Must run LLM inference workloads efficiently
- **Test Cases**:
  - Load Llama-3.2-1B (1.3B parameters) → Should work smoothly
  - Load Llama-3-8B (8B parameters) → Should work with reasonable performance
  - Load larger models (13B+) → Should at least attempt, may be slow
- **Expected Performance**:
  - Small models (1-3B): > 20 tokens/second
  - Medium models (7-13B): > 5 tokens/second
  - Large models (30B+): Best effort with unified memory

### 5.2 Training/Fine-tuning Workloads
- **Requirement**: Must support LoRA fine-tuning at minimum
- **Test Cases**:
  - LoRA fine-tuning on Llama-3-8B with small dataset
  - Full fine-tuning on smaller models (1-3B)
- **Expected Functionality**:
  - Training starts and progresses
  - GPU memory efficiently utilized
  - No CUDA out-of-memory errors on reasonable configs
  - Training loss decreases (validation that compute works)

### 5.3 Memory Management
- **Requirement**: Utilize unified memory architecture effectively
- **System Memory**: 128GB LPDDR5X shared between CPU/GPU/NPU
- **Expected Behavior**:
  - Large models can load by using system RAM
  - Graceful degradation if VRAM-equivalent exceeds limits
  - No hard crashes from memory allocation

---

## 6. Software Dependencies

### 6.1 Operating System
- **Target**: Ubuntu 24.10 (Oracular Oriole)
- **Kernel**: 6.11+ (for NPU support), preferably 6.14+
- **Driver**: amdgpu-dkms compatible with Strix Halo

### 6.2 ROCm Stack
- **Version**: ROCm 7.9.0 (preview) with gfx1151 support
- **Fallback**: ROCm 7.0 community builds if 7.9 unstable
- **Components Required**:
  - ROCm runtime libraries
  - HSA runtime (libhsa-runtime64)
  - ROCm SMI library
  - AMD SMI library and CLI
  - HIP runtime (for PyTorch)
  - ROCm math libraries (rocBLAS, rocFFT, etc.)

### 6.3 Python Environment
- **Python**: 3.10 or 3.11
- **pip**: Latest version
- **Virtual Environment**: Recommended for AI frameworks

### 6.4 Container Runtime (Optional but Recommended)
- **Docker**: For sglang and other containerized AI workloads
- **Podman**: Alternative to Docker

---

## 7. Success Criteria Summary

### Minimum Viable Product (MVP)
- ✅ GPU detected by amdgpu driver
- ✅ rocminfo shows GPU agent
- ✅ amd-smi displays GPU information and metrics
- ✅ PyTorch detects GPU via ROCm
- ✅ sglang serves Llama-3.2-1B successfully
- ✅ LLaMA-Factory WebUI launches

### Full Success
- ✅ All MVP criteria met
- ✅ NPU detected and has driver bound
- ✅ All amd-smi metrics working (CPU/GPU/NPU)
- ✅ Can fine-tune Llama-3-8B with LoRA
- ✅ GPU temperature, utilization, memory monitoring works
- ✅ Inference performance meets expectations
- ✅ No stability issues during extended workloads

### Stretch Goals
- ✅ NPU functional for AI acceleration
- ✅ Full fine-tuning (not just LoRA) works on 7B models
- ✅ Can run quantized models (GPTQ, AWQ)
- ✅ Multi-GPU support (if system has eGPU)
- ✅ Stable enough for daily use/development

---

## 8. Known Limitations & Acceptance

### Acceptable Limitations
1. **NPU Support**: If NPU doesn't work initially, we accept GPU-only operation
2. **ROCm Stability**: ROCm 7.9 is preview - some instability expected
3. **Performance**: Not expecting data center GPU performance - this is an APU
4. **Software Compatibility**: Some AI tools may not support gfx1151 yet
5. **Model Size**: Very large models (70B+) may be impractical

### Unacceptable Failures
1. ❌ GPU not detected at all by system
2. ❌ ROCm completely non-functional
3. ❌ PyTorch cannot see GPU
4. ❌ System crashes/freezes during normal AI workloads
5. ❌ No GPU metrics available (temperature, utilization)

---

## 9. Documentation Requirements

All steps, attempts, and results must be documented in:
- **This file** (requirements.md): What we want to achieve
- **machine_exploration.md**: What we discovered and tried
- **progress_log.md**: Dated progress entries
- **installation_notes.md**: Technical details and commands used

---

## 10. Verification Checklist

After installation, verify each requirement:

- [ ] CPU: `lscpu` shows all 32 threads
- [ ] GPU: `lspci | grep VGA` shows AMD device
- [ ] GPU Driver: `lspci -k` shows amdgpu driver bound
- [ ] DRM: `ls /dev/dri/` shows card0 and renderD128
- [ ] NPU: `lspci | grep Signal` shows NPU device
- [ ] NPU Driver: `ls /dev/accel/` shows accel0 (if supported)
- [ ] ROCm: `rocminfo` shows both CPU and GPU agents
- [ ] AMD SMI: `amd-smi static` displays hardware info
- [ ] AMD SMI Metrics: `amd-smi metric` displays real-time data
- [ ] ROCm SMI: `/opt/rocm/bin/rocm-smi` shows GPU
- [ ] PyTorch: Python script confirms CUDA available
- [ ] PyTorch GPU: Can allocate tensor on device
- [ ] sglang: Server starts and serves model
- [ ] sglang API: Can generate text via HTTP request
- [ ] LLaMA-Factory: WebUI launches successfully
- [ ] LLaMA-Factory: Can load model and start training
- [ ] GPU Metrics: Can monitor temp/util during inference
- [ ] Stability: No crashes during 1-hour inference test

**Target**: At minimum, first 13 items checked. Ideally all items checked.

---

**Document Status**: ✅ COMPLETE
**Next Steps**: Proceed with system exploration documentation
