---
name: nvidia-ai-blueprints
description: Comprehensive directory and operational runbook for NVIDIA AI Blueprints across Enterprise, Media, Finance, Retail, Healthcare, and Physical AI. Use when building enterprise agents, GPU-accelerated video/rag pipelines, financial models, genomics analysis, or deploying NVIDIA NIM containers.
version: 1.0.0
author: NVIDIA AI & Xennials Architecture
license: Apache-2.0
dependencies: [git, docker, nvidia-container-toolkit, curl]
metadata:
  hermes:
    tags: [NVIDIA, AI Blueprints, NIM, GPU Acceleration, NeMo, Omniverse, Enterprise Agents, RAG, Financial AI, Healthcare AI]
---

# NVIDIA AI Blueprints Reference Catalog & Execution Runbook

NVIDIA AI Blueprints are enterprise-grade reference architectures and production workflows designed to accelerate the development of specialized generative AI and agentic applications on NVIDIA accelerated computing and NVIDIA NIM microservices.

---

## 1. Catalog of Blueprints

### General & Platform Architecture
| Blueprint | GitHub Repository | Focus & Architecture |
| :--- | :--- | :--- |
| **AI-Q** | `https://github.com/NVIDIA-AI-Blueprints/aiq` | Open reference example for building intelligent AI agents connecting to enterprise data. |
| **Video Search & Summarization** | `https://github.com/NVIDIA-AI-Blueprints/video-search-and-summarization` | GPU-accelerated reference architecture for building video analytics and visual QA agents. |
| **Vulnerability Analysis** | `https://github.com/NVIDIA-AI-Blueprints/vulnerability-analysis` | Generative AI application to identify, inspect, and mitigate container security vulnerabilities. |
| **Nemotron Voice Agent** | `https://github.com/NVIDIA-AI-Blueprints/nemotron-voice-agent` | End-to-end multimodal voice agent built using NVIDIA Nemotron NIM, Riva STT/TTS, and low latency streaming. |
| **Nsight Copilot** | `https://github.com/NVIDIA-AI-Blueprints/nsight-copilot` | AI-powered coding assistant and performance tuner for CUDA development and GPU profiling. |
| **Streaming Data to RAG** | `https://github.com/NVIDIA-AI-Blueprints/streaming-data-to-rag` | Blueprint for streaming live event data into Retrieval-Augmented Generation workflows. |
| **RAG** | `https://github.com/NVIDIA-AI-Blueprints/rag` | Foundational enterprise Retrieval-Augmented Generation pipeline using NeMo Retriever NIMs. |
| **NIM Usage Scanner** | `https://github.com/NVIDIA-AI-Blueprints/nim-usage-scanner` | Static code analyzer to discover, audit, and catalog NVIDIA NIM API usage across repos. |
| **LLM Router** | `https://github.com/NVIDIA-AI-Blueprints/llm-router` | Intelligent architecture to route LLM requests dynamically to the optimal model based on complexity and cost. |
| **PDF to Podcast** | `https://github.com/NVIDIA-AI-Blueprints/pdf-to-podcast` | Transforms dense technical PDFs into multi-speaker conversational AI podcasts with natural audio pacing. |
| **AI Virtual Assistant** | `https://github.com/NVIDIA-AI-Blueprints/ai-virtual-assistant` | Customizable, AI-driven virtual assistant designed to streamline customer service workflows. |
| **Bring LLMs to NIM** | `https://github.com/NVIDIA-AI-Blueprints/bring-llms-to-nim` | Guidelines, scripts, and containerization recipes for packaging custom open weights into NIM microservices. |
| **Goose** | `https://github.com/NVIDIA-AI-Blueprints/goose` | Open-source, extensible developer agent for intelligent code suggestions, execution, and in-place editing. |
| **Pydantic-AI** | `https://github.com/NVIDIA-AI-Blueprints/pydantic-ai` | Model-agnostic AI agent framework with strict validation and structured output using Pydantic. |
| **Hermes Agent** | `https://github.com/NVIDIA-AI-Blueprints/hermes-agent` | Flexible AI agent designed to grow with developers through persistent skills, memory, and tools. |
| **Data Flywheel** | `https://github.com/NVIDIA-AI-Blueprints/data-flywheel` | Pipeline architecture for continuous data collection, synthetic curation, and automated model fine-tuning. |
| **GPU Query Engine (GQE)** | Reference Architecture | GPU-accelerated SQL analytics engine utilizing RAPIDS and CUDA for real-time querying. |

