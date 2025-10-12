# Deployment and Integration Notes

- **Runtime**: Python 3.11 with virtual environment recommended (`python3 -m venv .venv`).
- **Dependencies**: install `markdown>=3.5`, `bleach>=6.0`, `pygments>=2.15`. Pin versions in `requirements.txt` for reproducibility.
- **Packaging**: convert script to console entry point via `setuptools` or `pipx` for distribution. Include optional extras for sanitization if policy differs.
- **Security**: run conversions in sandboxed process when handling untrusted Markdown. Audit sanitization policy before relaxing defaults.
- **Integration**: embed via Python API (`from converter import MarkdownConverter`) or call CLI as subprocess. Use config overrides for custom extension sets.
- **Styling**: default build embeds lightweight theme CSS; operators can disable it (`--no-css`) or supply curated stylesheets with `--css-file` for brand alignment.
- **Monitoring**: forward converter logs to central logging solution for tracking sanitization warnings and conversion failures.
