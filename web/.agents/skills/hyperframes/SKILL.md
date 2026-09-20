---
name: hyperframes
description: >-
  Build, automate, validate, and render code-first HTML/CSS/GSAP videos with HyperFrames.
  Use when asked to create promotional videos, product launches, PR explainers, kinetic typography,
  code walkthroughs, or when running `hyperframes` CLI (`init`, `preview`, `check`, `render`),
  or embedding DocsVideo playback in React/web apps.
---

# HyperFrames Video Engineering & Agent Orchestration Skill

HyperFrames is an open-source, code-first video framework that builds production videos on web standards: **HTML**, **CSS**, **GSAP**, and **WebGL/Canvas**.

This skill guides the agent in authoring compositions, managing the HyperFrames CLI, avoiding engine pitfalls, and autonomously turning code diffs, READMEs, and product designs into polished MP4 videos.

---

## 🎯 Proactive Workflow: Automated Video Production

When the user asks to create a video, explainer, or walkthrough, take on the task autonomously through this 5-stage pipeline:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ 1. Scan Source  │ ──> │ 2. Storyboard   │ ──> │ 3. Composition  │ ──> │ 4. Lint Check   │ ──> │ 5. Render Video │
│ Git / Doc / UI  │     │ Beats & Timing  │     │ HTML + GSAP     │     │ CLI Validator   │     │ MP4 Output      │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 1. Source Intake
- **PR or Git Diff**: Run `git log -n 5`, `git status`, or `git diff` to extract what changed, why it matters, and code snippets for terminal animation.
- **Product / Feature Launch**: Scan `README.md`, landing pages, or UI components to gather headlines, value propositions, and visual assets.

### 2. Storyboard & Beat Sheet
Map the composition into defined time intervals (typically 10s–30s total duration):
- **Scene 1 (0s–4s)**: Hook, brand badge, kinetic title, ambient background.
- **Scene 2 (4s–9s)**: Demonstration, terminal code walkthrough, or UI interaction.
- **Scene 3 (9s–12s)**: Key metrics, value summary, and call to action.

