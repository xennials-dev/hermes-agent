import { useEffect, useState } from "react";
import {
  getBackendTargetInfo,
  probeBackend,
  onBackendTargetChange,
  type BackendProbeResult,
  type BackendTargetInfo,
} from "@/lib/backend-router";
import { BackendRouterModal } from "@/components/BackendRouterModal";
import { Globe, Laptop } from "lucide-react";
import { cn } from "@/lib/utils";

export function BackendStatusBadge({ className }: { className?: string }) {
  const [modalOpen, setModalOpen] = useState(false);
  const [targetInfo, setTargetInfo] = useState<BackendTargetInfo>(getBackendTargetInfo);
  const [probeResult, setProbeResult] = useState<BackendProbeResult | null>(null);

  useEffect(() => {
    const check = async () => {
      const res = await probeBackend();
      setProbeResult(res);
    };

    void check();
    const interval = setInterval(check, 30000); // Check every 30s
    const unsubscribe = onBackendTargetChange((info) => {
      setTargetInfo(info);
      void check();
    });

    return () => {
      clearInterval(interval);
      unsubscribe();
    };
  }, []);

  const isOnline = probeResult?.ok;
  const isLocal = targetInfo.type.startsWith("local");

  return (
    <>
      <button
        type="button"
        onClick={() => setModalOpen(true)}
        title={`Backend: ${targetInfo.url || "Same-Origin"} (${isOnline ? "Connected" : "Offline"} - Click to configure)`}
        className={cn(
          "inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-[11px] font-mono transition-all",
          "border border-border/80 bg-background/80 hover:bg-muted/80 hover:border-primary/50 text-foreground",
          className,
        )}
      >
        <span className="relative flex h-2 w-2">
          {isOnline && (
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75" />
          )}
          <span
            className={cn(
              "relative inline-flex rounded-full h-2 w-2",
              isOnline ? "bg-success" : "bg-destructive",
            )}
          />
        </span>

        {isLocal ? (
          <Laptop className="h-3 w-3 text-muted-foreground" />
        ) : (
          <Globe className="h-3 w-3 text-muted-foreground" />
        )}

        <span className="truncate max-w-[120px]">
          {targetInfo.port ? `:${targetInfo.port}` : targetInfo.host || "Router"}
        </span>

        {probeResult?.latencyMs !== undefined && isOnline && (
          <span className="text-[9px] text-muted-foreground hidden sm:inline">
            {probeResult.latencyMs}ms
          </span>
        )}
      </button>

      <BackendRouterModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </>
  );
}
