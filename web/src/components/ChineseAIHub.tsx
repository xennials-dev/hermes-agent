import { useState, useMemo, memo, type ComponentType } from "react";
import {
  ExternalLink,
  Sparkles,
  Search,
  Bot,
  Layers,
  Video,
  Eye,
  CheckCircle2,
  ArrowUpRight,
  X,
} from "lucide-react";
import { Card, CardContent } from "@nous-research/ui/ui/components/card";
import { Badge } from "@nous-research/ui/ui/components/badge";
import { Button } from "@nous-research/ui/ui/components/button";
import { Typography } from "@nous-research/ui/ui/components/typography/index";
import { cn } from "@/lib/utils";

export interface AIModelOrg {
  id: string;
  name: string;
  category: "llm" | "vlm" | "media" | "tooling";
  categoryLabel: string;
  modelFamily: readonly string[];
  interfaceUrl: string;
  interfaceName: string;
  description: string;
  crmEntityId?: string;
  brandColor: string;
  logo: ComponentType<{ className?: string }>;
  _searchIndex: string;
}

export function TwentyLogo({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="Twenty CRM"
    >
      <rect width="24" height="24" rx="5" fill="#111827" />
      <path
        d="M6 8.5C6 7.4 6.9 6.5 8 6.5H10.5C11.6 6.5 12.5 7.4 12.5 8.5V11C12.5 12.1 11.6 13 10.5 13H8.5V14.5H12.5V16.5H6.5V14C6.5 12.9 7.4 12 8.5 12H10.5V8.5H8V9.5H6V8.5Z"
        fill="#3B82F6"
      />
      <rect x="13.5" y="6.5" width="4.5" height="10" rx="2" fill="#60A5FA" />
    </svg>
  );
}