### 3. Composition Markup
Author standard HyperFrames HTML (see [Composition Architecture](#composition-architecture)).

### 4. Linter & Cold-Seek Validation
Run `npx hyperframes check <path-to-index.html>` to detect seek-order hazards or occlusion issues before rendering.

### 5. Render
Execute `npx hyperframes render <path-to-index.html> --output <filename.mp4>`.

---

## 📐 Composition Architecture

A HyperFrames project is plain web technology. Every composition begins with a declarative root:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Video Title</title>
  <link rel="stylesheet" href="./styles.css" />
  <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
</head>
<body>
  <!-- Composition Root: defines canvas bounds and total duration -->
  <div
    id="root"
    data-composition-id="main"
    data-start="0"
    data-duration="12"
    data-width="1920"
    data-height="1080"
  >
    <!-- Timed Scene Clip -->
    <div
      class="clip"
      id="scene-1"
      data-start="0"
      data-duration="4"
      data-track-index="1"
    >
      <h1 class="title">Hello World</h1>
    </div>
  </div>

  <script>
    // 1. Mandatory Timeline Registration
    window.__timelines = window.__timelines || [];
    const tl = gsap.timeline();
    window.__timelines.push(tl);

    // 2. Animations
    tl.fromTo(".title", { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 1 });
  </script>
</body>
</html>
```

### Essential Attributes
| Attribute | Scope | Description |
| :--- | :--- | :--- |
| `id="root"` | Root `<div>` | Identifies the primary composition container |
| `data-composition-id` | Root `<div>` | Identifier for the composition (e.g. `"main"`) |
| `data-width` & `data-height` | Root `<div>` | Target resolution (e.g. `1920` x `1080`, or `1080` x `1920` for vertical) |
| `data-duration` | Root & Clips | Duration in seconds (floating point or integer) |
| `class="clip"` | Any scene element | Marks an element as participating in the timeline |
| `data-track-index` | Clips | Layer track (integer, 1-indexed, higher tracks paint above lower) |
| `data-start` | Clips | Start timestamp in seconds on the main timeline |

---

## ⚡ The 7 Golden Rules of HyperFrames

Breaking Rules 1–5 causes engine rendering errors; Rules 6–7 are critical visual best practices:

1. **Register All Timelines on `window.__timelines`**:
   The headless renderer controls seeking by inspecting `window.__timelines`. Any unregistered timeline will not be rendered.
2. **Video Tags Must Be `muted`**:
   Browsers block autoplay and headless renders desync audio if embedded in `<video>`. Place audio in separate `<audio>` tags for timeline audio mixing.
3. **Strict Determinism (NO `Math.random()`)**:
   Headless renders execute across parallel workers seeking arbitrary frames. Any non-deterministic call causes frame jitter and tearing.
   - Use a seeded PRNG (e.g. `mulberry32`) if pseudo-randomness is required.
   - Quantize stepped holds on the integer frame number, not float seconds (`Math.floor(time * fps)`).
4. **Synchronous Timeline Construction**:
   Do not use `async`, `await`, or `fetch()` inside GSAP timeline declarations. Load all resources upfront.
5. **Timed Elements Require `class="clip"`**:
   Every visual scene or layer that has `data-start` and `data-duration` must include `class="clip"`.
6. **Explicit Entrance Animations**:
   Elements appearing without motion feel abrupt on video. Use `gsap.fromTo()` for reveals.
7. **Intentional Scene Transitions**:
   Cross-fade, scale, or wipe between scenes instead of hard unstyled jump cuts.

---

## 🛡️ Linter & Cold-Seek Pitfalls (PR Rules)

Headless multi-process render workers seek frames non-linearly. To ensure preview matches the rendered video:

### 1. Cold-Seek Visibility (`gsap_cold_seek_hidden_fromto_missing_reveal`)
- When revealing a hidden element with `gsap.fromTo()`, **always specify destination `opacity: 1`** (or `autoAlpha: 1`), not just start `opacity: 0`.
- Set initial hidden states in **CSS** or with bare `gsap.set()` **outside** the timeline, rather than relying on a `tl.set()` at position `0`.

### 2. Seek-Order Safety
- **No Relative Offsets on Multi-Writer Properties**: Avoid `"+=50"` if another tween animates the same property. State absolute endpoints.
- **No DOM Measurement in Callbacks**: Never call `getBoundingClientRect()` or `getTotalLength()` inside a timeline callback or tick. Measure once at build time.

### 3. SVG Draw-On Animations
- Ensure the SVG path has a static `d` attribute in HTML before calling `getTotalLength()`.
- Do not mix CSS `stroke-dasharray` with GSAP `strokeDashoffset` on the same node.
- Use `stroke-linecap: butt` (or keep opacity 0 until draw begins) to avoid round caps painting a rogue dot at frame 0.

---

## 🛠️ CLI Reference

Install and execute commands using `npx hyperframes`:

```bash
# Initialize a new composition project
npx hyperframes init my-video --example blank

# Launch live Studio preview server (default: http://localhost:3000)
npx hyperframes preview

# Check composition against official linter rules
npx hyperframes check index.html

# Render headless video to MP4
npx hyperframes render index.html --output output.mp4

# Render with specific worker count or resolution
npx hyperframes render index.html --workers 1 --output output.mp4
```

---

## 📺 Embedding Player in React (`DocsVideo`)

To showcase rendered videos or previews in a React 19 / Tailwind CSS v4 dashboard:

```tsx
import { DocsVideo } from "@/components/DocsVideo";

export function VideoSection() {
  return (
    <DocsVideo
      src="/videos/demo.mp4"
      poster="/images/poster.jpg"
      title="HyperFrames Feature Overview"
      autoPlay={false}
      loop={false}
    />
  );
}
```

Includes hover timestamp scrub preview, rate multiplier ($1\times, 1.25\times, 1.5\times, 2\times$), keyboard shortcuts (`Space`, `Left/Right`, `M`, `F`), and fullscreen support.
