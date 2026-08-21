import { useEffect, useState } from "react";
import {
  getBackendTargetInfo,
  getResolvedBackendUrl,
  probeBackend,
  setBackendTarget,
  type BackendProbeResult,
  type BackendTargetInfo,
} from "@/lib/backend-router";
import { Button } from "@nous-research/ui/ui/components/button";
import { Input } from "@nous-research/ui/ui/components/input";
import { Spinner } from "@nous-research/ui/ui/components/spinner";
import {
  Activity,
  CheckCircle2,
  Globe,
  Laptop,
  Radio,
  RefreshCw,
  Server,
  XCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface BackendRouterModalProps {
  open: boolean;
  onClose(): void;
}

export function BackendRouterModal({ open, onClose }: BackendRouterModalProps) {
  const [targetInfo, setTargetInfo] = useState<BackendTargetInfo>(getBackendTargetInfo);
  const [customUrl, setCustomUrl] = useState(getResolvedBackendUrl() || "http://127.0.0.1:9119");
  const [probing, setProbing] = useState(false);
  const [probeResult, setProbeResult] = useState<BackendProbeResult | null>(null);

  const runProbe = async (urlToTest: string) => {
    setProbing(true);
    try {
      const res = await probeBackend(urlToTest);
      setProbeResult(res);
    } finally {
      setProbing(false);
    }
  };

  useEffect(() => {
    if (open) {
      const info = getBackendTargetInfo();
      setTargetInfo(info);
      const active = getResolvedBackendUrl() || "http://127.0.0.1:9119";
      setCustomUrl(active);
      void runProbe(active);
    }
  }, [open]);

  if (!open) return null;

  const handleApply = (url: string) => {
    setBackendTarget(url);
    const updated = getBackendTargetInfo();
    setTargetInfo(updated);
    onClose();
    window.location.reload();
  };

  const handleReset = () => {
    setBackendTarget(null);
    const updated = getBackendTargetInfo();
    setTargetInfo(updated);
    onClose();
    window.location.reload();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg rounded-xl border border-border bg-background p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between pb-4 border-b border-border">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Server className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold tracking-wide text-foreground">
                Backend Connection Router
              </h2>
              <p className="text-xs text-muted-foreground">
                Configure local or remote Hermes Agent instance endpoint
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground text-sm font-mono px-2 py-1 rounded"
          >
            ✕
          </button>
        </div>

        {/* Live Status Card */}
        <div className="my-5 rounded-lg border border-border/80 bg-muted/40 p-4 space-y-3">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground font-mono">Current Host:</span>
            <span className="font-mono font-medium text-foreground">
              {targetInfo.url || `${window?.location?.origin || "Local Origin"} (Same-Origin)`}
            </span>
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground font-mono">Target Type:</span>
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium bg-primary/10 text-primary">
              {targetInfo.type === "local-default" && <Laptop className="h-3 w-3" />}
              {targetInfo.type === "remote-custom" && <Globe className="h-3 w-3" />}
              {targetInfo.type === "same-origin" && <Activity className="h-3 w-3" />}
              {targetInfo.type}
            </span>
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground font-mono">Build Context:</span>
            <span className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
              {targetInfo.buildType}
            </span>
          </div>

          {/* Probe Status */}
          <div className="pt-2 border-t border-border/60 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              {probing ? (
                <>
                  <Spinner className="h-3.5 w-3.5 text-primary" />
                  <span className="text-muted-foreground">Testing endpoint…</span>
                </>
              ) : probeResult?.ok ? (
                <>
                  <CheckCircle2 className="h-4 w-4 text-success" />
                  <span className="text-success font-medium">Connected</span>
                  {probeResult.latencyMs !== undefined && (
                    <span className="text-[11px] text-muted-foreground font-mono">
                      ({probeResult.latencyMs}ms)
                    </span>
                  )}
                </>
              ) : (
                <>
                  <XCircle className="h-4 w-4 text-destructive" />
                  <span className="text-destructive font-medium">
                    {probeResult?.error || "Offline / Unreachable"}
                  </span>
                </>
              )}
            </div>

            <Button
              outlined
              className="h-7 text-xs gap-1.5 px-2.5"
              onClick={() => void runProbe(customUrl)}
              disabled={probing}
            >
              <RefreshCw className={cn("h-3 w-3", probing && "animate-spin")} />
              Probe
            </Button>
          </div>
        </div>

        {/* Presets */}
        <div className="space-y-2 mb-4">
          <label className="text-xs font-medium text-muted-foreground">Quick Presets</label>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => {
                setCustomUrl("http://127.0.0.1:9119");
                void runProbe("http://127.0.0.1:9119");
              }}
              className={cn(
                "flex items-center gap-2 p-2.5 rounded-lg border text-left text-xs transition-colors",
                customUrl === "http://127.0.0.1:9119"
                  ? "border-primary bg-primary/5 text-foreground"
                  : "border-border hover:bg-muted/50 text-muted-foreground",
              )}
            >
              <Laptop className="h-4 w-4 text-primary shrink-0" />
              <div>
                <div className="font-medium text-foreground">Local Default</div>
                <div className="text-[10px] text-muted-foreground">127.0.0.1:9119</div>
              </div>
            </button>

            <button
              type="button"
              onClick={() => {
                setCustomUrl("http://localhost:9119");
                void runProbe("http://localhost:9119");
              }}
              className={cn(
                "flex items-center gap-2 p-2.5 rounded-lg border text-left text-xs transition-colors",
                customUrl === "http://localhost:9119"
                  ? "border-primary bg-primary/5 text-foreground"
                  : "border-border hover:bg-muted/50 text-muted-foreground",
              )}
            >
              <Radio className="h-4 w-4 text-primary shrink-0" />
              <div>
                <div className="font-medium text-foreground">Localhost</div>
                <div className="text-[10px] text-muted-foreground">localhost:9119</div>
              </div>
            </button>
          </div>
        </div>

        {/* Custom Input */}
        <div className="space-y-2 mb-6">
          <label htmlFor="backend-url" className="text-xs font-medium text-muted-foreground">
            Custom Host / IP & Port
          </label>
          <div className="flex gap-2">
            <Input
              id="backend-url"
              value={customUrl}
              onChange={(e) => setCustomUrl(e.target.value)}
              placeholder="e.g. http://192.168.1.50:9119 or https://hermes.domain.com"
              className="h-9 text-xs font-mono"
            />
          </div>
          <p className="text-[11px] text-muted-foreground">
            Connects web UI to remote or local Hermes Agent server. Supports HTTP/HTTPS and WS/WSS.
          </p>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between gap-3 pt-3 border-t border-border">
          <Button outlined onClick={handleReset} className="text-xs px-3">
            Reset to Default
          </Button>

          <div className="flex items-center gap-2">
            <Button outlined onClick={onClose} className="text-xs px-3">
              Cancel
            </Button>
            <Button
              onClick={() => handleApply(customUrl)}
              className="text-xs gap-1.5 px-3"
            >
              Apply & Switch
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
