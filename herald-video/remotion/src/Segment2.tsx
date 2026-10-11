import React from "react";
import { useCurrentFrame, spring, useVideoConfig } from "remotion";

export const Segment2: React.FC = () => {
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
      {/* Presenter 2 Card */}
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
            src="/presenter_2.png"
            alt="Presenter 2"
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
              color: "#EE6F57",
            }}
          >
            <span>PRESENTER 2 ON AIR</span>
          </div>
        </div>

        <h2 style={{ fontSize: 20, fontWeight: 800, color: "#FFF", marginBottom: 4 }}>
          Lead Data Pipeline Architect
        </h2>
        <p style={{ fontSize: 12, fontFamily: "'JetBrains Mono', monospace", color: "#EE6F57", marginBottom: 12 }}>
          0:30 - 1:00 • INGESTION PIPELINE
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
          Dual Ingestion & Fleet Governance
        </div>

        <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: 10, fontSize: 13, color: "#94A3B8" }}>
          <li>▹ Dual pipelines decouple logs from APM traces</li>
          <li>▹ Filebeat streams to 2x Load-Balanced Logstash</li>
          <li>▹ APM agents instrument 10+ core programming stacks</li>
          <li>▹ Fleet Server cluster coordinates zero-downtime upgrades</li>
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
                Dual Ingestion Telemetry Architecture
              </h1>
              <p style={{ fontSize: 13, color: "#94A3B8", marginTop: 4 }}>
                Specialized routing for high-volume logs vs. deep distributed APM traces.
              </p>
            </div>
            <span
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 12,
                padding: "4px 10px",
                borderRadius: 6,
                backgroundColor: "rgba(136, 215, 198, 0.12)",
                border: "1px solid rgba(136, 215, 198, 0.3)",
                color: "#88D7C6",
              }}
            >
              DUAL PIPELINE
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
            {/* Log Track */}
            <div style={{ backgroundColor: "rgba(22, 34, 54, 0.6)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: 12, padding: "16px 20px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontSize: 11, fontWeight: 800, fontFamily: "'JetBrains Mono', monospace", padding: "4px 8px", borderRadius: 4, backgroundColor: "rgba(42, 157, 143, 0.2)", color: "#88D7C6" }}>
                LOG TRACK
              </span>
              <div style={{ display: "flex", alignItems: "center", gap: 12, flex: 1, margin: "0 20px" }}>
                <span style={{ backgroundColor: "rgba(14, 22, 36, 0.8)", border: "1px solid rgba(255, 255, 255, 0.1)", borderRadius: 8, padding: "8px 14px", fontSize: 12, fontWeight: 700 }}>📂 App Logs</span>
                <span style={{ color: "#88D7C6" }}>➔</span>
                <span style={{ backgroundColor: "rgba(14, 22, 36, 0.8)", border: "1px solid rgba(255, 255, 255, 0.1)", borderRadius: 8, padding: "8px 14px", fontSize: 12, fontWeight: 700 }}>⚡ Filebeat</span>
                <span style={{ color: "#88D7C6" }}>➔</span>
                <span style={{ backgroundColor: "rgba(14, 22, 36, 0.8)", border: "1px solid #88D7C6", borderRadius: 8, padding: "8px 14px", fontSize: 12, fontWeight: 700, color: "#88D7C6" }}>🔄 Logstash (2x LB + GeoIP)</span>
                <span style={{ color: "#88D7C6" }}>➔</span>
                <span style={{ backgroundColor: "rgba(136, 215, 198, 0.15)", border: "1px solid #88D7C6", borderRadius: 8, padding: "8px 14px", fontSize: 12, fontWeight: 700, color: "#88D7C6" }}>🗄️ Elasticsearch</span>
              </div>
            </div>

            {/* APM Track */}
            <div style={{ backgroundColor: "rgba(22, 34, 54, 0.6)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: 12, padding: "16px 20px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontSize: 11, fontWeight: 800, fontFamily: "'JetBrains Mono', monospace", padding: "4px 8px", borderRadius: 4, backgroundColor: "rgba(238, 111, 87, 0.2)", color: "#EE6F57" }}>
                APM TRACK
              </span>
              <div style={{ display: "flex", alignItems: "center", gap: 12, flex: 1, margin: "0 20px" }}>
                <span style={{ backgroundColor: "rgba(14, 22, 36, 0.8)", border: "1px solid rgba(255, 255, 255, 0.1)", borderRadius: 8, padding: "8px 14px", fontSize: 12, fontWeight: 700 }}>💻 APM SDKs</span>
                <span style={{ color: "#EE6F57" }}>➔</span>
                <span style={{ backgroundColor: "rgba(14, 22, 36, 0.8)", border: "1px solid rgba(255, 255, 255, 0.1)", borderRadius: 8, padding: "8px 14px", fontSize: 12, fontWeight: 700 }}>📦 Elastic Agent</span>
                <span style={{ color: "#EE6F57" }}>➔</span>
                <span style={{ backgroundColor: "rgba(14, 22, 36, 0.8)", border: "1px solid #EE6F57", borderRadius: 8, padding: "8px 14px", fontSize: 12, fontWeight: 700, color: "#EE6F57" }}>🛡️ Fleet Server (2x LB)</span>
                <span style={{ color: "#EE6F57" }}>➔</span>
                <span style={{ backgroundColor: "rgba(238, 111, 87, 0.15)", border: "1px solid #EE6F57", borderRadius: 8, padding: "8px 14px", fontSize: 12, fontWeight: 700, color: "#EE6F57" }}>🗄️ Elasticsearch</span>
              </div>
            </div>
          </div>
        </div>

        {/* Supported Languages Grid */}
        <div style={{ backgroundColor: "rgba(22, 34, 54, 0.6)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: 12, padding: "16px 20px" }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: "#FFF", marginBottom: 8 }}>
            SUPPORTED APM RUNTIME LIBRARIES:
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {["Node.js", "Python", "Golang", "Java", ".NET", "Ruby", "PHP", "OpenTelemetry"].map((lang) => (
              <span
                key={lang}
                style={{
                  fontSize: 11,
                  fontFamily: "'JetBrains Mono', monospace",
                  padding: "4px 10px",
                  borderRadius: 4,
                  backgroundColor: "rgba(255, 255, 255, 0.05)",
                  border: "1px solid rgba(255, 255, 255, 0.12)",
                  color: "#F8FAFC",
                }}
              >
                {lang}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
