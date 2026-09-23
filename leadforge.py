#!/usr/bin/env python3
"""
LeadForge — NIM-backed Lead Agent
End-to-end: discover HN leads → score → generate personalized outreach → output report

Usage:
    python3 leadforge.py "workflow automation"
    python3 leadforge.py --query "workflow automation" --max-leads 5 --model nemotron-3-ultra
"""

import os
import sys
import json
import time
import argparse
import logging
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime, timezone
import urllib.request
import urllib.error

# ── 配置 ─────────────────────────────────────────────────────────────
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY")
NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_MODEL = "nvidia/nemotron-3-ultra-550b-a55b"
HN_ALGOLIA_URL = "https://hn.algolia.com/api/v1/search"

# 重试配置
MAX_RETRIES = 2
BASE_BACKOFF = 30  # seconds
WATCHDOG_TIMEOUT = 120

# 评分阈值
MIN_HN_POINTS_WARM = 30

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("leadforge")


# ── 数据模型 ─────────────────────────────────────────────────────────
@dataclass
class HNLead:
    objectID: str
    title: str
    url: str
    author: str
    points: int
    num_comments: int
    created_at: str
    story_text: str = ""

    @property
    def is_warm(self) -> bool:
        return self.points >= MIN_HN_POINTS_WARM


@dataclass
class OutreachMessage:
    lead_id: str
    subject: str
    body: str
    model_used: str
    generated_at: str


# ── HN 发现层 ────────────────────────────────────────────────────────
def discover_hn_leads(query: str, max_results: int = 10) -> List[HNLead]:
    """从 HN Algolia 搜索 leads（免鉴权）"""
    params = urllib.parse.urlencode({
        "query": query,
        "tags": "story",
        "hitsPerPage": max_results,
    })
    url = f"{HN_ALGOLIA_URL}?{params}"

    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.load(resp)
    except Exception as e:
        log.error(f"HN 搜索失败: {e}")
        return []

    leads = []
    for hit in data.get("hits", []):
        leads.append(HNLead(
            objectID=hit.get("objectID", ""),
            title=hit.get("title", ""),
            url=hit.get("url", "") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
            author=hit.get("author", ""),
            points=hit.get("points", 0),
            num_comments=hit.get("num_comments", 0),
            created_at=hit.get("created_at", ""),
            story_text=hit.get("story_text", "")[:2000],
        ))
    log.info(f"HN 发现 {len(leads)} 条 leads")
    return leads


def filter_warm_leads(leads: List[HNLead], max_leads: int = 5) -> List[HNLead]:
    """按 points 加权筛选 warm leads"""
    warm = [l for l in leads if l.is_warm]
    warm.sort(key=lambda x: x.points, reverse=True)
    selected = warm[:max_leads]
    log.info(f"筛选后 {len(selected)} 条 warm leads (points≥{MIN_HN_POINTS_WARM})")
    return selected


