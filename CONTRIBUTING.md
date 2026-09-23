# Contributing to LeadForge

Thank you for your interest in contributing! LeadForge is a small, focused project — we value quality over quantity.

## How to Contribute

### 1. Found a Bug?
- Open an issue with: steps to reproduce, expected vs actual behavior, Python version, OS
- Include error traceback if applicable

### 2. Have a Feature Request?
- Open an issue describing the use case and proposed solution
- Keep scope small — we prefer focused additions

### 3. Want to Submit a PR?
1. Fork the repo
2. Create a branch: `git checkout -b feat/your-feature`
3. Make changes with clear, focused commits
4. Run tests: `python3 leadforge.py "test query" --max-leads 1`
5. Push and open PR

## Code Style

- Python 3.10+ type hints where practical
- No external dependencies beyond `requests` (stdlib preferred)
- Logging over print statements
- Docstrings for public functions

## Testing

```bash
# Quick smoke test
export NVIDIA_API_KEY="your-key"
python3 leadforge.py "workflow automation" --max-leads 1

# Report generation
python3 leadforge.py "test" --max-leads 1 --output test_results.json
python3 leadforge_report.py test_results.json --format console
python3 leadforge_report.py test_results.json --format html --output test_report.html
```

## Areas We Welcome Contributions

- Additional lead sources (GitHub Trending, Reddit, Twitter/X)
- More NIM model support
- Better fallback templates
- Report formatting improvements
- CI/CD pipeline
- Documentation

## What We Don't Need

- Heavy frameworks (FastAPI, Django, etc.) — this is a CLI tool
- Database dependencies — keep it file-based
- Paid API integrations — free tiers only

## Code of Conduct

Be respectful. This is a small project by indie builders for indie builders.

## License

By contributing, you agree your contributions will be licensed under the MIT License.