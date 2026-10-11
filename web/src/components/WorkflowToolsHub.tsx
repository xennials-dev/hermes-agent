import { useState, useMemo, memo, type ComponentType } from "react";
import {
  Search,
  Workflow,
  CheckCircle2,
  FolderGit2,
  ArrowUpRight,
} from "lucide-react";
import { Card, CardContent } from "@nous-research/ui/ui/components/card";
import { Badge } from "@nous-research/ui/ui/components/badge";
import { Typography } from "@nous-research/ui/ui/components/typography/index";
import { cn } from "@/lib/utils";

export interface WorkflowTool {
  id: string;
  name: string;
  repo: string;
  githubUrl: string;
  category: "personal" | "swarms" | "cowork" | "edge";
  categoryLabel: string;
  tagline: string;
  description: string;
  localPath: string;
  runtime: "Node/TypeScript" | "Python" | "Electron/Rust";
  brandColor: string;
  logo: ComponentType<{ className?: string }>;
  _searchIndex: string;
}

// Custom brand logos for the workflow tools
export function OpenClawLogo({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="24" height="24" rx="6" fill="#DC2626" />
      <path d="M7 14C6 11 8 8 12 8C16 8 18 11 17 14M9 13C9 15 10 17 12 17C14 17 15 15 15 13" stroke="#FFFFFF" strokeWidth="1.75" strokeLinecap="round" />
      <circle cx="10" cy="11" r="1" fill="#FFFFFF" />
      <circle cx="14" cy="11" r="1" fill="#FFFFFF" />
    </svg>
  );
}

export function HermesLogo({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="24" height="24" rx="6" fill="#0F172A" />
      <path d="M12 4L18 8V16L12 20L6 16V8L12 4Z" stroke="#38BDF8" strokeWidth="1.5" />
      <circle cx="12" cy="12" r="3" fill="#38BDF8" />
    </svg>
  );
}

export function NanoClawLogo({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="24" height="24" rx="6" fill="#047857" />
      <path d="M8 7H16M8 12H16M8 17H12" stroke="#6EE7B7" strokeWidth="2" strokeLinecap="round" />
      <circle cx="15.5" cy="16.5" r="2.5" fill="#34D399" />
    </svg>
  );
}

export function EigentLogo({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="24" height="24" rx="6" fill="#4F46E5" />
      <path d="M7 8L12 5L17 8V16L12 19L7 16V8Z" fill="#818CF8" fillOpacity="0.4" stroke="#C7D2FE" strokeWidth="1.5" />
      <circle cx="12" cy="12" r="2" fill="#FFFFFF" />
    </svg>
  );
}

export function ClawSwarmLogo({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="24" height="24" rx="6" fill="#B91C1C" />
      <circle cx="8" cy="9" r="2" fill="#FCA5A5" />
      <circle cx="16" cy="9" r="2" fill="#FCA5A5" />
      <circle cx="12" cy="16" r="2.5" fill="#FEE2E2" />
      <path d="M8 9L12 16M16 9L12 16" stroke="#FFFFFF" strokeWidth="1.5" />
    </svg>
  );
}

export function SunaLogo({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="24" height="24" rx="6" fill="#18181B" />
      <path d="M6 12C6 8.686 8.686 6 12 6C15.314 6 18 8.686 18 12C18 15.314 15.314 18 12 18" stroke="#F43F5E" strokeWidth="2" strokeLinecap="round" />
      <circle cx="12" cy="12" r="2" fill="#FDA4AF" />
    </svg>
  );
}

