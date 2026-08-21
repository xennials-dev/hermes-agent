---
name: generative-video-audio
description: "Orchestrate talking avatars, lip-sync, and video generation."
version: 1.0.0
author: Terrance (tee), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [VideoGeneration, LipSync, Wav2Lip, SadTalker, HunyuanVideo, AI]
    related_skills: [knowledge-system, ai-concierge]
---

# Generative Talking Video & Lip-Sync Pipelines

Automate talking head video synthesis, speech-driven facial animation, and text-to-video generation using Wav2Lip, SadTalker, and HunyuanVideo.

---

## 1. Quick Reference

| Pipeline | Engine | Typical Command |
|---|---|---|
| **Lip-Sync Video to Audio** | Wav2Lip | `python inference.py --checkpoint_path wav2lip_gan.pth --face input_video.mp4 --audio voice.wav` |
| **Still Photo to Talking Video** | SadTalker | `python inference.py --driven_audio voice.wav --source_image avatar.png --still` |
| **Text-to-Video Synthesis** | HunyuanVideo | `python sample_video.py --prompt "Cinematic product launch" --video-size 720 1280` |

---

## 2. Automated Avatar Video Workflow

```
[Target Script Text]
        │
        ▼ (TTS Engine / ElevenLabs / Bark)
   [voice.wav]
        │
        ├─────────────────────────────┐
        ▼ (Single Portrait)           ▼ (Existing Video Clip)
  [SadTalker Avatar]            [Wav2Lip Re-Sync]
        │                             │
        └──────────────┬──────────────┘
                       ▼
            [Polished MP4 Video]
```
