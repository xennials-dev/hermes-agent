import { WorkflowToolsHub } from "@/components/WorkflowToolsHub";
import { PluginSlot } from "@/plugins";

export default function WorkflowsPage() {
  return (
    <div className="flex min-w-0 w-full max-w-full flex-col gap-4 py-2">
      <PluginSlot name="workflows:top" />
      <WorkflowToolsHub />
      <PluginSlot name="workflows:bottom" />
    </div>
  );
}
