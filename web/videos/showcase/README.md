# HyperFrames Video Showcase

A standards-compliant, code-first video composition powered by [HyperFrames](https://hyperframes.heygen.com) and tailored for Xennials.

---

## 🎬 Composition Overview

- **Dimensions**: 1920 × 1080 (16:9 Landscape)
- **Duration**: 12 seconds
- **Engine**: Plain HTML + CSS + GSAP (`https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js`)
- **Scenes**:
  - **Scene 1 (0.0s – 4.0s)**: Kinetic Title & Brand Hook (`#scene-1`) with animated badge and radial ambient glow.
  - **Scene 2 (4.0s – 8.5s)**: Terminal Code Walkthrough (`#scene-2`) highlighting declarative markup and agent-first video generation.
  - **Scene 3 (8.5s – 12.0s)**: Value Call-To-Action Card (`#scene-3`) resolving on headless render commands.

---

## 🚀 Commands

Run these commands from this directory (`videos/showcase/`) or from the workspace root:

```bash
# 1. Check composition against HyperFrames linter rules
npx hyperframes check index.html

# 2. Preview live in HyperFrames Studio
npx hyperframes preview

# 3. Render high-definition video to MP4
npx hyperframes render index.html --output output.mp4
```

---

## ⚡ Technical Compliance

- **Timeline Registration**: Timelines are registered on `window.__timelines`.
- **Determinism**: Zero `Math.random()`; fully reproducible across parallel render workers.
- **Cold-Seek Safety**: Explicit destination `opacity: 1` on all reveals; initial hidden states defined outside timelines.
- **Timed Tracks**: Every timed element has `class="clip"`, `data-track-index`, `data-start`, and `data-duration`.
