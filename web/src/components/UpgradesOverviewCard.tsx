import { useState } from "react";
import { Link } from "react-router";
import {
  ExternalLink,
  Sparkles,
  Cpu,
  Server,
  ArrowUpRight,
  Globe,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { Card } from "@nous-research/ui/ui/components/card";
import { Badge } from "@nous-research/ui/ui/components/badge";
import { Button } from "@nous-research/ui/ui/components/button";
import { Typography } from "@nous-research/ui/ui/components/typography/index";
import { cn } from "@/lib/utils";
import { TwentyLogo, N8nLogo } from "@/components/ChineseAIHub";

interface UpgradeItem {
  id: string;
  title: string;
  category: string;
  description: string;
  badges: string[];
  primaryLink: {
    label: string;
    url: string;
    isInternal?: boolean;
  };
  secondaryLinks?: {
    label: string;
    url: string;
    isInternal?: boolean;
  }[];
  logo: React.ReactNode;
  accentBorder: string;
}

const UPGRADES: UpgradeItem[] = [
  {
    id: "twenty-crm",
    title: "Twenty CRM Suite",
    category: "Customer & Agent Memory",
    description:
      "Self-hosted CRM with autonomous loop orchestration, PostgreSQL schema, SCIM 2.0 provisioning, and Composio tool fabric.",
    badges: ["Port 3000", "Live Cloud", "PostgreSQL", "SCIM 2.0"],
    primaryLink: {
      label: "Open Live Twenty CRM",
      url: "https://techstarz101.com:3000",
    },
    secondaryLinks: [
      {
        label: "Twenty Docs",
        url: "https://docs.twenty.com",
      },
      {
        label: "GraphQL API",
        url: "https://techstarz101.com:3000/graphql",
      },
    ],
    logo: <TwentyLogo className="h-6 w-6" />,
    accentBorder: "border-blue-500/30 hover:border-blue-500/60",
  },
  {
    id: "n8n-workflows",
    title: "n8n Workflow Engine",
    category: "Automation Orchestration",
    description:
      "Autonomous lifecycle pipelines syncing incoming filesystem drops and CRM customer engagement lifecycle events.",
    badges: ["Port 5678", "File Watcher", "Lifecycle Router"],
    primaryLink: {
      label: "Open n8n Workflows",
      url: "https://techstarz101.com:5678",
    },
    secondaryLinks: [
      {
        label: "n8n Docs",
        url: "https://docs.n8n.io",
      },
    ],
    logo: <N8nLogo className="h-6 w-6" />,
    accentBorder: "border-rose-500/30 hover:border-rose-500/60",
  },
  {
    id: "chinese-ai-hub",
    title: "Chinese AI Frontier Hub",
    category: "18+ Frontier Labs & Models",
    description:
      "Interactive directory & playgrounds for DeepSeek, Qwen, Moonshot Kimi, Zhipu GLM, MiniMax, StepFun, Yi, Baichuan, and more with CRM sync.",
    badges: ["18 Labs", "Interactive Hub", "CRM Mapped", "DeepSeek", "Qwen"],
    primaryLink: {
      label: "Explore AI Ecosystem Hub",
      url: "/ecosystem",
      isInternal: true,
    },
    secondaryLinks: [
      {
        label: "DeepSeek",
        url: "https://chat.deepseek.com",
      },
      {
        label: "Qwen",
        url: "https://tongyi.aliyun.com",
      },
      {
        label: "Kimi",
        url: "https://kimi.moonshot.cn",
      },
      {
        label: "GLM-4",
        url: "https://chatglm.cn",
      },
    ],
    logo: <Sparkles className="h-6 w-6 text-amber-400" />,
    accentBorder: "border-amber-500/30 hover:border-amber-500/60",
  },
  {
    id: "nvidia-blueprints",
    title: "Enterprise NVIDIA AI Blueprints",
    category: "Enterprise Infrastructure",
    description:
      "Production multi-agent blueprints with NeMo Retriever, NIM container microservices, and TensorRT-LLM inference optimization.",
    badges: ["NeMo Retriever", "NIM Microservices", "TensorRT-LLM"],
    primaryLink: {
      label: "NVIDIA Developer Blueprints",
      url: "https://build.nvidia.com",
    },
    secondaryLinks: [
      {
        label: "View Skills in Hermes",
        url: "/skills",
        isInternal: true,
      },
    ],
    logo: <Cpu className="h-6 w-6 text-emerald-400" />,
    accentBorder: "border-emerald-500/30 hover:border-emerald-500/60",
  },
  {
    id: "minimax-deployment",
    title: "MiniMax Sovereign Deployment",
    category: "Multi-Agent Reasoning",
    description:
      "Production containerized deployment stacks supporting MiniMax ABAB 6.5 / Hailuo model services and sovereign agent workflows.",
    badges: ["Docker Compose", "Hailuo AI", "Sovereign Agent"],
    primaryLink: {
      label: "MiniMax Hailuo Interface",
      url: "https://hailuoai.com",
    },
    secondaryLinks: [
      {
        label: "MiniMax Open Platform",
        url: "https://api.minimax.chat",
      },
    ],
    logo: <Server className="h-6 w-6 text-purple-400" />,
    accentBorder: "border-purple-500/30 hover:border-purple-500/60",
  },
  {
    id: "sovereign-mesh",
    title: "Xennials Sovereign Mesh & Repos",
    category: "Decentralized Architecture",
    description:
      "Core distributed agent architecture, CRM design specifications, sovereign mesh orchestration, and founder dossier.",
    badges: ["xennials-dev", "Mesh Mesh", "Founder Dossier"],
    primaryLink: {
      label: "Xennials Sovereign Mesh Repo",
      url: "https://github.com/xennials-dev/xennials-dev",
    },
    secondaryLinks: [
      {
        label: "Hermes Agent Repo",
        url: "https://github.com/xennials-dev/hermes-agent",
      },
      {
        label: "Documentation",
        url: "/docs",
        isInternal: true,
      },
    ],
    logo: <Globe className="h-6 w-6 text-sky-400" />,
    accentBorder: "border-sky-500/30 hover:border-sky-500/60",
  },
];

export function UpgradesOverviewCard() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="relative overflow-hidden rounded-xl border border-border bg-gradient-to-b from-background-base/90 via-background-base/60 to-background-base/30 p-4 shadow-sm backdrop-blur-sm sm:p-5">
      {/* Header Bar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-primary/30 bg-primary/10 shadow-inner">
            <Sparkles className="h-5 w-5 text-primary animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <Typography className="text-base font-bold tracking-tight text-text-primary">
                Workspace Upgrades & Ecosystem Links
              </Typography>
              <Badge tone="success" className="text-[10px] px-1.5 py-0 uppercase">
                Active
              </Badge>
            </div>
            <p className="text-xs text-text-secondary mt-0.5">
              Instant entry points to all upgraded services, deployed tools, automated pipelines, and AI directories.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-end sm:self-auto">
          <Link to="/ecosystem">
            <Button outlined size="sm" className="gap-1.5 text-xs text-primary border-primary/40 hover:bg-primary/10">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Full AI Hub</span>
            </Button>
          </Link>
          <Button
            ghost
            size="sm"
            onClick={() => setCollapsed(!collapsed)}
            className="text-xs text-text-secondary hover:text-text-primary"
            aria-label={collapsed ? "Expand upgrade links" : "Collapse upgrade links"}
          >
            {collapsed ? (
              <span className="flex items-center gap-1">
                Show Links <ChevronDown className="h-3.5 w-3.5" />
              </span>
            ) : (
              <span className="flex items-center gap-1">
                Collapse <ChevronUp className="h-3.5 w-3.5" />
              </span>
            )}
          </Button>
        </div>
      </div>

      {/* Grid of Upgrades */}
      {!collapsed && (
        <div className="mt-4 grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-3">
          {UPGRADES.map((upgrade) => (
            <Card
              key={upgrade.id}
              className={cn(
                "group relative flex flex-col justify-between border bg-background-base/60 p-3.5 transition-all duration-200 hover:shadow-md",
                upgrade.accentBorder,
              )}
            >
              <div>
                {/* Header inside card */}
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2.5">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-current/15 bg-background-base/80 shadow-xs">
                      {upgrade.logo}
                    </div>
                    <div>
                      <Typography className="text-sm font-semibold text-text-primary group-hover:text-midground transition-colors">
                        {upgrade.title}
                      </Typography>
                      <span className="text-[11px] text-text-tertiary">
                        {upgrade.category}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Description */}
                <p className="text-xs text-text-secondary leading-relaxed mb-3 line-clamp-2">
                  {upgrade.description}
                </p>

                {/* Badges */}
                <div className="flex flex-wrap gap-1 mb-3">
                  {upgrade.badges.map((b) => (
                    <Badge
                      key={b}
                      tone="outline"
                      className="text-[10px] px-1.5 py-0 font-mono-ui bg-background-base/40"
                    >
                      {b}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="border-t border-current/10 pt-2.5 mt-auto flex flex-col gap-1.5">
                {upgrade.primaryLink.isInternal ? (
                  <Link
                    to={upgrade.primaryLink.url}
                    className="flex items-center justify-between rounded-md bg-primary/10 px-2.5 py-1.5 text-xs font-medium text-primary hover:bg-primary/20 transition-colors"
                  >
                    <span>{upgrade.primaryLink.label}</span>
                    <ArrowUpRight className="h-3.5 w-3.5" />
                  </Link>
                ) : (
                  <a
                    href={upgrade.primaryLink.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-between rounded-md bg-primary/10 px-2.5 py-1.5 text-xs font-medium text-primary hover:bg-primary/20 transition-colors"
                  >
                    <span>{upgrade.primaryLink.label}</span>
                    <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                )}

                {/* Secondary Links if any */}
                {upgrade.secondaryLinks && upgrade.secondaryLinks.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-0.5">
                    {upgrade.secondaryLinks.map((sec) =>
                      sec.isInternal ? (
                        <Link
                          key={sec.label}
                          to={sec.url}
                          className="text-[11px] text-text-tertiary hover:text-text-primary hover:underline flex items-center gap-0.5"
                        >
                          {sec.label}
                        </Link>
                      ) : (
                        <a
                          key={sec.label}
                          href={sec.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[11px] text-text-tertiary hover:text-text-primary hover:underline flex items-center gap-0.5"
                        >
                          {sec.label} <ArrowUpRight className="h-2.5 w-2.5" />
                        </a>
                      ),
                    )}
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
