"""Ingestion script for the Comprehensive Chinese AI Open-Source Repository Directory into Twenty CRM."""

from datetime import datetime, timezone
import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "twenty_crm" / "data.json"


CHINESE_AI_COMPANIES = [
    {
        "id": "comp-deepseek",
        "name": "DeepSeek AI",
        "domainName": "deepseek.com",
        "employees": 150,
        "annualRecurringRevenue": 1200000,
        "createdAt": "2026-10-04T12:00:00Z",
        "enrichedTags": ["Foundational LLM", "Reasoning", "DeepSeek-V3", "R1", "DeepSeek-Coder", "Open-Source"],
    },
    {
        "id": "comp-alibaba-qwen",
        "name": "Alibaba Cloud (Qwen Team)",
        "domainName": "alibabacloud.com",
        "employees": 130000,
        "annualRecurringRevenue": 2500000,
        "createdAt": "2026-10-04T12:00:00Z",
        "enrichedTags": ["Qwen 2.5", "Qwen-Coder", "Qwen-VL", "Qwen-Agent", "Hyperscaler"],
    },
    {
        "id": "comp-zhipu-thudm",
        "name": "Zhipu AI & Tsinghua KEG",
        "domainName": "zhipuai.cn",
        "employees": 800,
        "annualRecurringRevenue": 950000,
        "createdAt": "2026-10-04T12:00:00Z",
        "enrichedTags": ["ChatGLM", "GLM-4", "CogVLM2", "CogVideoX", "Tsinghua"],
    },
    {
        "id": "comp-01-ai",
        "name": "01.AI (Kai-Fu Lee)",
        "domainName": "01.ai",
        "employees": 200,
        "annualRecurringRevenue": 400000,
        "createdAt": "2026-10-04T12:00:00Z",
        "enrichedTags": ["Yi", "Yi-1.5", "Yi-34B", "Foundational LLM"],
    },
    {
        "id": "comp-baichuan",
        "name": "Baichuan Intelligent",
        "domainName": "baichuan-ai.com",
        "employees": 250,
        "annualRecurringRevenue": 350000,
        "createdAt": "2026-10-04T12:00:00Z",
        "enrichedTags": ["Baichuan 2", "Healthcare LLM", "Enterprise"],
    },
    {
        "id": "comp-shanghai-ai-lab",
        "name": "Shanghai AI Laboratory",
        "domainName": "shlab.org.cn",
        "employees": 1200,
        "annualRecurringRevenue": 1500000,
        "createdAt": "2026-10-04T12:00:00Z",
        "enrichedTags": ["InternLM 2.5", "InternVL", "Research Institute", "Open-Source"],
    },
    {
        "id": "comp-xverse",
        "name": "XVERSE Technology",
        "domainName": "xverse.cn",
        "employees": 180,
        "annualRecurringRevenue": 280000,
        "createdAt": "2026-10-04T12:00:00Z",
        "enrichedTags": ["XVERSE-13B", "XVERSE-65B", "Long Context"],
    },
    {
        "id": "comp-inspur",
        "name": "Inspur (IEG)",
        "domainName": "inspur.com",
        "employees": 32000,
        "annualRecurringRevenue": 800000,
        "createdAt": "2026-10-04T12:00:00Z",
        "enrichedTags": ["Yuan 2.0", "HPC", "Enterprise Compute"],
    },
    {
        "id": "comp-baai",
        "name": "Beijing Academy of Artificial Intelligence (BAAI)",
        "domainName": "baai.ac.cn",
        "employees": 600,
        "annualRecurringRevenue": 900000,
        "createdAt": "2026-10-04T12:00:00Z",
        "enrichedTags": ["BGE Embeddings", "Aquila 2", "WuDao", "FlagEmbedding", "FlagAI"],
    },
    {
        "id": "comp-kunlun",
        "name": "Kunlun Tech",
        "domainName": "kunlun.com",
        "employees": 1500,
        "annualRecurringRevenue": 450000,
        "createdAt": "2026-10-04T12:00:00Z",
        "enrichedTags": ["Skywork", "Skywork-MoE", "Open-Weights"],
    },
    {
        "id": "comp-openbmb",
        "name": "OpenBMB (Tsinghua ModelBest)",
        "domainName": "openbmb.org",
        "employees": 120,
        "annualRecurringRevenue": 300000,
        "createdAt": "2026-10-04T12:00:00Z",
        "enrichedTags": ["MiniCPM", "MiniCPM-V", "On-Device SLM", "Edge AI"],
    },
    {
        "id": "comp-opengvlab",
        "name": "OpenGVLab",
        "domainName": "opengvlab.github.io",
        "employees": 80,
        "annualRecurringRevenue": 200000,
        "createdAt": "2026-10-04T12:00:00Z",
        "enrichedTags": ["InternVL", "Multimodal Vision", "VLM Leaderboard"],
    },
    {
        "id": "comp-map-yue",
        "name": "Multimodal Art Projection (YuE)",
        "domainName": "map-bmu.github.io",
        "employees": 50,
        "annualRecurringRevenue": 150000,
        "createdAt": "2026-10-04T12:00:00Z",
        "enrichedTags": ["YuE", "Audio Generation", "Music AI", "Full-Song Generation"],
    },
    {
        "id": "comp-stepfun",
        "name": "StepFun (Jieyue Xingchen)",
        "domainName": "stepfun.com",
        "employees": 220,
        "annualRecurringRevenue": 500000,
        "createdAt": "2026-10-04T12:00:00Z",
        "enrichedTags": ["Step-Audio", "StepVideo", "Omni Multimodal"],
    },
]