export function DeepSeekLogo({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="32" height="32" rx="8" fill="#1E40AF" />
      <path
        d="M8 17.5C9.5 14 13.5 11 18 11C23 11 25.5 14.5 25.5 17C25.5 20.5 21.5 23 17 23C13.5 23 10 21 8 17.5Z"
        fill="#60A5FA"
      />
      <circle cx="19.5" cy="14.5" r="1.5" fill="#FFFFFF" />
      <path d="M10 18C12 21 16 23.5 20.5 22" stroke="#FFFFFF" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

export function QwenLogo({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="32" height="32" rx="8" fill="#4F46E5" />
      <path d="M16 6L25 11.5V22.5L16 28L7 22.5V11.5L16 6Z" stroke="#A5B4FC" strokeWidth="2" strokeLinejoin="round" />
      <circle cx="16" cy="17" r="4.5" fill="#FFFFFF" />
      <circle cx="16" cy="17" r="2" fill="#4F46E5" />
    </svg>
  );
}

export function ZhipuLogo({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="32" height="32" rx="8" fill="#2563EB" />
      <path d="M10 9H22L14 17H22L12 25L15 17H10L10 9Z" fill="#93C5FD" />
      <circle cx="21" cy="10" r="1.5" fill="#FFFFFF" />
    </svg>
  );
}

export function YiLogo({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="32" height="32" rx="8" fill="#111827" />
      <text x="7" y="22" fill="#10B981" fontFamily="sans-serif" fontWeight="bold" fontSize="16">
        01
      </text>
      <circle cx="24" cy="12" r="3" fill="#10B981" />
    </svg>
  );
}

export function BaichuanLogo({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="32" height="32" rx="8" fill="#EA580C" />
      <path d="M7 16C11 11 16 11 20 16C24 21 28 20 28 20" stroke="#FED7AA" strokeWidth="2.5" strokeLinecap="round" />
      <path d="M7 21C11 16 16 16 20 21C22 23 25 23 27 22" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export function ShanghaiAILabLogo({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="32" height="32" rx="8" fill="#0284C7" />
      <circle cx="16" cy="16" r="8" stroke="#BAE6FD" strokeWidth="2" />
      <circle cx="16" cy="16" r="3.5" fill="#FFFFFF" />
      <path d="M8 16H24M16 8V24" stroke="#BAE6FD" strokeWidth="1.5" />
    </svg>
  );
}

export function XverseLogo({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="32" height="32" rx="8" fill="#7C3AED" />
      <path d="M9 8L23 24M23 8L9 24" stroke="#DDD6FE" strokeWidth="3" strokeLinecap="round" />
      <circle cx="16" cy="16" r="2.5" fill="#FFFFFF" />
    </svg>
  );
}

export function InspurLogo({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="32" height="32" rx="8" fill="#0369A1" />
      <path d="M7 19C11 13 14 13 18 17C21 20 23 20 26 16" stroke="#E0F2FE" strokeWidth="2.5" strokeLinecap="round" />
      <circle cx="12" cy="10" r="2" fill="#38BDF8" />
      <circle cx="22" cy="10" r="2" fill="#38BDF8" />
    </svg>
  );
}

export function BaaiLogo({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="32" height="32" rx="8" fill="#1D4ED8" />
      <path d="M16 7L24 13V21L16 26L8 21V13L16 7Z" fill="#3B82F6" />
      <path d="M16 11L21 15V19L16 22L11 19V15L16 11Z" fill="#DBEAFE" />
    </svg>
  );
}

export function KunlunLogo({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="32" height="32" rx="8" fill="#D97706" />
      <path d="M8 22L16 9L24 22H8Z" fill="#FDE68A" />
      <path d="M13 22L16 16L19 22H13Z" fill="#D97706" />
    </svg>
  );
}

export function OpenBmbLogo({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="32" height="32" rx="8" fill="#059669" />
      <rect x="9" y="9" width="6" height="6" rx="1.5" fill="#A7F3D0" />
      <rect x="17" y="9" width="6" height="6" rx="1.5" fill="#A7F3D0" />
      <rect x="9" y="17" width="6" height="6" rx="1.5" fill="#A7F3D0" />
      <rect x="17" y="17" width="6" height="6" rx="1.5" fill="#FFFFFF" />
    </svg>
  );
}

export function OpenGvLabLogo({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="32" height="32" rx="8" fill="#4338CA" />
      <path d="M7 16C9.5 11.5 12.5 9 16 9C19.5 9 22.5 11.5 25 16C22.5 20.5 19.5 23 16 23C12.5 23 9.5 20.5 7 16Z" stroke="#C7D2FE" strokeWidth="2" />
      <circle cx="16" cy="16" r="3.5" fill="#FFFFFF" />
    </svg>
  );
}

export function TencentLogo({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="32" height="32" rx="8" fill="#0052D9" />
      <path d="M16 7C11.03 7 7 11.03 7 16C7 20.97 11.03 25 16 25C20.97 25 25 20.97 25 16" stroke="#93C5FD" strokeWidth="2.5" strokeLinecap="round" />
      <circle cx="16" cy="16" r="4" fill="#FFFFFF" />
    </svg>
  );
}

export function StepFunLogo({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="32" height="32" rx="8" fill="#0D9488" />
      <path d="M8 24H13V18H18V12H23V8" stroke="#99F6E4" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="23" cy="8" r="2" fill="#FFFFFF" />
    </svg>
  );
}

export function YueLogo({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className} xmlns="http://www.w3.org/2000/svg">
      <rect width="32" height="32" rx="8" fill="#DB2777" />
      <path d="M9 19V13C9 10 12 8 16 8C20 8 23 10 23 13V19" stroke="#FBCFE8" strokeWidth="2" />
      <circle cx="9" cy="19" r="3" fill="#F472B6" />
      <circle cx="23" cy="19" r="3" fill="#F472B6" />
    </svg>
  );
}

function buildSearchIndex(name: string, description: string, family: readonly string[], iface: string) {
  return `${name} ${description} ${family.join(" ")} ${iface}`.toLowerCase();
}

export const CHINESE_AI_ORGS: readonly AIModelOrg[] = [
  // 1. Foundational LLMs
  {
    id: "deepseek",
    name: "DeepSeek AI",
    category: "llm",
    categoryLabel: "Foundational LLM",
    modelFamily: ["DeepSeek-V3", "DeepSeek-R1", "DeepSeek-Coder"],
    interfaceUrl: "https://chat.deepseek.com",
    interfaceName: "DeepSeek Chat & Reasoner",
    description: "Frontier open-weights reasoning (R1) and general mixture-of-experts (V3) models.",
    crmEntityId: "comp-deepseek",
    brandColor: "#1E40AF",
    logo: DeepSeekLogo,
    _searchIndex: buildSearchIndex("DeepSeek AI", "Frontier open-weights reasoning (R1) and general mixture-of-experts (V3) models.", ["DeepSeek-V3", "DeepSeek-R1", "DeepSeek-Coder"], "DeepSeek Chat & Reasoner"),
  },
  {
    id: "alibaba-qwen",
    name: "Alibaba Cloud / Qwen",
    category: "llm",
    categoryLabel: "Foundational LLM",
    modelFamily: ["Qwen 2.5", "Qwen-Coder", "Qwen-Max"],
    interfaceUrl: "https://chat.qwenlm.ai",
    interfaceName: "Qwen Chat Playground",
    description: "Industry-leading polyglot coding and general LLMs from Alibaba Cloud.",
    crmEntityId: "comp-alibaba-cloud",
    brandColor: "#4F46E5",
    logo: QwenLogo,
    _searchIndex: buildSearchIndex("Alibaba Cloud / Qwen", "Industry-leading polyglot coding and general LLMs from Alibaba Cloud.", ["Qwen 2.5", "Qwen-Coder", "Qwen-Max"], "Qwen Chat Playground"),
  },
  {
    id: "zhipu-glm",
    name: "Zhipu AI & Tsinghua",
    category: "llm",
    categoryLabel: "Foundational LLM",
    modelFamily: ["ChatGLM", "GLM-4", "GLM-Zero-Preview"],
    interfaceUrl: "https://chatglm.cn",
    interfaceName: "Zhipu Qingyan Chat",
    description: "Bilingual Chinese/English powerhouse models developed with Tsinghua KEG lab.",
    crmEntityId: "comp-zhipu-ai",
    brandColor: "#2563EB",
    logo: ZhipuLogo,
    _searchIndex: buildSearchIndex("Zhipu AI & Tsinghua", "Bilingual Chinese/English powerhouse models developed with Tsinghua KEG lab.", ["ChatGLM", "GLM-4", "GLM-Zero-Preview"], "Zhipu Qingyan Chat"),
  },
  {
    id: "01-ai",
    name: "01.AI (Lingyi Wanwu)",
    category: "llm",
    categoryLabel: "Foundational LLM",
    modelFamily: ["Yi-1.5", "Yi-Large", "Yi-Coder"],
    interfaceUrl: "https://yiyan.lingyiwanwu.com",
    interfaceName: "Wanzhi AI Interface",
    description: "Founded by Dr. Kai-Fu Lee; delivers high-throughput architectures.",
    crmEntityId: "comp-01-ai",
    brandColor: "#111827",
    logo: YiLogo,
    _searchIndex: buildSearchIndex("01.AI (Lingyi Wanwu)", "Founded by Dr. Kai-Fu Lee; delivers high-throughput architectures.", ["Yi-1.5", "Yi-Large", "Yi-Coder"], "Wanzhi AI Interface"),
  },
  {
    id: "baichuan",
    name: "Baichuan Intelligent",
    category: "llm",
    categoryLabel: "Foundational LLM",
    modelFamily: ["Baichuan 2", "Baichuan 3", "Baichuan 4"],
    interfaceUrl: "https://www.baichuan-ai.com/chat",
    interfaceName: "Baichuan AI Chat",
    description: "Founded by Sogou founder Xiaochuan Wang, specialized in medical & Chinese knowledge.",
    crmEntityId: "comp-baichuan",
    brandColor: "#EA580C",
    logo: BaichuanLogo,
    _searchIndex: buildSearchIndex("Baichuan Intelligent", "Founded by Sogou founder Xiaochuan Wang, specialized in medical & Chinese knowledge.", ["Baichuan 2", "Baichuan 3", "Baichuan 4"], "Baichuan AI Chat"),
  },
  {
    id: "shanghai-ai-lab",
    name: "Shanghai AI Lab",
    category: "llm",
    categoryLabel: "Foundational LLM",
    modelFamily: ["InternLM 2.5", "InternLM-XComposer"],
    interfaceUrl: "https://internlm.intern-ai.org.cn/",
    interfaceName: "InternLM Web Chat",
    description: "Premier academic lab delivering 1M token context reasoning architectures.",
    crmEntityId: "comp-shanghai-ai-lab",
    brandColor: "#0284C7",
    logo: ShanghaiAILabLogo,
    _searchIndex: buildSearchIndex("Shanghai AI Lab", "Premier academic lab delivering 1M token context reasoning architectures.", ["InternLM 2.5", "InternLM-XComposer"], "InternLM Web Chat"),
  },
  {
    id: "xverse",
    name: "XVERSE Technology",
    category: "llm",
    categoryLabel: "Foundational LLM",
    modelFamily: ["XVERSE-13B", "XVERSE-65B", "XVERSE-MoE"],
    interfaceUrl: "https://chat.xverse.cn",
    interfaceName: "XVERSE Interactive Chat",
    description: "High-performance enterprise foundational models with expansive vocabularies.",
    crmEntityId: "comp-xverse",
    brandColor: "#7C3AED",
    logo: XverseLogo,
    _searchIndex: buildSearchIndex("XVERSE Technology", "High-performance enterprise foundational models with expansive vocabularies.", ["XVERSE-13B", "XVERSE-65B", "XVERSE-MoE"], "XVERSE Interactive Chat"),
  },
  {
    id: "inspur",
    name: "Inspur (IEG)",
    category: "llm",
    categoryLabel: "Foundational LLM",
    modelFamily: ["Yuan 2.0-102B", "Yuan 2.0-M32"],
    interfaceUrl: "https://air.inspur.com/",
    interfaceName: "Inspur AI Lab Platform",
    description: "Industrial-grade open language models with Local Attention Filtering.",
    crmEntityId: "comp-inspur",
    brandColor: "#0369A1",
    logo: InspurLogo,
    _searchIndex: buildSearchIndex("Inspur (IEG)", "Industrial-grade open language models with Local Attention Filtering.", ["Yuan 2.0-102B", "Yuan 2.0-M32"], "Inspur AI Lab Platform"),
  },
  {
    id: "baai-aquila",
    name: "BAAI (Beijing Acad. AI)",
    category: "llm",
    categoryLabel: "Foundational LLM",
    modelFamily: ["Aquila 2", "AquilaChat-34B", "WuDao"],
    interfaceUrl: "https://aquila.baai.ac.cn/",
    interfaceName: "Aquila Model Playground",
    description: "National AI institute fostering compliant, open open-source foundational research.",
    crmEntityId: "comp-baai",
    brandColor: "#1D4ED8",
    logo: BaaiLogo,
    _searchIndex: buildSearchIndex("BAAI (Beijing Acad. AI)", "National AI institute fostering compliant, open open-source foundational research.", ["Aquila 2", "AquilaChat-34B", "WuDao"], "Aquila Model Playground"),
  },
  {
    id: "kunlun-skywork",
    name: "Kunlun Tech",
    category: "llm",
    categoryLabel: "Foundational LLM",
    modelFamily: ["Skywork", "Skywork-MoE", "Tiangong 3.0"],
    interfaceUrl: "https://www.tiangong.cn",
    interfaceName: "Tiangong AI Chat",
    description: "Sparse Mixture-of-Experts models powering large-scale consumer applications.",
    crmEntityId: "comp-kunlun-tech",
    brandColor: "#D97706",
    logo: KunlunLogo,
    _searchIndex: buildSearchIndex("Kunlun Tech", "Sparse Mixture-of-Experts models powering large-scale consumer applications.", ["Skywork", "Skywork-MoE", "Tiangong 3.0"], "Tiangong AI Chat"),
  },

  // 2. Multimodal & Vision
  {
    id: "openbmb",
    name: "OpenBMB (Tsinghua)",
    category: "vlm",
    categoryLabel: "Vision & Edge SLM",
    modelFamily: ["MiniCPM", "MiniCPM-V 2.6", "MiniCPM-o"],
    interfaceUrl: "https://modelplus.cn",
    interfaceName: "ModelPlus MiniCPM Studio",
    description: "SOTA edge vision-language models outperforming larger models on mobile hardware.",
    crmEntityId: "comp-openbmb",
    brandColor: "#059669",
    logo: OpenBmbLogo,
    _searchIndex: buildSearchIndex("OpenBMB (Tsinghua)", "SOTA edge vision-language models outperforming larger models on mobile hardware.", ["MiniCPM", "MiniCPM-V 2.6", "MiniCPM-o"], "ModelPlus MiniCPM Studio"),
  },
  {
    id: "opengvlab",
    name: "OpenGVLab",
    category: "vlm",
    categoryLabel: "Vision & Edge SLM",
    modelFamily: ["InternVL 2.5", "InternVL-Chat"],
    interfaceUrl: "https://internvl.opengvlab.com/",
    interfaceName: "InternVL Online Demo",
    description: "Open-source frontier multimodal model rivaling proprietary vision models.",
    crmEntityId: "comp-opengvlab",
    brandColor: "#4338CA",
    logo: OpenGvLabLogo,
    _searchIndex: buildSearchIndex("OpenGVLab", "Open-source frontier multimodal model rivaling proprietary vision models.", ["InternVL 2.5", "InternVL-Chat"], "InternVL Online Demo"),
  },
  {
    id: "qwen-vl",
    name: "Alibaba Cloud Vision",
    category: "vlm",
    categoryLabel: "Vision & Audio VLM",
    modelFamily: ["Qwen2-VL", "Qwen2-Audio"],
    interfaceUrl: "https://chat.qwenlm.ai",
    interfaceName: "Qwen Vision Web App",
    description: "Understands arbitrary resolution video, high-res documents, and multilingual audio.",
    crmEntityId: "comp-alibaba-cloud",
    brandColor: "#4F46E5",
    logo: QwenLogo,
    _searchIndex: buildSearchIndex("Alibaba Cloud Vision", "Understands arbitrary resolution video, high-res documents, and multilingual audio.", ["Qwen2-VL", "Qwen2-Audio"], "Qwen Vision Web App"),
  },
  {
    id: "zhipu-cogvlm",
    name: "Zhipu AI Multimodal",
    category: "vlm",
    categoryLabel: "Vision & Multimodal",
    modelFamily: ["CogVLM2", "CogVision"],
    interfaceUrl: "https://chatglm.cn",
    interfaceName: "CogVLM Visual Workspace",
    description: "Deep visual understanding with pixel-grounded spatial awareness.",
    crmEntityId: "comp-zhipu-ai",
    brandColor: "#2563EB",
    logo: ZhipuLogo,
    _searchIndex: buildSearchIndex("Zhipu AI Multimodal", "Deep visual understanding with pixel-grounded spatial awareness.", ["CogVLM2", "CogVision"], "CogVLM Visual Workspace"),
  },

  // 3. Video, Audio, & 3D
  {
    id: "tencent-hunyuan",
    name: "Tencent Hunyuan",
    category: "media",
    categoryLabel: "Video & 3D Gen",
    modelFamily: ["HunyuanVideo", "Hunyuan3D-2.0"],
    interfaceUrl: "https://hunyuan.tencent.com/",
    interfaceName: "Tencent Hunyuan Creation Studio",
    description: "World-class open cinematic video generation and rapid 3D asset synthesis.",
    crmEntityId: "comp-tencent",
    brandColor: "#0052D9",
    logo: TencentLogo,
    _searchIndex: buildSearchIndex("Tencent Hunyuan", "World-class open cinematic video generation and rapid 3D asset synthesis.", ["HunyuanVideo", "Hunyuan3D-2.0"], "Tencent Hunyuan Creation Studio"),
  },
  {
    id: "zhipu-cogvideo",
    name: "Zhipu AI Video",
    category: "media",
    categoryLabel: "Video Generation",
    modelFamily: ["CogVideoX-5B", "CogVideoX-Flash"],
    interfaceUrl: "https://chatglm.cn",
    interfaceName: "CogVideoX Generator",
    description: "High-frame-rate text-to-video and image-to-video generation.",
    crmEntityId: "comp-zhipu-ai",
    brandColor: "#2563EB",
    logo: ZhipuLogo,
    _searchIndex: buildSearchIndex("Zhipu AI Video", "High-frame-rate text-to-video and image-to-video generation.", ["CogVideoX-5B", "CogVideoX-Flash"], "CogVideoX Generator"),
  },
  {
    id: "map-yue",
    name: "Multimodal Art Projection",
    category: "media",
    categoryLabel: "Audio & Music Gen",
    modelFamily: ["YuE (Audio/Music)", "Vocalist"],
    interfaceUrl: "https://map-yue.github.io/",
    interfaceName: "YuE Music Interactive Space",
    description: "Full-song lyric-to-audio foundation models supporting diverse genres and voices.",
    crmEntityId: "comp-multimodal-art",
    brandColor: "#DB2777",
    logo: YueLogo,
    _searchIndex: buildSearchIndex("Multimodal Art Projection", "Full-song lyric-to-audio foundation models supporting diverse genres and voices.", ["YuE (Audio/Music)", "Vocalist"], "YuE Music Interactive Space"),
  },
  {
    id: "stepfun",
    name: "StepFun (Jieyue Xingchen)",
    category: "media",
    categoryLabel: "Audio & Video",
    modelFamily: ["Step-Audio", "Step-Video", "Step-1V"],
    interfaceUrl: "https://www.stepfun.com",
    interfaceName: "StepFun Consumer AI",
    description: "Multimodal reasoning with ultra-low latency emotional audio generation.",
    crmEntityId: "comp-stepfun",
    brandColor: "#0D9488",
    logo: StepFunLogo,
    _searchIndex: buildSearchIndex("StepFun (Jieyue Xingchen)", "Multimodal reasoning with ultra-low latency emotional audio generation.", ["Step-Audio", "Step-Video", "Step-1V"], "StepFun Consumer AI"),
  },

  // 4. Embeddings & Specialized Tooling
  {
    id: "baai-bge",
    name: "BAAI (FlagOpen / BGE)",
    category: "tooling",
    categoryLabel: "Embeddings & Rerank",
    modelFamily: ["BGE-M3", "BGE-Reranker-Large", "BAAI/bge-en-icl"],
    interfaceUrl: "https://flagopen.baai.ac.cn/",
    interfaceName: "FlagOpen Model Platform",
    description: "The global benchmark for multi-lingual dense retrieval, sparse matching, and reranking.",
    crmEntityId: "comp-baai",
    brandColor: "#1D4ED8",
    logo: BaaiLogo,
    _searchIndex: buildSearchIndex("BAAI (FlagOpen / BGE)", "The global benchmark for multi-lingual dense retrieval, sparse matching, and reranking.", ["BGE-M3", "BGE-Reranker-Large", "BAAI/bge-en-icl"], "FlagOpen Model Platform"),
  },
  {
    id: "qwen-agent",
    name: "Alibaba / Tongyi Agent",
    category: "tooling",
    categoryLabel: "Agent Framework",
    modelFamily: ["Qwen-Agent", "Qwen2.5-FunctionCalling"],
    interfaceUrl: "https://chat.qwenlm.ai",
    interfaceName: "Qwen Agent Playground",
    description: "Autonomous agent execution engine with 8k-token tool schemas and code interpreter.",
    crmEntityId: "comp-alibaba-cloud",
    brandColor: "#4F46E5",
    logo: QwenLogo,
    _searchIndex: buildSearchIndex("Alibaba / Tongyi Agent", "Autonomous agent execution engine with 8k-token tool schemas and code interpreter.", ["Qwen-Agent", "Qwen2.5-FunctionCalling"], "Qwen Agent Playground"),
  },
];

const ModelOrgCard = memo(function ModelOrgCard({ org }: { org: AIModelOrg }) {
  const Logo = org.logo;
  return (
    <Card className="group flex flex-col justify-between overflow-hidden border-current/15 transition-all duration-200 hover:border-current/30 hover:shadow-md">
      <CardContent className="p-4 space-y-3.5 flex flex-col justify-between h-full">
        {/* Card Header: Logo, Name, Badge */}
        <div className="space-y-2.5">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="shrink-0 transition-transform group-hover:scale-105">
                <Logo />
              </div>
              <div>
                <h4 className="font-bold text-sm text-text-primary leading-tight">
                  {org.name}
                </h4>
                <span className="text-[11px] font-mono text-text-tertiary">
                  {org.categoryLabel}
                </span>
              </div>
            </div>

            {org.crmEntityId && (
              <Badge className="text-[10px] font-mono font-normal shrink-0 flex items-center gap-1 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                <CheckCircle2 className="h-2.5 w-2.5" />
                <span>Synced</span>
              </Badge>
            )}
          </div>

          {/* Model Families Tags */}
          <div className="flex flex-wrap gap-1">
            {org.modelFamily.map((model: string) => (
              <span
                key={model}
                className="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-medium bg-current/5 text-text-secondary border border-current/10"
              >
                {model}
              </span>
            ))}
          </div>

          {/* Description */}
          <p className="text-xs text-text-secondary leading-relaxed line-clamp-2">
            {org.description}
          </p>
        </div>

        {/* Direct LLM Interface Link Button */}
        <div className="pt-2 border-t border-current/10">
          <a
            href={org.interfaceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className={cn(
              "flex w-full items-center justify-between gap-2 px-3 py-2 rounded-md",
              "bg-primary/10 text-primary hover:bg-primary hover:text-primary-foreground",
              "font-sans text-xs font-semibold tracking-wide transition-all duration-200 cursor-pointer shadow-xs",
            )}
          >
            <div className="flex items-center gap-1.5 truncate">
              <Sparkles className="h-3.5 w-3.5 shrink-0" />
              <span className="truncate">{org.interfaceName}</span>
            </div>
            <ExternalLink className="h-3.5 w-3.5 shrink-0 opacity-80" />
          </a>
        </div>
      </CardContent>
    </Card>
  );
});

const CATEGORY_TABS = [
  { id: "all", label: "All Models", count: CHINESE_AI_ORGS.length },
  { id: "llm", label: "Foundational LLMs", icon: Bot },
  { id: "vlm", label: "Vision & Multimodal", icon: Eye },
  { id: "media", label: "Video & Audio", icon: Video },
  { id: "tooling", label: "Embeddings & Agents", icon: Layers },
] as const;

export function ChineseAIHub({
  twentyCrmUrl = "http://localhost:3020",
}: {
  twentyCrmUrl?: string;
}) {
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState("");

  const filteredOrgs = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    return CHINESE_AI_ORGS.filter((org) => {
      const matchesCategory =
        selectedCategory === "all" || org.category === selectedCategory;
      if (!matchesCategory) return false;
      return !q || org._searchIndex.includes(q);
    });
  }, [selectedCategory, searchQuery]);

  return (
    <div className="space-y-6">
      {/* Top Banner with Twenty CRM Direct Link */}
      <div className="relative overflow-hidden rounded-xl border border-current/15 bg-gradient-to-r from-blue-950/20 via-background-base to-purple-950/20 p-5 shadow-sm">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <Typography className="font-bold text-sm tracking-wide uppercase text-midground">
                Open-Source Ecosystem & CRM Directory
              </Typography>
            </div>
            <Typography className="text-xl font-bold text-text-primary tracking-tight">
              Chinese AI Frontier Models & Live Interfaces
            </Typography>
            <p className="text-xs text-text-secondary max-w-2xl leading-relaxed">
              Direct access to live playgrounds, chat systems, and reasoning web interfaces for China's leading AI organizations. Ingested and synchronized with your local Twenty CRM workspace.
            </p>
          </div>

          {/* Twenty CRM Quick Action Link */}
          <div className="flex shrink-0 items-center gap-3">
            <a
              href={twentyCrmUrl}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Open Twenty CRM Workspace"
              className={cn(
                "group flex items-center gap-3 rounded-lg border border-blue-500/30 bg-blue-500/10 px-4 py-2.5",
                "text-text-primary transition-all duration-200 hover:border-blue-500/60 hover:bg-blue-500/20 hover:shadow-md",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500",
              )}
            >
              <TwentyLogo className="h-6 w-6 shrink-0 transition-transform group-hover:scale-105" />
              <div className="text-left">
                <div className="flex items-center gap-1.5 font-bold text-xs text-blue-400">
                  <span>Twenty CRM</span>
                  <ArrowUpRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                </div>
                <div className="text-[11px] text-text-tertiary">
                  System of Record (17 Companies)
                </div>
              </div>
            </a>
          </div>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-1.5">
          {CATEGORY_TABS.map((tab) => {
            const active = selectedCategory === tab.id;
            const Icon = "icon" in tab ? tab.icon : undefined;
            return (
              <Button
                key={tab.id}
                size="sm"
                outlined={!active}
                onClick={() => setSelectedCategory(tab.id)}
                className={cn(
                  "h-8 text-xs font-medium cursor-pointer transition-all",
                  active
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-text-secondary hover:text-text-primary",
                )}
              >
                {Icon && <Icon className="h-3.5 w-3.5 mr-1" />}
                {tab.label}
              </Button>
            );
          })}
        </div>

        {/* Search input with clear button */}
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-text-tertiary pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search models, orgs..."
            className={cn(
              "w-full h-8 pl-8 pr-7 text-xs rounded-md border border-current/20 bg-background-base",
              "text-text-primary placeholder:text-text-tertiary",
              "focus:outline-none focus:ring-1 focus:ring-primary",
            )}
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => setSearchQuery("")}
              aria-label="Clear search"
              className="absolute right-2 top-1/2 -translate-y-1/2 text-text-tertiary hover:text-text-primary cursor-pointer p-0.5"
            >
              <X className="h-3 w-3" />
            </button>
          )}
        </div>
      </div>

      {/* Models Grid */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {filteredOrgs.map((org: AIModelOrg) => (
          <ModelOrgCard key={org.id} org={org} />
        ))}
      </div>

      {filteredOrgs.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center text-text-tertiary">
          <Bot className="h-10 w-10 mb-2 opacity-40" />
          <p className="text-sm font-medium">No models match your query</p>
          <p className="text-xs mt-1">Try clearing your search or category filter.</p>
        </div>
      )}
    </div>
  );
}