export function OpenMausBotLogo({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="24" height="24" rx="6" fill="#2563EB" />
      <rect x="6" y="8" width="12" height="9" rx="3" fill="#60A5FA" />
      <circle cx="9.5" cy="12" r="1.5" fill="#FFFFFF" />
      <circle cx="14.5" cy="12" r="1.5" fill="#FFFFFF" />
      <path d="M12 5V8" stroke="#93C5FD" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export function OpenWorkLogo({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="24" height="24" rx="6" fill="#0284C7" />
      <path d="M6 9H18M6 14H18M10 6V18" stroke="#E0F2FE" strokeWidth="1.75" strokeLinecap="round" />
    </svg>
  );
}

export function ClaweLogo({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="24" height="24" rx="6" fill="#7C3AED" />
      <rect x="6" y="7" width="5" height="10" rx="1.5" fill="#C4B5FD" />
      <rect x="13" y="7" width="5" height="6" rx="1.5" fill="#DDD6FE" />
      <rect x="13" y="15" width="5" height="2" rx="1" fill="#DDD6FE" />
    </svg>
  );
}

export function CoWorkLogo({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="24" height="24" rx="6" fill="#D97706" />
      <circle cx="8" cy="10" r="2.5" fill="#FDE68A" />
      <circle cx="16" cy="10" r="2.5" fill="#FDE68A" />
      <path d="M5 18C5 15.5 7 14 10 14M19 18C19 15.5 17 14 14 14" stroke="#FFFBEB" strokeWidth="1.75" strokeLinecap="round" />
    </svg>
  );
}

export const WORKFLOW_TOOLS: WorkflowTool[] = [
  {
    id: "openclaw",
    name: "OpenClaw",
    repo: "openclaw/openclaw",
    githubUrl: "https://github.com/openclaw/openclaw",
    category: "personal",
    categoryLabel: "Personal Assistant",
    tagline: "Personal AI Assistant & Controllable Canvas",
    description: "Runs locally on your devices and connects with 20+ chat platforms with speech capabilities and live Canvas control.",
    localPath: "cloned_repos/openclaw",
    runtime: "Node/TypeScript",
    brandColor: "#DC2626",
    logo: OpenClawLogo,
    _searchIndex: "openclaw personal assistant canvas chat discord telegram whatsapp pnpm",
  },
  {
    id: "hermes-agent",
    name: "Hermes Agent",
    repo: "NousResearch/hermes-agent",
    githubUrl: "https://github.com/NousResearch/hermes-agent",
    category: "personal",
    categoryLabel: "Core Agent Engine",
    tagline: "Autonomous Self-Improving AI Agent",
    description: "Self-improving AI agent by Nous Research featuring automatic skill generation, prompt caching, and persistent memory.",
    localPath: "hermes-agent (Core Host)",
    runtime: "Python",
    brandColor: "#38BDF8",
    logo: HermesLogo,
    _searchIndex: "hermes agent nous research self-improving skills prompt cache python",
  },
  {
    id: "nanoclaw",
    name: "NanoClaw",
    repo: "Clawland-AI/nanoclaw",
    githubUrl: "https://github.com/Clawland-AI/nanoclaw",
    category: "edge",
    categoryLabel: "Edge & Containers",
    tagline: "Lightweight Edge AI Assistant",
    description: "Containerized mid-weight Python AI agent designed to run efficiently on SBCs, edge devices, and isolated Linux containers.",
    localPath: "cloned_repos/nanoclaw",
    runtime: "Python",
    brandColor: "#047857",
    logo: NanoClawLogo,
    _searchIndex: "nanoclaw edge containers python sbc raspberry pi clawland",
  },
  {
    id: "eigent",
    name: "Eigent",
    repo: "eigent-ai/eigent",
    githubUrl: "https://github.com/eigent-ai/eigent",
    category: "cowork",
    categoryLabel: "Desktop & Cowork",
    tagline: "Custom AI Workforce Desktop Suite",
    description: "Open-source desktop environment designed to build, manage, and coordinate your private multi-agent workforce.",
    localPath: "cloned_repos/eigent",
    runtime: "Electron/Rust",
    brandColor: "#4F46E5",
    logo: EigentLogo,
    _searchIndex: "eigent cowork desktop workforce multi-agent electron",
  },
  {
    id: "clawswarm",
    name: "ClawSwarm",
    repo: "The-Swarm-Corporation/ClawSwarm",
    githubUrl: "https://github.com/The-Swarm-Corporation/ClawSwarm",
    category: "swarms",
    categoryLabel: "Multi-Agent & Swarms",
    tagline: "High-Performance Swarms Multi-Agent Engine",
    description: "Natively multi-agent, Rust-compiled OpenClaw variant built on the Swarms framework for collaborative intelligence.",
    localPath: "cloned_repos/ClawSwarm",
    runtime: "Python",
    brandColor: "#B91C1C",
    logo: ClawSwarmLogo,
    _searchIndex: "clawswarm swarms multi-agent kye gomez rust collaborative",
  },
  {
    id: "suna",
    name: "Kortix Suna",
    repo: "kortix-ai/suna",
    githubUrl: "https://github.com/kortix-ai/suna",
    category: "cowork",
    categoryLabel: "Desktop & Cowork",
    tagline: "All-in-One Autonomous AI Employee",
    description: "Leading open-source AI Operating System for operations, research, strategy, and guided task automation.",
    localPath: "cloned_repos/suna",
    runtime: "Node/TypeScript",
    brandColor: "#F43F5E",
    logo: SunaLogo,
    _searchIndex: "suna kortix ai employee cowork operating system nextjs",
  },
  {
    id: "openmausbot",
    name: "OpenMausBot",
    repo: "andreycurious252/OpenMausBot",
    githubUrl: "https://github.com/andreycurious252/OpenMausBot",
    category: "personal",
    categoryLabel: "Personal Assistant",
    tagline: "Messaging-Interface Agent Workplace",
    description: "Desktop chat application featuring a familiar messenger UI where contacts are active, working AI agents.",
    localPath: "cloned_repos/OpenMausBot",
    runtime: "Electron/Rust",
    brandColor: "#2563EB",
    logo: OpenMausBotLogo,
    _searchIndex: "openmausbot messaging telegram whatsapp agents desktop",
  },
  {
    id: "openwork",
    name: "OpenWork",
    repo: "different-ai/openwork",
    githubUrl: "https://github.com/different-ai/openwork",
    category: "cowork",
    categoryLabel: "Desktop & Cowork",
    tagline: "Universal MCP Agent Control Plane",
    description: "Extensible desktop application and MCP hub connecting local agent workflows, skills, and tools into one shared space.",
    localPath: "cloned_repos/openwork",
    runtime: "Electron/Rust",
    brandColor: "#0284C7",
    logo: OpenWorkLogo,
    _searchIndex: "openwork mcp model context protocol desktop control plane",
  },
  {
    id: "clawe",
    name: "Clawe",
    repo: "getclawe/clawe",
    githubUrl: "https://github.com/getclawe/clawe",
    category: "swarms",
    categoryLabel: "Multi-Agent & Swarms",
    tagline: "Multi-Agent Kanban Coordination System",
    description: "Squad coordination layer powered by OpenClaw featuring Kanban task boards, cron heartbeats, and notifications.",
    localPath: "cloned_repos/clawe",
    runtime: "Node/TypeScript",
    brandColor: "#7C3AED",
    logo: ClaweLogo,
    _searchIndex: "clawe kanban openclaw coordination squad tasks convex",
  },
  {
    id: "cowork-os",
    name: "CoWork-OSS",
    repo: "cowork-os/cowork-os",
    githubUrl: "https://github.com/cowork-os/cowork-os",
    category: "cowork",
    categoryLabel: "Desktop & Cowork",
    tagline: "Local-First Agent Workbench",
    description: "Run complex multi-step workflows in folder-scoped workspaces with fine-grained human-in-the-loop approval controls.",
    localPath: "cloned_repos/cowork-os",
    runtime: "Electron/Rust",
    brandColor: "#D97706",
    logo: CoWorkLogo,
    _searchIndex: "cowork-os local-first folder workbench human approval",
  },
];

export const WorkflowToolsHub = memo(function WorkflowToolsHub() {
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");

  const filteredTools = useMemo(() => {
    return WORKFLOW_TOOLS.filter((tool) => {
      const matchesCategory =
        activeCategory === "all" || tool.category === activeCategory;
      const q = searchQuery.toLowerCase().trim();
      const matchesSearch =
        !q ||
        tool.name.toLowerCase().includes(q) ||
        tool.repo.toLowerCase().includes(q) ||
        tool._searchIndex.includes(q);
      return matchesCategory && matchesSearch;
    });
  }, [activeCategory, searchQuery]);

  return (
    <div className="flex flex-col gap-5 w-full">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-xl border border-current/15 bg-background-surface shadow-sm">
        <div className="flex items-center gap-3.5">
          <div className="p-2.5 rounded-lg bg-primary/10 text-primary">
            <Workflow className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <Typography className="text-lg font-bold text-text-primary">
                Workflow Automation & Agent Workforce
              </Typography>
              <Badge tone="outline" className="text-xs bg-emerald-500/10 text-emerald-400 border-emerald-500/30">
                10 Systems Cloned
              </Badge>
            </div>
            <Typography className="text-xs text-text-secondary mt-0.5">
              Integrated open-source autonomous agent engines, swarms, and cowork workbenches.
            </Typography>
          </div>
        </div>

        {/* Search */}
        <div className="relative min-w-[240px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-text-tertiary" />
          <input
            type="text"
            placeholder="Search agents & workflows..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-background-base border border-current/20 rounded-lg pl-8 pr-3 py-1.5 text-xs text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-primary"
          />
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2">
        {[
          { id: "all", label: "All Repositories (10)" },
          { id: "personal", label: "Personal Assistants" },
          { id: "swarms", label: "Multi-Agent & Swarms" },
          { id: "cowork", label: "Desktop & Cowork" },
          { id: "edge", label: "Edge & Containers" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveCategory(tab.id)}
            className={cn(
              "px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer",
              activeCategory === tab.id
                ? "bg-primary text-primary-foreground shadow-sm"
                : "bg-background-surface hover:bg-background-elevated text-text-secondary border border-current/10"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Grid of Tools */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredTools.map((tool) => {
          const Logo = tool.logo;
          return (
            <Card
              key={tool.id}
              className="group border border-current/15 bg-background-surface hover:border-current/30 hover:shadow-md transition-all flex flex-col justify-between"
            >
              <CardContent className="p-4 flex flex-col gap-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <Logo className="h-8 w-8 shrink-0 rounded-lg" />
                    <div>
                      <Typography className="text-sm font-semibold text-text-primary group-hover:text-primary transition-colors">
                        {tool.name}
                      </Typography>
                      <Typography className="text-[11px] text-text-tertiary font-mono">
                        {tool.repo}
                      </Typography>
                    </div>
                  </div>
                  <Badge tone="outline" className="text-[10px] px-1.5 py-0.5">
                    {tool.categoryLabel}
                  </Badge>
                </div>

                <Typography className="text-xs text-text-secondary line-clamp-2 leading-relaxed">
                  {tool.description}
                </Typography>

                <div className="flex flex-col gap-1.5 pt-2 border-t border-current/10 text-[11px] text-text-tertiary">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <FolderGit2 className="h-3 w-3 text-text-tertiary" />
                      <span className="font-mono text-[10px] truncate max-w-[160px]">
                        {tool.localPath}
                      </span>
                    </span>
                    <Badge tone="secondary" className="text-[10px] font-mono">
                      {tool.runtime}
                    </Badge>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-1">
                  <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
                    <CheckCircle2 className="h-3 w-3" />
                    Installed
                  </span>
                  <a
                    href={tool.githubUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-primary hover:underline font-medium"
                  >
                    GitHub
                    <ArrowUpRight className="h-3 w-3" />
                  </a>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
});