OPPORTUNITY_CHINESE_AI = {
    "id": "opp-chinese-ai",
    "name": "China Open-Source AI Upstream Sync & Infrastructure Mesh",
    "amount": {
        "amountMicros": 500000000000,
        "currencyCode": "USD",
    },
    "stage": "NEGOTIATION",
    "closeDate": "2026-12-31T00:00:00Z",
    "companyId": "comp-deepseek",
    "pointOfContactId": "person-1",
    "probability": 90,
    "assignedEmployeeId": "emp-101",
}

NOTES = [
    {
        "id": "note-zh-llm-1",
        "title": "Foundational LLMs Repository Upstream Directory",
        "body": (
            "### Foundational Large Language Models (LLMs)\n"
            "Direct GitHub upstream addresses for automated sync:\n"
            "• DeepSeek AI: DeepSeek-V3, R1, Coder (https://github.com/deepseek-ai/DeepSeek-V3)\n"
            "• Alibaba Cloud: Qwen 2.5, Qwen-Coder (https://github.com/QwenLM/Qwen2.5)\n"
            "• Zhipu AI & Tsinghua: ChatGLM, GLM-4 (https://github.com/THUDM/ChatGLM3)\n"
            "• 01.AI: Yi, Yi-1.5 (https://github.com/01-ai/Yi-1.5)\n"
            "• Baichuan Intelligent: Baichuan 2 (https://github.com/baichuan-inc/Baichuan2)\n"
            "• Shanghai AI Lab: InternLM 2.5 (https://github.com/InternLM/InternLM)\n"
            "• XVERSE Technology: XVERSE (https://github.com/xverse-ai/XVERSE-13B)\n"
            "• Inspur (IEG): Yuan 2.0 (https://github.com/IEG-Yuan/Yuan-2.0)\n"
            "• BAAI: Aquila 2, WuDao (https://github.com/FlagAI-Open/FlagAI)\n"
            "• Kunlun Tech: Skywork, Skywork-MoE (https://github.com/SkyworkAI/Skywork)"
        ),
        "targetOpportunityId": "opp-chinese-ai",
        "targetCompanyId": "comp-deepseek",
        "author": "Hermes Upstream Sync Engine",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "note-zh-vlm-2",
        "title": "Multimodal, Vision, and Edge Models (VLMs / SLMs) Directory",
        "body": (
            "### Multimodal, Vision, and Edge Models (VLMs / SLMs)\n"
            "Direct GitHub upstream addresses for automated sync:\n"
            "• OpenBMB (Tsinghua): MiniCPM, MiniCPM-V (https://github.com/OpenBMB/MiniCPM)\n"
            "• OpenGVLab: InternVL Vision Leader (https://github.com/OpenGVLab/InternVL)\n"
            "• Alibaba Cloud: Qwen-VL, Qwen2-Audio (https://github.com/QwenLM/Qwen2-VL)\n"
            "• Zhipu AI & Tsinghua: CogVLM, CogVision (https://github.com/THUDM/CogVLM2)"
        ),
        "targetOpportunityId": "opp-chinese-ai",
        "targetCompanyId": "comp-openbmb",
        "author": "Hermes Upstream Sync Engine",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "note-zh-gen-3",
        "title": "Video, Audio, and 3D Generation Repositories",
        "body": (
            "### Video, Audio, and 3D Generation\n"
            "Direct GitHub upstream addresses for automated sync:\n"
            "• Tencent: HunyuanVideo, Hunyuan3D (https://github.com/Tencent/HunyuanVideo)\n"
            "• Zhipu AI: CogVideoX (https://github.com/THUDM/CogVideo)\n"
            "• Multimodal Art Projection: YuE Audio/Music (https://github.com/multimodal-art-projection/YuE)\n"
            "• StepFun: Step-Audio, stepvideo (https://github.com/stepfun-ai)"
        ),
        "targetOpportunityId": "opp-chinese-ai",
        "targetCompanyId": "comp-3",
        "author": "Hermes Upstream Sync Engine",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": "note-zh-emb-4",
        "title": "Embeddings & Specialized Agent Tooling Directory",
        "body": (
            "### Embeddings and Specialized Tooling\n"
            "Direct GitHub upstream addresses for automated sync:\n"
            "• BAAI (Beijing Academy of AI): BGE Embeddings (https://github.com/FlagOpen/FlagEmbedding)\n"
            "• Alibaba / Tongyi: Qwen-Agent Framework (https://github.com/QwenLM/Qwen-Agent)"
        ),
        "targetOpportunityId": "opp-chinese-ai",
        "targetCompanyId": "comp-baai",
        "author": "Hermes Upstream Sync Engine",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    },
]


