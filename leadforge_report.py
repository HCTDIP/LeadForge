#!/usr/bin/env python3
"""
LeadForge Report Generator
从 leadforge.py 的 JSON 输出生成可读报告（Markdown/HTML/控制台）
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


def load_results(json_path: str) -> Dict[str, Any]:
    """加载 leadforge.py 的输出 JSON"""
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"结果文件不存在: {json_path}")
    return json.loads(path.read_text(encoding="utf-8"))


def generate_markdown_report(data: Dict[str, Any]) -> str:
    """生成 Markdown 格式报告"""
    lines = []
    lines.append(f"# LeadForge Report")
    lines.append(f"")
    lines.append(f"**Query:** {data.get('query', 'N/A')}")
    lines.append(f"**Timestamp:** {data.get('timestamp', 'N/A')}")
    lines.append(f"**Model:** {data.get('model', 'N/A')}")
    lines.append(f"**Elapsed:** {data.get('elapsed_seconds', 0)}s")
    lines.append(f"**Leads Found:** {data.get('leads_found', 0)}")
    lines.append(f"**Warm Leads:** {data.get('warm_leads', 0)}")
    lines.append(f"**Messages Generated:** {data.get('messages_generated', 0)}")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    leads = data.get("leads", [])
    messages = data.get("messages", [])
    msg_by_lead = {m["lead_id"]: m for m in messages}

    for i, lead in enumerate(leads, 1):
        lines.append(f"## Lead #{i}: {lead['title']}")
        lines.append(f"")
        lines.append(f"- **HN ID:** {lead['objectID']}")
        lines.append(f"- **Author:** {lead['author']}")
        lines.append(f"- **Points:** {lead['points']} ({'🔥 Warm' if lead['points'] >= 30 else '❄️ Cold'})")
        lines.append(f"- **Comments:** {lead['num_comments']}")
        lines.append(f"- **URL:** {lead['url']}")
        lines.append(f"- **Created:** {lead['created_at']}")
        lines.append(f"")

        msg = msg_by_lead.get(lead['objectID'])
        if msg:
            lines.append(f"### Outreach Message")
            lines.append(f"")
            lines.append(f"**Subject:** {msg['subject']}")
            lines.append(f"")
            lines.append(f"**Body:**")
            lines.append(f"")
            lines.append(f"> {msg['body'].replace(chr(10), chr(10) + '> ')}")
            lines.append(f"")
            lines.append(f"*Model: {msg['model_used']} | Generated: {msg['generated_at']}*")
        else:
            lines.append(f"*⚠️ 未生成 outreach*")
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")

    return "\n".join(lines)


def generate_html_report(data: Dict[str, Any]) -> str:
    """生成 HTML 格式报告（phone viewport 自适应）"""
    md = generate_markdown_report(data)
    # 简单转换 markdown -> html（基础版）
    html_lines = []
    html_lines.append("""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LeadForge Report</title>
<style>
* { box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; max-width: 100vw; margin: 0; padding: 1rem; font-size: clamp(14px, 3.5vw, 16px); color: #1a1a1a; background: #fafafa; }
h1 { font-size: clamp(1.5rem, 5vw, 2rem); margin-bottom: 0.5rem; }
h2 { font-size: clamp(1.2rem, 4vw, 1.5rem); margin-top: 2rem; border-bottom: 1px solid #eee; padding-bottom: 0.3rem; }
h3 { font-size: clamp(1rem, 3.5vw, 1.2rem); }
.meta { color: #666; font-size: clamp(12px, 3vw, 14px); margin-bottom: 1rem; }
.card { background: white; border-radius: 12px; padding: 1rem; margin: 1rem 0; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.warm { border-left: 4px solid #f59e0b; }
.cold { border-left: 4px solid #9ca3af; }
.subject { font-weight: 600; color: #111; }
.body { white-space: pre-wrap; background: #f8fafc; padding: 0.75rem; border-radius: 8px; font-size: clamp(13px, 3.2vw, 15px); }
.model-note { color: #666; font-size: clamp(11px, 2.8vw, 13px); margin-top: 0.5rem; }
a { color: #2563eb; text-decoration: none; }
a:hover { text-decoration: underline; }
hr { border: none; border-top: 1px solid #eee; margin: 1.5rem 0; }
</style>
</head>
<body>
""")

    # 简单解析 markdown 生成 HTML（简化版）
    in_body = False
    for line in md.split("\n"):
        if line.startswith("# "):
            html_lines.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("## "):
            html_lines.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("### "):
            html_lines.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("- **") and ":**" in line:
            key, val = line[3:].split(":** ", 1)
            html_lines.append(f'<div class="meta"><strong>{key}:</strong> {val}</div>')
        elif line.startswith("> "):
            if not in_body:
                html_lines.append('<div class="body">')
                in_body = True
            html_lines.append(line[2:])
        elif in_body and line == "":
            html_lines.append('</div>')
            in_body = False
        elif line.startswith("*"):
            html_lines.append(f'<div class="model-note">{line[1:].strip()}</div>')
        elif line == "---":
            html_lines.append("<hr>")
        elif line.strip():
            html_lines.append(f"<p>{line}</p>")

    if in_body:
        html_lines.append('</div>')

    html_lines.append("</body></html>")
    return "\n".join(html_lines)


def generate_console_report(data: Dict[str, Any]) -> str:
    """生成控制台友好报告"""
    lines = []
    lines.append("=" * 60)
    lines.append("LeadForge Report")
    lines.append("=" * 60)
    lines.append(f"Query: {data.get('query')}")
    lines.append(f"Time:  {data.get('timestamp')}")
    lines.append(f"Model: {data.get('model')}")
    lines.append(f"Elapsed: {data.get('elapsed_seconds')}s")
    lines.append(f"Leads: {data.get('leads_found')} found → {data.get('warm_leads')} warm → {data.get('messages_generated')} messages")
    lines.append("-" * 60)

    leads = data.get("leads", [])
    messages = data.get("messages", [])
    msg_by_lead = {m["lead_id"]: m for m in messages}

    for i, lead in enumerate(leads, 1):
        warm = "🔥" if lead['points'] >= 30 else "❄️"
        lines.append(f"\n#{i} {lead['title'][:60]} {warm}")
        lines.append(f"   HN: {lead['objectID']} | {lead['author']} | {lead['points']}pts | {lead['num_comments']}cmts")
        lines.append(f"   URL: {lead['url']}")

        msg = msg_by_lead.get(lead['objectID'])
        if msg:
            lines.append(f"   Subject: {msg['subject']}")
            body_preview = msg['body'][:120].replace("\n", " ") + "..."
            lines.append(f"   Body: {body_preview}")
            lines.append(f"   Model: {msg['model_used']}")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="LeadForge Report Generator")
    parser.add_argument("input", help="leadforge.py 输出的 JSON 文件")
    parser.add_argument("--format", "-f", choices=["markdown", "html", "console"], default="console", help="输出格式")
    parser.add_argument("--output", "-o", help="输出文件路径（默认 stdout）")
    args = parser.parse_args()

    try:
        data = load_results(args.input)
    except Exception as e:
        print(f"❌ 读取失败: {e}", file=sys.stderr)
        sys.exit(1)

    if args.format == "markdown":
        report = generate_markdown_report(data)
    elif args.format == "html":
        report = generate_html_report(data)
    else:
        report = generate_console_report(data)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"✅ 报告已写入: {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()