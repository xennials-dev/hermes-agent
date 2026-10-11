import React from "react";
import { useCurrentFrame, spring, useVideoConfig } from "remotion";

export const Segment3: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const cardScale = spring({ frame, fps, config: { damping: 14 } });

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
      {/* Presenter 3 Card */}
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
            src="/presenter_3.png"
            alt="Presenter 3"
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
              color: "#E9C46A",
            }}
          >
            <span>PRESENTER 3 ON AIR</span>
          </div>
        </div>

        <h2 style={{ fontSize: 20, fontWeight: 800, color: "#FFF", marginBottom: 4 }}>
          Principal Cloud & Security Architect
        </h2>
        <p style={{ fontSize: 12, fontFamily: "'JetBrains Mono', monospace", color: "#E9C46A", marginBottom: 12 }}>
          1:00 - 1:30 • CLOUD & INTELLIGENCE
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
          Auto-Scaling Cluster & Kibana
        </div>

        <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: 10, fontSize: 13, color: "#94A3B8" }}>
          <li>▹ 3-node master cluster ensures quorum & no split-brain</li>
          <li>▹ Auto-scaling data nodes scale dynamically 1 to 12</li>
          <li>▹ Hardened Bastion Host with mTLS certificate security</li>
          <li>▹ Kibana sub-second search, APM service maps & traces</li>
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
                Auto-Scaling Elastic Cluster & Visual Intelligence
              </h1>
              <p style={{ fontSize: 13, color: "#94A3B8", marginTop: 4 }}>
                Resilient AWS ECS deployment with quorum protection and sub-second Kibana querying.
              </p>
            </div>
            <span
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 12,
                padding: "4px 10px",
                borderRadius: 6,
                backgroundColor: "rgba(233, 196, 106, 0.12)",
                border: "1px solid rgba(233, 196, 106, 0.3)",
                color: "#E9C46A",
              }}
            >
              CLOUD AUTO-SCALE
            </span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
            {/* Master Pool */}
            <div style={{ backgroundColor: "rgba(22, 34, 54, 0.6)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: 12, padding: 18 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12, fontSize: 13, fontWeight: 700 }}>
                <span>🏛️ MASTER QUORUM POOL</span>
                <span style={{ fontFamily: "'JetBrains Mono', monospace", color: "#88D7C6", fontSize: 11 }}>QUORUM: 2/3</span>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
                {["es01", "es02", "es03"].map((node) => (
                  <div
                    key={node}
                    style={{
                      backgroundColor: "rgba(136, 215, 198, 0.1)",
                      border: "1px solid #88D7C6",
                      borderRadius: 8,
                      padding: "10px 4px",
                      textAlign: "center",
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: 12,
                      color: "#88D7C6",
                      fontWeight: 700,
                    }}
                  >
                    <div>{node}</div>
                    <div style={{ fontSize: 9, opacity: 0.8 }}>MASTER</div>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 14, paddingTop: 10, borderTop: "1px solid rgba(255, 255, 255, 0.08)", fontSize: 11, color: "#94A3B8", display: "flex", justifyContent: "space-between" }}>
                <span>Split-Brain Prevention:</span>
                <span style={{ color: "#88D7C6", fontWeight: 700 }}>GUARANTEED</span>
              </div>
            </div>

            {/* Auto-Scaling Data Pool */}
            <div style={{ backgroundColor: "rgba(22, 34, 54, 0.6)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: 12, padding: 18 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12, fontSize: 13, fontWeight: 700 }}>
                <span>⚡ DATA / INGESTION POOL</span>
                <span style={{ fontFamily: "'JetBrains Mono', monospace", color: "#E9C46A", fontSize: 11 }}>DYNAMIC 1 - 12</span>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
                <div style={{ backgroundColor: "rgba(14, 22, 36, 0.8)", border: "1px solid rgba(255, 255, 255, 0.1)", borderRadius: 8, padding: "10px 4px", textAlign: "center", fontFamily: "'JetBrains Mono', monospace", fontSize: 11 }}>
                  data01
                </div>
                <div style={{ backgroundColor: "rgba(14, 22, 36, 0.8)", border: "1px solid rgba(255, 255, 255, 0.1)", borderRadius: 8, padding: "10px 4px", textAlign: "center", fontFamily: "'JetBrains Mono', monospace", fontSize: 11 }}>
                  data02
                </div>
                <div style={{ backgroundColor: "rgba(233, 196, 106, 0.15)", border: "1px solid #E9C46A", borderRadius: 8, padding: "10px 4px", textAlign: "center", fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "#E9C46A", fontWeight: 700 }}>
                  + AUTO
                </div>
              </div>
              <div style={{ marginTop: 14, paddingTop: 10, borderTop: "1px solid rgba(255, 255, 255, 0.08)", fontSize: 11, color: "#94A3B8", display: "flex", justifyContent: "space-between" }}>
                <span>Scaling Trigger:</span>
                <span style={{ color: "#E9C46A", fontWeight: 700 }}>CPU &gt; 70% | HEAP &gt; 75%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Security & Intelligence Bar */}
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
          <div style={{ display: "flex", gap: 32 }}>
            <div>
              <div style={{ fontSize: 11, color: "#64748B" }}>SEARCH LATENCY</div>
              <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 15, fontWeight: 800, color: "#88D7C6" }}>&lt; 1.0 SEC</div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: "#64748B" }}>SECURITY TUNNEL</div>
              <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 15, fontWeight: 800, color: "#FFF" }}>BASTION + mTLS</div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: "#64748B" }}>VISUAL EXPLORATION</div>
              <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 15, fontWeight: 800, color: "#E9C46A" }}>KIBANA 8.6+</div>
            </div>
          </div>
          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: "#88D7C6" }}>
            AWS ECS Fargate & EC2 Cluster
          </div>
        </div>
      </div>
    </div>
  );
};
