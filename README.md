# LeadForge

**NIM-backed Lead Agent** — One command to your next ten customers.

Find, qualify, and generate personalized outreach for high-intent leads from Hacker News in seconds. Built on free-tier infrastructure: NVIDIA Nemotron, Jev calibration, and ColdEmailOS (open source).

## Why LeadForge?

| Problem | LeadForge Solution |
|---------|-------------------|
| Cold email reply rate: **0.1%** | Personalized, context-aware outreach — not templates |
| **47%** of cold emails never reach inbox | Brevo shared domains (zero DNS, instant warmup) |
| **6+ months** to first 10 customers | **5 minutes** to first qualified lead |
| $49-97/mo for email infra | **$0** — all free tiers, self-hosted |

## Quick Start

```bash
# 1. Clone
git clone https://github.com/HCTDIP/LeadForge.git
cd LeadForge

# 2. Install deps
pip install -r requirements.txt

# 3. Set NVIDIA API key (free tier at build.nvidia.com)
export NVIDIA_API_KEY="nvapi-..."

# 4. Run
python3 leadforge.py "workflow automation" --max-leads 5
```

## Output

```json
{
  "query": "workflow automation",
  "leads_found": 12,
  "warm_leads": 5,
  "messages_generated": 5,
  "elapsed_seconds": 8.3,
  "leads": [...],
  "messages": [
    {
      "lead_id": "123456",
      "subject": "Re: your HN post on workflow automation",
      "body": "Hey, saw your post on GitHub Actions...\n\nWould love to chat...",
      "model_used": "nvidia/nemotron-3-ultra-550b-a55b"
    }
  ]
}
```

Generate a readable report:
```bash
python3 leadforge_report.py results.json --format html --output report.html
python3 leadforge_report.py results.json --format markdown --output report.md
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────┐
│  HN Algolia │────▶│  Jev-style  │────▶│  NVIDIA Nemotron │
│  (free)     │     │  points gate│     │  (free tier)     │
└─────────────┘     └─────────────┘     └──────────────────┘
       │                   │                     │
       ▼                   ▼                     ▼
  Raw leads           Warm filter           Personalized
  (10-20)             (points≥30)           outreach
```

**Three-layer qualification:**
1. **HN Points gate** — `points ≥ 30` = warm candidate (rules, instant)
2. **Jev calibration** (System 1) — `noul ≤ 0.08` escalates semantic false positives (optional)
3. **NIM reasoning** (System 2) — Generates personalized icebreaker + qualification

## Tech Stack (All Free)

| Layer | Tech | Cost |
|-------|------|------|
| Discovery | HN Algolia API | Free |
| Qualification | NVIDIA Nemotron 3 Ultra | Free tier (82 models) |
| Semantic gate | Jev (optional) | ~$0.00002/call |
| Email infra | ColdEmailOS + Brevo | 300/day free |
| Hosting | Self-hosted / Railway / Fly.io | Free tiers |

## Requirements

- Python 3.10+
- `NVIDIA_API_KEY` (free at [build.nvidia.com](https://build.nvidia.com))
- Internet access for HN search + NIM API

## Project Structure

```
LeadForge/
├── leadforge.py          # Main pipeline
├── leadforge_report.py   # Report generator (MD/HTML/console)
├── requirements.txt      # Dependencies
├── .env.example          # Environment template
├── LICENSE               # MIT
└── examples/             # Usage examples
```

## ColdEmailOS Integration

LeadForge pairs with **[ColdEmailOS](https://github.com/HCTDIP/ColdEmailOS)** for zero-cost email delivery:
- Brevo shared domains (`@sendinblue.com`) — instant, zero DNS
- Drip campaigns, suppression sync, webhook automation
- Deploy to Railway/Render/Fly.io in minutes

## Vietnam AI Hackathon 2024 Submission

- **Track**: Solana — AI + Web3
- **Demo video**: 30s, `vietnam-demo-final.mp4`
- **Pitch deck**: `leadforge-report-20260923.html`
- **Repo**: `github.com/HCTDIP/LeadForge`
- **Deadline**: Oct 13, 2024

## License

MIT — see [LICENSE](LICENSE)

## Contributing

Issues and PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

**Built in public by [HCTDIP](https://github.com/HCTDIP)** — Star ⭐ if this saves you time.