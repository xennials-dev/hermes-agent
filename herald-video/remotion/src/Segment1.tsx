import React from "react";
import { useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";

export const Segment1: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Entrance spring animations
  const cardScale = spring({ frame, fps, config: { damping: 14 } });
  const meterProgress = interpolate(frame, [30, 200], [0, 100], { extrapolateRight: "clamp" });

  return (
    <div
      style={{
        position: "absolute",
        top: 72,
        bottom: 84,
        left: 0,
        right: 0,
        padding: "36px 48px",
        display: "grid",
        gridTemplateColumns: "380px 1fr",
        gap: "40px",
      }}
    >
      {/* Presenter 1 Card */}
      <div
        style={{
          backgroundColor: "rgba(14, 22, 36, 0.75)",
          backdropFilter: "blur(16px)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: 16,
          padding: 24,
          display: "flex",
          flexDirection: "column",
          transform: `scale(${cardScale})`,
          boxShadow: "0 12px 30px rgba(0, 0, 0, 0.5)",
        }}
      >
        <div
          style={{
            position: "relative",
            width: "100%",
            height: 240,
            borderRadius: 12,
            overflow: "hidden",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            marginBottom: 20,
            backgroundColor: "#030712",
          }}
        >
          <img
            src="/presenter_1.png"
            alt="Presenter 1"
            style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "top center" }}
          />
          <div
            style={{
              position: "absolute",
              bottom: 12,
              left: 12,
              display: "flex",
              alignItems: "center",
              gap: 6,
              padding: "4px 10px",
              backgroundColor: "rgba(8, 13, 20, 0.85)",
              border: "1px solid rgba(255, 255, 255, 0.12)",
              borderRadius: 20,
              fontSize: 11,
              fontWeight: 700,
              color: "#88D7C6",
            }}
          >
            <span>PRESENTER 1 ON AIR</span>
          </div>
        </div>

        <h2 style={{ fontSize: 20, fontWeight: 800, color: "#FFF", marginBottom: 4 }}>
          Chief Systems Architect
        </h2>
        <p style={{ fontSize: 12, fontFamily: "'JetBrains Mono', monospace", color: "#88D7C6", marginBottom: 12 }}>
          0:00 - 0:30 • FOUNDATIONAL ARCHITECTURE
        </p>
        <div
          style={{
            display: "inline-block",
            fontSize: 11,
            fontWeight: 700,
            padding: "3px 8px",
            borderRadius: 4,
            backgroundColor: "rgba(255, 255, 255, 0.06)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            color: "#94A3B8",
            marginBottom: 16,
          }}
        >
          The Observability Crisis & Herald Solution
        </div>

        <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: 10, fontSize: 13, color: "#94A3B8" }}>
          <li>▹ Microservices fragment telemetry across networks</li>
          <li>▹ Unified 3 Pillars: Logs, Traces & Metrics</li>
          <li>▹ Escaping high Datadog & New Relic SaaS billing</li>
          <li>▹ Herald automates AWS ECS deployment in minutes</li>
        </ul>
      </div>

      {/* Infographic Presentation Area */}
      <div
        style={{
          backgroundColor: "rgba(14, 22, 36, 0.55)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: 16,
          padding: "28px 32px",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", borderBottom: "1px solid rgba(255, 255, 255, 0.08)", paddingBottom: 16, marginBottom: 24 }}>
            <div>
              <h1 style={{ fontSize: 26, fontWeight: 800, color: "#FFF", letterSpacing: "-0.02em" }}>
                The Three Pillars of Observability
              </h1>
              <p style={{ fontSize: 13, color: "#94A3B8", marginTop: 4 }}>
                Explore logs, traces, and metrics in a single unified interface.
              </p>
            </div>
            <span
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 12,
                padding: "4px 10px",
                borderRadius: 6,
                backgroundColor: "rgba(238, 111, 87, 0.12)",
                border: "1px solid rgba(238, 111, 87, 0.3)",
                color: "#EE6F57",
              }}
            >
              PILLAR INGEST
            </span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 18 }}>
            {/* Logs */}
            <div style={{ backgroundColor: "rgba(22, 34, 54, 0.6)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: 12, padding: 20 }}>
              <div style={{ fontSize: 24, marginBottom: 8 }}>📄</div>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: "#FFF", marginBottom: 6 }}>Structured Logs</h3>
              <p style={{ fontSize: 12, color: "#94A3B8", lineHeight: 1.45, marginBottom: 12 }}>
                Continuous capture of discrete events, error stack traces, and access entries across microservices.
              </p>
              <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "#88D7C6" }}>
                Filebeat Log Streaming
              </div>
            </div>

            {/* Traces */}
            <div style={{ backgroundColor: "rgba(22, 34, 54, 0.6)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: 12, padding: 20 }}>
              <div style={{ fontSize: 24, marginBottom: 8 }}>🕸️</div>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: "#FFF", marginBottom: 6 }}>Distributed Traces</h3>
              <p style={{ fontSize: 12, color: "#94A3B8", lineHeight: 1.45, marginBottom: 12 }}>
                End-to-end request lifecycle tracking through microservice boundaries to pinpoint latency bottlenecks.
              </p>
              <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "#EE6F57" }}>
                APM Waterfall Spans
              </div>
            </div>

            {/* Metrics */}
            <div style={{ backgroundColor: "rgba(22, 34, 54, 0.6)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: 12, padding: 20 }}>
              <div style={{ fontSize: 24, marginBottom: 8 }}>📊</div>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: "#FFF", marginBottom: 6 }}>System Metrics</h3>
              <p style={{ fontSize: 12, color: "#94A3B8", lineHeight: 1.45, marginBottom: 12 }}>
                Real-time CPU, RAM, heap allocation, and HTTP throughput indicators sampled continuously.
              </p>
              <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "#E9C46A" }}>
                Container & Host Telemetry
              </div>
            </div>
          </div>
        </div>

        {/* TCO Comparison Banner */}
        <div
          style={{
            backgroundColor: "rgba(22, 34, 54, 0.6)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: 12,
            padding: "16px 24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: "#FFF" }}>Production-Ready ELK on AWS ECS</div>
            <div style={{ fontSize: 12, color: "#94A3B8" }}>Eliminates weeks of DIY manual config while saving up to 80% vs commercial SaaS</div>
          </div>
          <div
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 13,
              fontWeight: 800,
              color: "#88D7C6",
              backgroundColor: "rgba(136, 215, 198, 0.12)",
              border: "1px solid rgba(136, 215, 198, 0.3)",
              padding: "6px 14px",
              borderRadius: 6,
            }}
          >
            100% DATA SOVEREIGNTY
          </div>
        </div>
      </div>
    </div>
  );
};
