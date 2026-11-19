# Deployment Guide — Service #12: ComfyUI Creative Engine

## 1. Local Modular Hub
```bash
cd techstarz101_services/12_comfyui_creative_engine
python hub/app.py
# Open http://localhost:7876
```

## 2. GPU Enablement (ComfyUI & InvokeAI)
On NVIDIA hosts with the NVIDIA Container Toolkit installed, uncomment or add `deploy.resources.reservations.devices` for `driver: nvidia` inside `tools/comfyui/docker-compose.yml` or `tools/invokeai/docker-compose.yml` for full CUDA acceleration.

## 3. Boot Any Tool Independently
```bash
cd tools/rembg-api
cp .env.example .env
docker compose up -d
# Open http://localhost:6910
```
