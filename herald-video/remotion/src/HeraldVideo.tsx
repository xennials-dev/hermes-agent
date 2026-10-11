import React from "react";
import { Sequence, useCurrentFrame, interpolate } from "remotion";
import { Segment1 } from "./Segment1";
import { Segment2 } from "./Segment2";
import { Segment3 } from "./Segment3";

export const HeraldVideo: React.FC = () => {
  const frame = useCurrentFrame();

  // Background subtle pulse
  const bgGlow = interpolate(frame % 120, [0, 60, 120], [0.15, 0.28, 0.15]);

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: "#080D14",
        backgroundImage: `radial-gradient(circle at 50% 10%, rgba(17, 30, 51, 0.9) 0%, #080D14 70%)`,
        width: "100%",
        height: "100%",
        position: "relative",
        fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif",
        color: "#F8FAFC",
        overflow: "hidden",
      }}
    >
      {/* Background Grid Pattern */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: `
            linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px)
          `,
          backgroundSize: "48px 48px",
          opacity: 0.6,
        }}
      />

      {/* Top Broadcast Branding Bar */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 72,
          padding: "0 48px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
          backgroundColor: "rgba(8, 13, 20, 0.85)",
          backdropFilter: "blur(12px)",
          zIndex: 50,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div
            style={{
              width: 36,
              height: 36,
              background: "linear-gradient(135deg, #88D7C6, #2A9D8F)",
              borderRadius: 8,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 800,
              color: "#080D14",
              fontSize: 18,
            }}
          >
            H
          </div>
          <span style={{ fontSize: 20, fontWeight: 800, letterSpacing: "-0.02em" }}>HERALD</span>
          <span
            style={{
              fontSize: 11,
              fontFamily: "'JetBrains Mono', monospace",
              color: "#88D7C6",
              backgroundColor: "rgba(136, 215, 198, 0.12)",
              border: "1px solid rgba(136, 215, 198, 0.3)",
              padding: "3px 10px",
              borderRadius: 4,
            }}
          >
            OBSERVABILITY SUITE
          </span>
        </div>

        {/* Phase Pill Indicators */}
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div
            style={{
              padding: "6px 16px",
              borderRadius: 20,
              fontSize: 12,
              fontWeight: 600,
              color: frame < 900 ? "#F8FAFC" : "#64748B",
              backgroundColor: frame < 900 ? "rgba(136, 215, 198, 0.18)" : "rgba(255, 255, 255, 0.04)",
              border: frame < 900 ? "1px solid #88D7C6" : "1px solid transparent",
            }}
          >
            01 • FOUNDATIONAL CRISIS (0:00 - 0:30)
          </div>
          <div
            style={{
              padding: "6px 16px",
              borderRadius: 20,
              fontSize: 12,
              fontWeight: 600,
              color: frame >= 900 && frame < 1800 ? "#F8FAFC" : "#64748B",
              backgroundColor: frame >= 900 && frame < 1800 ? "rgba(238, 111, 87, 0.18)" : "rgba(255, 255, 255, 0.04)",
              border: frame >= 900 && frame < 1800 ? "1px solid #EE6F57" : "1px solid transparent",
            }}
          >
            02 • DUAL PIPELINE INGEST (0:30 - 1:00)
          </div>
          <div
            style={{
              padding: "6px 16px",
              borderRadius: 20,
              fontSize: 12,
              fontWeight: 600,
              color: frame >= 1800 ? "#F8FAFC" : "#64748B",
              backgroundColor: frame >= 1800 ? "rgba(233, 196, 106, 0.18)" : "rgba(255, 255, 255, 0.04)",
              border: frame >= 1800 ? "1px solid #E9C46A" : "1px solid transparent",
            }}
          >
            03 • AUTO-SCALE & KIBANA (1:00 - 1:30)
          </div>
        </div>
      </div>

      {/* Segment 1: Presenter 1 (0:00 - 0:30 / Frames 0 - 900) */}
      <Sequence from={0} durationInFrames={900}>
        <Segment1 />
      </Sequence>

      {/* Segment 2: Presenter 2 (0:30 - 1:00 / Frames 900 - 1800) */}
      <Sequence from={900} durationInFrames={900}>
        <Segment2 />
      </Sequence>

      {/* Segment 3: Presenter 3 (1:00 - 1:30 / Frames 1800 - 2700) */}
      <Sequence from={1800} durationInFrames={900}>
        <Segment3 />
      </Sequence>

      {/* Bottom Live Teleprompter Subtitle Banner */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: 84,
          backgroundColor: "rgba(8, 13, 20, 0.94)",
          borderTop: "1px solid rgba(255, 255, 255, 0.08)",
          display: "flex",
          alignItems: "center",
          padding: "0 48px",
          gap: 20,
          zIndex: 50,
        }}
      >
        <span
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 11,
            fontWeight: 800,
            padding: "4px 8px",
            borderRadius: 4,
            backgroundColor: "#88D7C6",
            color: "#080D14",
          }}
        >
          CC LIVE
        </span>
        <div style={{ flex: 1, fontSize: 16, fontWeight: 500, color: "#F8FAFC" }}>
          {frame < 300 && "Welcome. Modern software architectures are transitioning from monoliths to distributed microservices."}
          {frame >= 300 && frame < 600 && "As systems distribute across networks, monitoring health and isolating errors becomes exponentially difficult."}
          {frame >= 600 && frame < 900 && "Herald unifies the three pillars of observability into one automated AWS ECS stack with zero SaaS markups."}

          {frame >= 900 && frame < 1200 && "Herald's dual-ingestion engine separates telemetry into two optimized, high-throughput pathways."}
          {frame >= 1200 && frame < 1500 && "Track one captures log data via Filebeat into a load-balanced Logstash cluster with GeoIP enrichment."}
          {frame >= 1500 && frame < 1800 && "Track two collects deep APM traces across Go, Python, Node, Java, and .NET with centralized Fleet Server governance."}

          {frame >= 1800 && frame < 2100 && "Herald provisions an AWS ECS cluster backed by a dedicated three-node master pool for quorum."}
          {frame >= 2100 && frame < 2400 && "Data and ingestion nodes dynamically auto-scale from 1 to 12 instances based on ingestion and CPU pressure."}
          {frame >= 2400 && "A secure Bastion Host and Kibana 8.6+ deliver sub-second search with 100% data sovereignty."}
        </div>
      </div>
    </div>
  );
};
