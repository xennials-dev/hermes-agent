import { useLayoutEffect } from "react";
import { ExternalLink } from "lucide-react";
import { usePageHeader } from "@/contexts/usePageHeader";
import { PluginSlot } from "@/plugins";
import { ChineseAIHub } from "@/components/ChineseAIHub";
import { Button } from "@nous-research/ui/ui/components/button";

export default function EcosystemPage() {
  const { setEnd } = usePageHeader();

  useLayoutEffect(() => {
    setEnd(
      <div className="flex items-center gap-2">
        <a
          href="http://2.25.238.185:3000"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Button outlined size="sm" className="gap-1.5 text-xs">
            <ExternalLink className="h-3.5 w-3.5" />
            Twenty CRM
          </Button>
        </a>
        <a
          href="http://2.25.238.185:5678"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Button outlined size="sm" className="gap-1.5 text-xs">
            <ExternalLink className="h-3.5 w-3.5" />
            n8n Workflows
          </Button>
        </a>
      </div>,
    );
    return () => {
      setEnd(null);
    };
  }, [setEnd]);

  return (
    <div className="flex min-w-0 w-full max-w-full flex-col gap-4 py-2">
      <PluginSlot name="ecosystem:top" />
      <ChineseAIHub />
      <PluginSlot name="ecosystem:bottom" />
    </div>
  );
}
