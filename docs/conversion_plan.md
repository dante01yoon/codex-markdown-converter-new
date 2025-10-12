# Markdown to HTML Converter Draft Plan

## Goals and Scope
- Produce deterministic HTML5 output from Markdown inputs using Python 3.11 runtime.
- Support core CommonMark syntax plus GitHub-style fenced code blocks, tables, task lists, footnotes, definition lists, and automatic linking.
- Generate sanitized HTML suitable for embedding in web surfaces; avoid inline scripting unless explicitly allowed.
- Provide CLI and importable API entry points for batch conversions and integration in pipelines.
- Offer opinionated default presentation (wrapper + CSS theme) while allowing operators to opt out or supply custom styles.

## Standards and Compatibility
- Target HTML5; enforce UTF-8 encoding on inputs and outputs.
- Leverage `python-markdown` (a.k.a. `Markdown`) with extensions: `extra`, `codehilite`, `toc`, `sane_lists`, `smarty`.
- Post-process with `bleach` 6.x to strip disallowed tags/attributes while preserving semantic structures such as `<pre>`, `<code>`, `<table>`, `<a>`, `<img>`.
- Ensure compatibility with downstream templating (no inline `<html>/<body>` wrappers, only fragment output).

## Performance Expectations
- Handle files up to ~5 MB per invocation with latency under a few hundred ms on modern hardware.
- Provide stateless function for concurrency; CLI supports streaming via `stdin`/`stdout` with buffered reads.
- Optimize extension configuration (disable slow tree processors) and allow toggling syntax highlight to trade runtime vs fidelity.

## Deployment Environment
- Python 3.11 (CPython) on macOS/Linux.
- Required libraries: `markdown>=3.5`, `bleach>=6.0`, `pygments>=2.15` (for code highlighting).
- Standard library usage: `pathlib`, `argparse`, `logging`, `dataclasses`, `typing`.
- No external network calls at runtime; dependencies installed via offline wheels or internal artifact store per security policy.

## Sanitization and Security
- Enforce allow-list sanitization with `bleach.clean` after conversion.
- Provide configuration hooks for custom tag/attribute policies.
- Reject disallowed embedded HTML with configurable strictness (`--fail-on-unsafe`).
- Log sanitization actions and emit warnings when stripping content.

## Error Handling and Observability
- Graceful handling of I/O errors, Markdown parsing issues, and sanitization conflicts.
- Use structured logging (JSON-ready key/value) at INFO level with optional verbose flag.
- Exit codes: `0` success, `1` recoverable/user error, `2` internal failure.

## Testing Strategy
- Unit tests for converter API covering: headings/lists/tables, HTML sanitization, footnotes, unicode handling.
- Property tests for idempotency (re-convert same input stable).
- Golden-file regression tests using known Markdown -> HTML fixtures (few-shot example included).
- CLI integration tests ensuring argument parsing and exit codes.

## Extensibility and Maintenance
- Config dataclass capturing extensions, output options, sanitization policy.
- Plugin registration for custom Markdown extensions (dynamic import by dotted path).
- Support locale-specific tweaks (e.g., code highlighting language mapping) via config file.
- Document usage in `README.md` with examples and troubleshooting.
- Allow overriding CSS theme or wrapper class without editing code; plan for future theming options and asset bundling.

## Deliverables & Format
- `converter.py` module exposing `MarkdownConverter` class and CLI `main()`.
- `docs/` directory hosts this plan and future design notes.
- Final response to include: design overview, implementation summary with file references, test recommendations, deployment notes.

## Representative I/O & Whitespace Rules
- Baseline sample aligns with provided few-shot: headings, emphasis, lists, block quotes, inline and fenced code render to HTML5 fragments with semantic tags and `language-` classes.
- Exceptional case: malicious `<script>alert(1)</script>` will trigger sanitization; with `--fail-on-unsafe` the run exits non-zero, otherwise the tag is stripped while preserving surrounding text.
- Default output wraps the fragment in `<div class="markdown-body">` and prepends a `<style>` block containing the bundled theme; `--no-wrap` or `--no-css` disable this. Whitespace policy: preserve blank lines between block elements from `python-markdown`; CLI appends a trailing newline to STDOUT when missing for POSIX-friendly output.