def ingest():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)

    # 1. Ingest Companies
    existing_comp_ids = {c["id"] for c in db.get("companies", [])}
    added_comps = 0
    for comp in CHINESE_AI_COMPANIES:
        if comp["id"] not in existing_comp_ids:
            db["companies"].append(comp)
            existing_comp_ids.add(comp["id"])
            added_comps += 1

    # 2. Ingest Opportunity
    existing_opp_ids = {o["id"] for o in db.get("opportunities", [])}
    added_opps = 0
    if OPPORTUNITY_CHINESE_AI["id"] not in existing_opp_ids:
        db["opportunities"].append(OPPORTUNITY_CHINESE_AI)
        added_opps += 1

    # 3. Ingest Notes
    existing_note_ids = {n["id"] for n in db.get("notes", [])}
    added_notes = 0
    for note in NOTES:
        if note["id"] not in existing_note_ids:
            db["notes"].append(note)
            added_notes += 1

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)

    print(f"Successfully ingested Chinese AI Repository Directory into Twenty CRM:")
    print(f"• Added {added_comps} AI organizations/companies (Total: {len(db['companies'])})")
    print(f"• Added {added_opps} upstream sync opportunity (Total: {len(db['opportunities'])})")
    print(f"• Added {added_notes} categorized repository notes (Total: {len(db['notes'])})")


if __name__ == "__main__":
    ingest()
