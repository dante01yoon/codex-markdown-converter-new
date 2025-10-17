# codex-markdown-converter-new

Utility for converting Markdown sources into sanitized HTML fragments suitable for
embedding. The converter ships with a CLI that exposes the most common
configuration options, including optional math rendering support.

## Installation

Install the core dependencies:

```bash
pip install markdown bleach
```

To enable the math rendering extension, install the optional dependency as well:

```bash
pip install pymdown-extensions
```

## CLI usage

Run the converter against a Markdown file (or STDIN when no file is provided):

```bash
python -m converter README.md
```

Write the HTML output to a file:

```bash
python -m converter docs/example.md -o example.html
```

Enable math-friendly Markdown processing (requires `pymdown-extensions`):

```bash
python -m converter docs/math.md --enable-math
```

Use `python -m converter --help` to review the full list of supported options.
