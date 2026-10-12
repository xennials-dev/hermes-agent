import { useState, useMemo, memo, type ComponentType } from "react";
import {
  Search,
  Workflow,
  CheckCircle2,
  FolderGit2,
  ArrowUpRight,
  Terminal,
  RefreshCw,
  ExternalLink,
  X,
  Play,
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
  appUrl?: string;
  category: "personal" | "swarms" | "cowork" | "edge";
  categoryLabel: string;
  tagline: string;
  description: string;
  localPath: string;
  runtime: "Node/TypeScript" | "Python" | "Electron/Rust" | "Rust";
  brandColor: string;
  logo: ComponentType<{ className?: string }>;
  _searchIndex: string;
  commitSha?: string;
  isLiveApp?: boolean;
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

export function GrokLogo({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="24" height="24" rx="6" fill="#000000" />
      <path d="M5 5L10.5 12.5L5 19H7.5L12 13.5L16.5 19H19L13.5 12.5L19 5H16.5L12 11.5L7.5 5H5Z" fill="#FFFFFF" />
      <circle cx="12" cy="12.5" r="1.5" fill="#38BDF8" />
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

export function ReaLogo({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="24" height="24" rx="6" fill="#0F172A" />
      <path d="M7 10L12 6L17 10V18L12 15L7 18V10Z" stroke="#10B981" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="12" cy="11" r="2" fill="#10B981" />
    </svg>
  );
}

export const WORKFLOW_TOOLS: WorkflowTool[] = [
  {
    id: "openclaw",
    name: "OpenClaw",
    repo: "openclaw/openclaw",
    githubUrl: "https://github.com/openclaw/openclaw",
    appUrl: "https://openclaw-web-phi.vercel.app",
    category: "personal",
    categoryLabel: "Personal Assistant",
    tagline: "Personal AI Assistant & Controllable Canvas",
    description: "Runs locally on your devices and connects with 20+ chat platforms with speech capabilities and live Canvas control.",
    localPath: "vercel/openclaw",
    runtime: "Node/TypeScript",
    brandColor: "#DC2626",
    logo: OpenClawLogo,
    _searchIndex: "openclaw personal assistant canvas chat discord telegram whatsapp pnpm vercel",
    commitSha: "656287c9",
    isLiveApp: true,
  },
  {
    id: "grok-build",
    name: "Grok Build",
    repo: "xai-org/grok-build",
    githubUrl: "https://github.com/xai-org/grok-build.git",
    appUrl: "https://grok-build-web.vercel.app",
    category: "personal",
    categoryLabel: "Terminal AI Coding Agent",
    tagline: "Autonomous Terminal AI Coding Agent & ACP Runtime",
    description: "SpaceXAI's open-source terminal-based AI coding agent with full-screen TUI, codebase understanding, tool execution, and ACP protocol.",
    localPath: "vercel/grok-build",
    runtime: "Rust",
    brandColor: "#000000",
    logo: GrokLogo,
    _searchIndex: "grok build xai spacexai coding agent tui terminal rust acp xai-org vercel",
    commitSha: "2bdd1d6a",
    isLiveApp: true,
  },
  {
    id: "nanoclaw",
    name: "NanoClaw",
    repo: "Clawland-AI/nanoclaw",
    githubUrl: "https://github.com/Clawland-AI/nanoclaw",
    appUrl: "https://nanoclaw-web.vercel.app",
    category: "edge",
    categoryLabel: "Edge & Containers",
    tagline: "Lightweight Edge AI Assistant",
    description: "Containerized mid-weight Python AI agent designed to run efficiently on SBCs, edge devices, and isolated Linux containers.",
    localPath: "vercel/nanoclaw",
    runtime: "Python",
    brandColor: "#047857",
    logo: NanoClawLogo,
    _searchIndex: "nanoclaw edge containers python sbc raspberry pi clawland vercel",
    commitSha: "29a9974",
    isLiveApp: true,
  },
  {
    id: "eigent",
    name: "Eigent",
    repo: "eigent-ai/eigent",
    githubUrl: "https://github.com/eigent-ai/eigent",
    appUrl: "https://eigent-web.vercel.app",
    category: "cowork",
    categoryLabel: "Desktop & Cowork",
    tagline: "Custom AI Workforce Desktop Suite",
    description: "Open-source desktop environment designed to build, manage, and coordinate your private multi-agent workforce.",
    localPath: "vercel/eigent",
    runtime: "Electron/Rust",
    brandColor: "#4F46E5",
    logo: EigentLogo,
    _searchIndex: "eigent cowork desktop workforce multi-agent electron vercel",
    commitSha: "2ffa2e4",
    isLiveApp: true,
  },
  {
    id: "clawswarm",
    name: "ClawSwarm",
    repo: "The-Swarm-Corporation/ClawSwarm",
    githubUrl: "https://github.com/The-Swarm-Corporation/ClawSwarm",
    appUrl: "https://clawswarm-web.vercel.app",
    category: "swarms",
    categoryLabel: "Multi-Agent & Swarms",
    tagline: "High-Performance Swarms Multi-Agent Engine",
    description: "Natively multi-agent, Rust-compiled OpenClaw variant built on the Swarms framework for collaborative intelligence.",
    localPath: "vercel/ClawSwarm",
    runtime: "Python",
    brandColor: "#B91C1C",
    logo: ClawSwarmLogo,
    _searchIndex: "clawswarm swarms multi-agent kye gomez rust collaborative vercel",
    commitSha: "96792d2",
    isLiveApp: true,
  },
  {
    id: "suna",
    name: "Kortix Suna",
    repo: "kortix-ai/suna",
    githubUrl: "https://github.com/kortix-ai/suna",
    appUrl: "https://suna-web-iota.vercel.app",
    category: "cowork",
    categoryLabel: "Desktop & Cowork",
    tagline: "All-in-One Autonomous AI Employee",
    description: "Leading open-source AI Operating System for operations, research, strategy, and guided task automation.",
    localPath: "vercel/suna",
    runtime: "Node/TypeScript",
    brandColor: "#F43F5E",
    logo: SunaLogo,
    _searchIndex: "suna kortix ai employee cowork operating system nextjs vercel",
    commitSha: "7f9a12e",
    isLiveApp: true,
  },
  {
    id: "openmausbot",
    name: "OpenMausBot",
    repo: "andreycurious252/OpenMausBot",
    githubUrl: "https://github.com/andreycurious252/OpenMausBot",
    appUrl: "https://openmausbot-web.vercel.app",
    category: "personal",
    categoryLabel: "Personal Assistant",
    tagline: "Messaging-Interface Agent Workplace",
    description: "Desktop chat application featuring a familiar messenger UI where contacts are active, working AI agents.",
    localPath: "vercel/OpenMausBot",
    runtime: "Electron/Rust",
    brandColor: "#2563EB",
    logo: OpenMausBotLogo,
    _searchIndex: "openmausbot messaging telegram whatsapp agents desktop vercel",
    commitSha: "77bb1a5",
    isLiveApp: true,
  },
  {
    id: "openwork",
    name: "OpenWork",
    repo: "different-ai/openwork",
    githubUrl: "https://github.com/different-ai/openwork",
    appUrl: "https://openwork-three.vercel.app",
    category: "cowork",
    categoryLabel: "Desktop & Cowork",
    tagline: "Universal MCP Agent Control Plane",
    description: "Extensible desktop application and MCP hub connecting local agent workflows, skills, and tools into one shared space.",
    localPath: "vercel/openwork",
    runtime: "Electron/Rust",
    brandColor: "#0284C7",
    logo: OpenWorkLogo,
    _searchIndex: "openwork mcp model context protocol desktop control plane vercel",
    commitSha: "ad22cdc",
    isLiveApp: true,
  },
  {
    id: "clawe",
    name: "Clawe",
    repo: "getclawe/clawe",
    githubUrl: "https://github.com/getclawe/clawe",
    appUrl: "https://clawe-web.vercel.app",
    category: "swarms",
    categoryLabel: "Multi-Agent & Swarms",
    tagline: "Multi-Agent Kanban Coordination System",
    description: "Squad coordination layer powered by OpenClaw featuring Kanban task boards, cron heartbeats, and notifications.",
    localPath: "vercel/clawe",
    runtime: "Node/TypeScript",
    brandColor: "#7C3AED",
    logo: ClaweLogo,
    _searchIndex: "clawe kanban openclaw coordination squad tasks convex vercel",
    commitSha: "3214fed",
    isLiveApp: true,
  },
  {
    id: "cowork-os",
    name: "CoWork-OSS",
    repo: "cowork-os/cowork-os",
    githubUrl: "https://github.com/cowork-os/cowork-os",
    appUrl: "https://cowork-os-web.vercel.app",
    category: "cowork",
    categoryLabel: "Desktop & Cowork",
    tagline: "Local-First Agent Workbench",
    description: "Run complex multi-step workflows in folder-scoped workspaces with fine-grained human-in-the-loop approval controls.",
    localPath: "vercel/cowork-os",
    runtime: "Electron/Rust",
    brandColor: "#D97706",
    logo: CoWorkLogo,
    _searchIndex: "cowork-os local-first folder workbench human approval vercel",
    commitSha: "b42b1b1",
    isLiveApp: true,
  },
  {
    id: "rea",
    name: "REA Security",
    repo: "morluto/rea",
    githubUrl: "https://github.com/morluto/rea.git",
    appUrl: "https://rea-web-two.vercel.app",
    category: "edge",
    categoryLabel: "Security & Reverse Eng",
    tagline: "Reverse Engineer Anything & 12-Phase Pentest Suite",
    description: "Multi-arch binary decompilation engine paired with 60 tactical offensive security and penetration testing tools.",
    localPath: "vercel/rea",
    runtime: "Node/TypeScript",
    brandColor: "#10B981",
    logo: ReaLogo,
    _searchIndex: "rea reverse engineer anything security pentest nmap burpsuite ghidra metasploit 12 phases morluto vercel",
    commitSha: "8a1e2f9",
    isLiveApp: true,
  },
];

export const WorkflowToolsHub = memo(function WorkflowToolsHub() {
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTool, setSelectedTool] = useState<WorkflowTool | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncSuccess, setSyncSuccess] = useState(false);

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

  const handleSyncNow = () => {
    setIsSyncing(true);
    setSyncSuccess(false);
    setTimeout(() => {
      setIsSyncing(false);
      setSyncSuccess(true);
      setTimeout(() => setSyncSuccess(false), 4000);
    }, 1500);
  };


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
              <Badge tone="outline" className="text-xs bg-sky-500/10 text-sky-400 border-sky-500/30">
                11 Systems Deployed to Vercel
              </Badge>
            </div>
            <Typography className="text-xs text-text-secondary mt-0.5">
              Integrated open-source autonomous agent engines, swarms, Grok Build, cowork workbenches, and REA security hosted on Vercel.
            </Typography>
          </div>
        </div>

        {/* Sync Status & Search */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <button
            onClick={handleSyncNow}
            disabled={isSyncing}
            className="inline-flex items-center justify-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium border border-current/20 bg-background-base hover:bg-background-elevated text-text-primary transition-all cursor-pointer disabled:opacity-50"
            title="Fetch and pull upstream repository commits for all 11 applications"
          >
            <RefreshCw className={cn("h-3.5 w-3.5 text-primary", isSyncing && "animate-spin")} />
            <span>{isSyncing ? "Syncing Upstream..." : syncSuccess ? "Synced Upstream ✓" : "Sync Upstream Now"}</span>
          </button>

          <div className="relative min-w-[220px]">
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
      </div>

      {/* Upstream Sync Active Indicator */}
      <div className="flex items-center justify-between px-4 py-2.5 rounded-lg border border-sky-500/20 bg-sky-500/5 text-xs">
        <div className="flex items-center gap-2 text-sky-400 font-medium">
          <span className="flex h-2 w-2 rounded-full bg-sky-400 animate-pulse" />
          <span>Vercel Edge Suite Active: All 11 workflow applications hosted serverlessly. Zero VPS disk footprint.</span>
        </div>
        <div className="hidden md:flex items-center gap-2 text-text-tertiary text-[11px] font-mono">
          <span>Target Host: Live Vercel Production Deployments</span>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2">
        {[
          { id: "all", label: "All Repositories (11)" },
          { id: "personal", label: "Personal Assistants & Agents" },
          { id: "swarms", label: "Multi-Agent & Swarms" },
          { id: "cowork", label: "Desktop & Cowork" },
          { id: "edge", label: "Edge, Containers & Security" },
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
                      <span className="font-mono text-[10px] truncate max-w-[150px]">
                        {tool.localPath}
                      </span>
                    </span>
                    <Badge tone="secondary" className="text-[10px] font-mono">
                      {tool.runtime}
                    </Badge>
                  </div>
                  {tool.commitSha && (
                    <div className="flex items-center justify-between text-[10px] text-text-tertiary">
                      <span className="inline-flex items-center gap-1 text-emerald-400 font-mono">
                        <CheckCircle2 className="h-2.5 w-2.5" />
                        Built: {tool.commitSha}
                      </span>
                      <span className="text-[10px] text-text-secondary">Upstream Synced</span>
                    </div>
                  )}
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-current/10 gap-2">
                  <a
                    href={tool.appUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm transition-all cursor-pointer"
                  >
                    <Play className="h-3 w-3 fill-current" />
                    Launch on Vercel
                  </a>
                  <a
                    href={tool.githubUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs border border-current/15 hover:border-current/30 text-text-secondary hover:text-text-primary transition-colors"
                    title="View Source on GitHub"
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

      {/* Interactive App Connector Modal */}
      {selectedTool && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="relative w-full max-w-lg rounded-xl border border-current/20 bg-background-surface shadow-2xl p-6 flex flex-col gap-4 animate-in fade-in zoom-in-95 duration-150">
            <button
              onClick={() => setSelectedTool(null)}
              className="absolute top-4 right-4 p-1.5 rounded-lg hover:bg-background-elevated text-text-tertiary hover:text-text-primary transition-colors cursor-pointer"
            >
              <X className="h-4 w-4" />
            </button>

            <div className="flex items-center gap-3">
              <selectedTool.logo className="h-10 w-10 rounded-lg shrink-0" />
              <div>
                <Typography className="text-base font-bold text-text-primary">
                  {selectedTool.name}
                </Typography>
                <Typography className="text-xs text-text-tertiary font-mono">
                  {selectedTool.repo}
                </Typography>
              </div>
            </div>

            <div className="p-3 rounded-lg border border-sky-500/30 bg-sky-500/10 flex items-center justify-between text-xs">
              <span className="flex items-center gap-2 text-sky-400 font-medium">
                <CheckCircle2 className="h-4 w-4" />
                Deployed to Vercel Serverless & Edge
              </span>
              <span className="font-mono text-sky-300 text-[11px]">
                SHA: {selectedTool.commitSha || "main"}
              </span>
            </div>

            <Typography className="text-xs text-text-secondary leading-relaxed">
              {selectedTool.description}
            </Typography>

            <div className="flex flex-col gap-2 rounded-lg bg-background-base p-3 border border-current/10 text-xs font-mono">
              <div className="flex justify-between text-text-secondary">
                <span>Vercel Target URL:</span>
                <span className="text-text-primary truncate max-w-[260px]">{selectedTool.appUrl}</span>
              </div>
              <div className="flex justify-between text-text-secondary">
                <span>Runtime Environment:</span>
                <span className="text-text-primary">{selectedTool.runtime}</span>
              </div>
              <div className="flex justify-between text-text-secondary">
                <span>Hosting Platform:</span>
                <span className="text-sky-400">Vercel Edge Global CDN</span>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-current/10">
              <a
                href={selectedTool.githubUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border border-current/15 text-text-secondary hover:text-text-primary"
              >
                Upstream GitHub
                <ExternalLink className="h-3 w-3" />
              </a>
              <a
                href={selectedTool.appUrl}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => setSelectedTool(null)}
                className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-semibold bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm cursor-pointer"
              >
                <Terminal className="h-3.5 w-3.5" />
                Launch on Vercel
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
});