### Retail & Supply Chain
| Blueprint | GitHub Repository | Focus & Architecture |
| :--- | :--- | :--- |
| **Retail Shopping Assistant** | `https://github.com/NVIDIA-AI-Blueprints/retail-shopping-assistant` | Multimodal shopping advisor with real-time visual recommendation and inventory lookup. |
| **Retail Catalog Enrichment** | `https://github.com/NVIDIA-AI-Blueprints/Retail-Catalog-Enrichment` | GenAI-powered ingestion system transforming raw product images and blurbs into rich e-commerce catalogs. |
| **Retail Agentic Commerce** | `https://github.com/NVIDIA-AI-Blueprints/Retail-Agentic-Commerce` | Agentic Commerce Protocol implementation enabling automated AI checkout and terms negotiation. |
| **Multi-Agent Intelligent Warehouse**| `https://github.com/NVIDIA-AI-Blueprints/Multi-Agent-Intelligent-Warehouse` | Swarm simulation optimizing autonomous mobile robots (AMRs), picking routes, and warehouse logistics. |

### Financial Services
| Blueprint | GitHub Repository | Focus & Architecture |
| :--- | :--- | :--- |
| **Portfolio Optimization** | `https://github.com/NVIDIA-AI-Blueprints/portfolio-optimization` | GPU-accelerated toolkit for quantitative backtesting, risk parity, and asset allocation scaling. |
| **Quantitative Signal Discovery** | `https://github.com/NVIDIA-AI-Blueprints/quantitative-signal-discovery-agent` | Autonomous agent discovering, testing, and ranking alpha signals from streaming market data. |
| **Financial Fraud Detection** | `https://github.com/NVIDIA-AI-Blueprints/financial-fraud-detection` | Real-time GNN and transformer framework detecting transaction anomalies with ultra-low false positives. |
| **Transaction Foundation Model** | `https://github.com/NVIDIA-AI-Blueprints/transaction-foundation-model` | Tabular transformer creating intelligent embeddings from banking and credit card transaction histories. |
| **AI Model Distillation for Finance**| `https://github.com/NVIDIA-AI-Blueprints/ai-model-distillation-for-financial-data` | Distilling 70B+ LLMs into sub-8B models fine-tuned specifically for compliance, filings, and finance. |

### Healthcare & Life Sciences
| Blueprint | GitHub Repository | Focus & Architecture |
| :--- | :--- | :--- |
| **Biomedical AI-Q Research Agent** | `https://github.com/NVIDIA-AI-Blueprints/biomedical-aiq-research-agent` | Specialized literature synthesis and clinical trial matching agent for life science researchers. |
| **Single Cell Analysis** | `https://github.com/NVIDIA-AI-Blueprints/single-cell-analysis-blueprint` | End-to-end GPU workflows (RAPIDS single-cell) for scRNA-seq clustering and cell annotation. |
| **Genomics Analysis** | `https://github.com/NVIDIA-AI-Blueprints/genomics-analysis` | Clara Parabricks accelerated pipelines for secondary analysis, variant calling, and alignment. |
| **Ambient Healthcare Agents** | `https://github.com/NVIDIA-AI-Blueprints/ambient-healthcare-agents` | Ambient clinical listening agent creating structured SOAP notes from doctor-patient encounters. |

### Media & Physical AI
| Blueprint | GitHub Repository | Focus & Architecture |
| :--- | :--- | :--- |
| **Content Localization** | `https://github.com/NVIDIA-AI-Blueprints/content-localization` | Multi-language dubbing, translation, and neural lip-sync matching video to translated speech. |
| **AI Factory Digital Twins** | NVIDIA Omniverse DSX | Omniverse-based simulation designing, testing, and optimizing data center cooling, power, and rack layouts. |

---

## 2. Standard Deployment Workflow

### Prerequisite Environment
- **OS**: Linux (Ubuntu 22.04/24.04 LTS recommended) or Windows WSL2 with NVIDIA Drivers >= 535.
- **Hardware**: NVIDIA GPU with >= 16GB VRAM (RTX 4090, A10, A100, H100).
- **Tooling**:
  ```bash
  # Check GPU status
  nvidia-smi
  
  # Ensure NVIDIA Container Toolkit is active
  docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
  ```

### Cloning and Inspecting a Blueprint
Hermes Agent can automatically inspect and clone any blueprint into `~/.hermes/repos/` or active workspace:
```bash
git clone https://github.com/NVIDIA-AI-Blueprints/<blueprint-name>.git
cd <blueprint-name>
```

### Running with NVIDIA NIM Microservices
NVIDIA Blueprints connect directly to NVIDIA NIM endpoints. In Hermes Agent, configure:
```yaml
# In ~/.hermes/config.yaml
providers:
  nvidia:
    api: https://integrate.api.nvidia.com/v1
    key_env: NVIDIA_API_KEY
    models:
      - nvidia/llama-3.1-nemotron-70b-instruct
      - meta/llama-3.2-11b-vision-instruct
      - deepseek-ai/deepseek-v4-flash-0731
```
