---
name: cuda-nsight-optimizer
description: GPU CUDA kernel profiling, Nsight analysis & performance...
platforms:
- linux
- macos
- windows
---

# CUDA & Nsight Compute Optimization Playbook

When profiling or optimizing GPU-accelerated code and CUDA kernels:

## 1. Inspect GPU Topology & Architecture
Run `terminal` to verify compute capability, SM count, and VRAM:
```bash
nvidia-smi --query-gpu=name,compute_cap,memory.total,memory.free --format=csv
```

## 2. Compile with Diagnostic Symbols
Ensure kernel is built with line numbers for Nsight attribution:
```bash
nvcc -O3 -lineinfo -Xcompiler -Wall -arch=native kernel.cu -o kernel_bench
```

## 3. Profile Memory Bandwidth & Warp Stalls
Run NVIDIA Nsight Compute CLI (`ncu`) to gather hardware performance counters:
```bash
ncu --set full --section SpeedOfLight --section MemoryWorkloadAnalysis ./kernel_bench
```

## 4. Remediation Checklist
- **Shared Memory Bank Conflicts**: Pad multi-dimensional shared memory arrays to 33 elements to eliminate 32-way bank conflicts.
- **Coalesced Global Memory Access**: Ensure consecutive threads access consecutive 32-byte / 128-byte aligned memory segments.
- **Occupancy Tuning**: Adjust thread block dimensions (`blockDim.x`) to maximize warp occupancy per Streaming Multiprocessor (SM).
- **Tensor Core Acceleration**: Use `wmma` (Warp Matrix Multiply and Accumulate) or `mma.sync` instructions on Ampere/Hopper/Blackwell architectures.
