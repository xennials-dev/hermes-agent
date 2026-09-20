// @vitest-environment jsdom
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import type { ReactNode } from "react";
import { DocsVideo } from "./DocsVideo";

let container: HTMLDivElement;
let root: Root;

async function render(ui: ReactNode) {
  container = document.createElement("div");
  document.body.append(container);
  root = createRoot(container);
  await act(async () => root.render(ui));
}

beforeEach(() => {
  // Clear DOM before each test
  document.body.innerHTML = "";
});

afterEach(async () => {
  if (root) {
    await act(async () => root.unmount());
  }
  container?.remove();
});

describe("DocsVideo Component", () => {
  it("renders with given video source, poster, and accessible labels", async () => {
    await render(
      <DocsVideo
        src="https://example.com/demo.mp4"
        poster="https://example.com/poster.jpg"
        title="Sample Walkthrough"
      />
    );

    const videoEl = container.querySelector("video");
    expect(videoEl).not.toBeNull();
    expect(videoEl?.getAttribute("src")).toBe("https://example.com/demo.mp4");
    expect(videoEl?.getAttribute("poster")).toBe("https://example.com/poster.jpg");
    expect(videoEl?.getAttribute("aria-label")).toBe("Sample Walkthrough");
  });

  it("renders portrait mode when requested", async () => {
    await render(
      <DocsVideo
        src="https://example.com/portrait.mp4"
        title="Portrait Demo"
        portrait={true}
      />
    );

    const wrapper = container.firstElementChild as HTMLElement;
    expect(wrapper?.className).toContain("aspect-[9/16]");
  });

  it("renders controls and playback rate button", async () => {
    await render(
      <DocsVideo
        src="https://example.com/demo.mp4"
        title="Playback Test"
      />
    );

    // Rate button default is 1x
    const rateBtn = container.querySelector('button[aria-label^="Playback speed"]');
    expect(rateBtn).not.toBeNull();
    expect(rateBtn?.textContent).toContain("1×");

    // Play / pause button
    const playBtn = container.querySelector('button[aria-label="Play video"]');
    expect(playBtn).not.toBeNull();
  });
});