# ── NIM 调用封装 ─────────────────────────────────────────────────────
class NIMClient:
    """NVIDIA NIM API 客户端，含重试、退避、fallback、watchdog"""

    def __init__(self, api_key: str, base_url: str = NIM_BASE_URL, model: str = DEFAULT_MODEL):
        if not api_key:
            raise RuntimeError("NVIDIA_API_KEY 未设置")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _request_with_retry(self, payload: Dict) -> Dict:
        """带重试、退避、watchdog 的请求"""
        last_err = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                req = urllib.request.Request(
                    f"{self.base_url}/chat/completions",
                    data=json.dumps(payload).encode(),
                    headers=self.headers,
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=WATCHDOG_TIMEOUT) as resp:
                    return json.load(resp)
            except urllib.error.HTTPError as e:
                last_err = e
                if e.code in (503, 404) and attempt < MAX_RETRIES:
                    wait = BASE_BACKOFF * (attempt + 1)
                    log.warning(f"NIM {e.code}，{wait}s 后重试 (attempt {attempt+1}/{MAX_RETRIES})")
                    time.sleep(wait)
                    continue
                elif e.code == 429 and attempt < MAX_RETRIES:
                    wait = BASE_BACKOFF * (attempt + 1)
                    log.warning(f"NIM 429，{wait}s 后重试")
                    time.sleep(wait)
                    continue
                else:
                    raise
            except Exception as e:
                last_err = e
                if attempt < MAX_RETRIES:
                    wait = BASE_BACKOFF * (attempt + 1)
                    log.warning(f"NIM 请求异常: {e}，{wait}s 后重试")
                    time.sleep(wait)
                    continue
                raise
        raise RuntimeError(f"NIM 请求失败，已重试 {MAX_RETRIES} 次: {last_err}")

    def generate_outreach(self, lead: HNLead, query: str) -> OutreachMessage:
        """生成个性化 outreach 消息"""
        prompt = f"""You are a senior BD engineer reaching out to a technical founder.

Lead context:
- Title: {lead.title}
- Author: {lead.author}
- HN Points: {lead.points}
- Comments: {lead.num_comments}
- URL: {lead.url}
- Story excerpt: {lead.story_text[:500]}

Your query/topic: {query}

Write a concise, personalized cold email (subject + body) that:
1. References their specific HN post
2. Shows genuine interest in their problem space
3. Proposes a low-friction conversation (not a pitch)
4. Sounds human, not templated

Format:
Subject: <subject line>
Body: <email body>"""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You write concise, human-sounding cold outreach for technical founders."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 500,
        }

        try:
            resp = self._request_with_retry(payload)
            content = resp["choices"][0]["message"]["content"].strip()

            # 解析 Subject / Body
            subject = ""
            body = content
            for line in content.split("\n"):
                if line.lower().startswith("subject:"):
                    subject = line.split(":", 1)[1].strip()
                    body = content.replace(line, "").strip()
                    break

            if not subject:
                subject = f"Re: your post on {lead.title[:50]}"

            return OutreachMessage(
                lead_id=lead.objectID,
                subject=subject,
                body=body,
                model_used=self.model,
                generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            )
        except Exception as e:
            log.error(f"NIM 生成失败: {e}")
            # Fallback: 规则兜底
            return self._fallback_outreach(lead, query)

    def _fallback_outreach(self, lead: HNLead, query: str) -> OutreachMessage:
        """规则兜底模板"""
        subject = f"Re: your HN post — {lead.title[:60]}"
        body = f"""Hey {lead.author},

Saw your post "{lead.title}" on HN ({lead.points} points). I'm building in the {query} space and your take on [problem from post] resonated.

Would love to chat briefly — no pitch, just comparing notes on how you're thinking about [related challenge].

Best,
[Your Name]"""
        return OutreachMessage(
            lead_id=lead.objectID,
            subject=subject,
            body=body,
            model_used=f"{self.model}-fallback",
            generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        )


# ── 主流程 ───────────────────────────────────────────────────────────
def run_pipeline(query: str, max_leads: int = 5, model: str = DEFAULT_MODEL) -> Dict[str, Any]:
    """端到端流程"""
    start_time = time.time()

    # 1. 发现
    leads = discover_hn_leads(query, max_results=max_leads * 2)
    if not leads:
        return {"error": "No leads found", "query": query}

    # 2. 筛选
    warm_leads = filter_warm_leads(leads, max_leads)
    if not warm_leads:
        # 兜底：取前 N 条即使 points 低
        warm_leads = leads[:max_leads]
        log.warning("无 warm leads，回退取前 N 条")

    # 3. 生成 outreach
    client = NIMClient(NVIDIA_API_KEY, model=model)
    messages = []
    for lead in warm_leads:
        log.info(f"Generating outreach for {lead.objectID} ({lead.points} pts)")
        msg = client.generate_outreach(lead, query)
        messages.append(msg)

    elapsed = time.time() - start_time
    return {
        "query": query,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "leads_found": len(leads),
        "warm_leads": len(warm_leads),
        "messages_generated": len(messages),
        "elapsed_seconds": round(elapsed, 2),
        "model": model,
        "leads": [asdict(l) for l in warm_leads],
        "messages": [asdict(m) for m in messages],
    }


def main():
    parser = argparse.ArgumentParser(description="LeadForge — NIM-backed Lead Agent")
    parser.add_argument("query", nargs="?", default="workflow automation", help="Search query for HN leads")
    parser.add_argument("--max-leads", type=int, default=5, help="Max warm leads to process")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="NIM model to use")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    args = parser.parse_args()

    if not NVIDIA_API_KEY:
        print("❌ NVIDIA_API_KEY 环境变量未设置", file=sys.stderr)
        sys.exit(1)

    log.info(f"启动 LeadForge: query='{args.query}', max_leads={args.max_leads}, model={args.model}")
    result = run_pipeline(args.query, args.max_leads, args.model)

    if "error" in result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)

    output_json = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output_json, encoding="utf-8")
        log.info(f"结果已写入: {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()