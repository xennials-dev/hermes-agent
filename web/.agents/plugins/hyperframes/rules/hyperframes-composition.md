# HyperFrames Composition Rules

When writing or modifying HyperFrames HTML compositions, CSS styles, or JavaScript animations:

1. **Root Configuration**:
   - The top-level composition container MUST have `id="root"`, `data-composition-id`, `data-start="0"`, `data-duration`, `data-width`, and `data-height`.
2. **Timeline Registration**:
   - ALWAYS push timelines to `window.__timelines`. Never rely on unassigned GSAP tweens.
3. **Determinism**:
   - NEVER use `Math.random()`. Parallel render workers seek non-linearly and will produce mismatched frame hashes.
4. **Visibility & Transitions**:
   - Reveal elements explicitly with `opacity: 1` or `autoAlpha: 1`.
   - Pre-hide elements in CSS or bare `gsap.set()` outside the timeline.
5. **Tracks**:
   - Assign integer `data-track-index` (1, 2, 3...) to clips to establish deterministic stacking context.
