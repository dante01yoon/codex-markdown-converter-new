"""Markdown to HTML conversion utility with sanitization and CLI support."""
from __future__ import annotations

import argparse
import html
import json
import logging
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


class ConversionError(Exception):
    """Raised when conversion fails for expected reasons."""


class DependencyError(ConversionError):
    """Raised when an optional dependency is missing."""


DEFAULT_EMBEDDED_CSS = textwrap.dedent(
    """
.markdown-body {
  box-sizing: border-box;
  margin: 0 auto;
  max-width: 860px;
  padding: 1.5rem;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  line-height: 1.6;
  color: #24292f;
  background-color: #ffffff;
}
.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {
  font-weight: 600;
  line-height: 1.25;
  margin-top: 1.8rem;
  margin-bottom: 0.8rem;
}
.markdown-body h1,
.markdown-body h2 {
  border-bottom: 1px solid #d0d7de;
  padding-bottom: 0.3rem;
}
.markdown-body p {
  margin: 0.8rem 0;
}
.markdown-body a {
  color: #0969da;
  text-decoration: none;
}
.markdown-body a:hover {
  text-decoration: underline;
}
.markdown-body code {
  font-size: 0.95em;
  background-color: rgba(175, 184, 193, 0.2);
  padding: 0.15em 0.35em;
  border-radius: 6px;
}
.markdown-body pre {
  background-color: #f6f8fa;
  padding: 1rem;
  overflow: auto;
  border-radius: 6px;
}
.markdown-body pre code {
  background: transparent;
  padding: 0;
}
.markdown-body blockquote {
  padding: 0 1rem;
  border-left: 0.25rem solid #d0d7de;
  color: #57606a;
  margin: 1rem 0;
}
.markdown-body ul,
.markdown-body ol {
  padding-left: 2rem;
  margin: 0.8rem 0;
}
.markdown-body li {
  margin: 0.3rem 0;
}
.markdown-body table {
  border-collapse: collapse;
  width: 100%;
  margin: 1rem 0;
}
.markdown-body table th,
.markdown-body table td {
  border: 1px solid #d0d7de;
  padding: 0.6rem 0.8rem;
}
.markdown-body table th {
  background-color: #f6f8fa;
  font-weight: 600;
}
.markdown-body img {
  max-width: 100%;
  height: auto;
  border-radius: 6px;
}
.markdown-body hr {
  border: 0;
  height: 1px;
  background: #d0d7de;
  margin: 2rem 0;
}
"""
).strip()


@dataclass
class SanitizationResult:
    html: str
    modified: bool


@dataclass
class SanitizationPolicy:
    allowed_tags: Iterable[str]
    allowed_attributes: Dict[str, Iterable[str]]
    allowed_protocols: Iterable[str]
    strip_disallowed: bool = False

    @classmethod
    def default(cls) -> "SanitizationPolicy":
        return cls(
            allowed_tags=(
                "a",
                "abbr",
                "acronym",
                "b",
                "blockquote",
                "code",
                "em",
                "i",
                "li",
                "ol",
                "ul",
                "p",
                "pre",
                "strong",
                "table",
                "thead",
                "tbody",
                "tr",
                "th",
                "td",
                "hr",
                "img",
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "h6",
                "sup",
                "sub",
                "del",
                "ins",
                "span",
                "kbd",
            ),
            allowed_attributes={
                "a": ("href", "title", "name"),
                "img": ("src", "alt", "title", "width", "height"),
                "th": ("scope",),
                "code": ("class",),
                "pre": ("class",),
                "*": ("class", "id", "lang"),
            },
            allowed_protocols=("http", "https", "mailto", "tel", "data"),
            strip_disallowed=False,
        )

    def sanitize(self, html: str) -> SanitizationResult:
        try:
            import bleach  # type: ignore
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise DependencyError(
                "bleach package is required for sanitization. Install with 'pip install bleach'."
            ) from exc

        cleaner = bleach.Cleaner(
            tags=list(self.allowed_tags),
            attributes={k: list(v) for k, v in self.allowed_attributes.items()},
            protocols=list(self.allowed_protocols),
            strip=self.strip_disallowed,
        )
        cleaned = cleaner.clean(html)
        return SanitizationResult(html=cleaned, modified=cleaned != html)


@dataclass
class ConverterConfig:
    extensions: List[str] = field(
        default_factory=lambda: [
            "extra",
            "codehilite",
            "sane_lists",
            "smarty",
            "toc",
        ]
    )
    extension_configs: Dict[str, Dict[str, Any]] = field(
        default_factory=lambda: {
            "codehilite": {
                "guess_lang": False,
                "linenums": False,
                "noclasses": False,
            },
            "toc": {"permalink": False},
        }
    )
    output_format: str = "html5"
    sanitize_html: bool = True
    fail_on_unsafe_html: bool = False
    sanitization_policy: SanitizationPolicy = field(default_factory=SanitizationPolicy.default)
    wrap_html: bool = True
    container_class: str = "markdown-body"
    embed_css: bool = True
    css_text: Optional[str] = None


class MarkdownConverter:
    """Markdown to HTML converter with configurable sanitization."""

    def __init__(self, config: Optional[ConverterConfig] = None) -> None:
        self.config = config or ConverterConfig()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._markdown = self._build_markdown()

    def _build_markdown(self):
        try:
            import markdown  # type: ignore
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise DependencyError(
                "markdown package is required. Install with 'pip install markdown'."
            ) from exc

        return markdown.Markdown(
            extensions=self.config.extensions,
            extension_configs=self.config.extension_configs,
            output_format=self.config.output_format,
        )

    def convert(self, markdown_text: str, *, source: Optional[Path] = None) -> str:
        if not markdown_text:
            self._logger.debug("Received empty markdown text for conversion.")
        try:
            html = self._markdown.convert(markdown_text)
        except Exception as exc:
            raise ConversionError(f"Markdown parsing failed: {exc}") from exc
        finally:
            self._markdown.reset()

        self._logger.debug("Conversion produced %d characters of HTML.", len(html))

        if self.config.sanitize_html:
            result = self.config.sanitization_policy.sanitize(html)
            if result.modified:
                msg = "Sanitization adjusted HTML output"
                if source:
                    msg += f" for source {source}"
                self._logger.warning(msg)
                if self.config.fail_on_unsafe_html:
                    raise ConversionError("Unsafe HTML detected during sanitization.")
            html_output = result.html
        else:
            html_output = html

        return self._apply_presentation(html_output)

    def convert_file(self, path: Path, *, encoding: str = "utf-8") -> str:
        try:
            markdown_text = path.read_text(encoding=encoding)
        except OSError as exc:
            raise ConversionError(f"Failed to read {path}: {exc}") from exc
        return self.convert(markdown_text, source=path)

    def convert_stream(self, stream: Any, *, encoding: str = "utf-8") -> str:
        try:
            data = stream.read()
        except OSError as exc:
            raise ConversionError(f"Failed to read stream: {exc}") from exc
        if isinstance(data, bytes):
            data = data.decode(encoding)
        return self.convert(str(data))

    def _apply_presentation(self, html_fragment: str) -> str:
        fragment = html_fragment
        if self.config.wrap_html:
            fragment = (
                f'<div class="{html.escape(self.config.container_class, quote=True)}">\n'
                f"{fragment}\n"
                "</div>"
            )
        if self.config.embed_css:
            css_text = (self.config.css_text or DEFAULT_EMBEDDED_CSS).strip()
            fragment = f"<style>\n{css_text}\n</style>\n{fragment}"
        return fragment


def _load_extension_config(path: Path) -> Dict[str, Dict[str, Any]]:
    try:
        raw = path.read_text(encoding="utf-8")
        config = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise ConversionError(f"Failed to load extension config: {exc}") from exc
    if not isinstance(config, dict):
        raise ConversionError("Extension config must be a JSON object")
    cleaned: Dict[str, Dict[str, Any]] = {}
    for key, value in config.items():
        if not isinstance(value, dict):
            raise ConversionError("Extension config values must be objects")
        cleaned[key] = value
    return cleaned


def _load_css_text(path: Path) -> str:
    try:
        css = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConversionError(f"Failed to load CSS file: {exc}") from exc
    return css.strip()


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert Markdown input to sanitized HTML fragments.",
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="Path to Markdown file. Use '-' or omit for STDIN.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file path. Defaults to STDOUT.",
    )
    parser.add_argument(
        "--input-encoding",
        default="utf-8",
        help="Text encoding for reading input (default: utf-8).",
    )
    parser.add_argument(
        "--output-encoding",
        default="utf-8",
        help="Text encoding for writing output (default: utf-8).",
    )
    parser.add_argument(
        "--no-sanitize",
        action="store_true",
        help="Disable HTML sanitization (not recommended).",
    )
    parser.add_argument(
        "--fail-on-unsafe",
        action="store_true",
        help="Exit with error if sanitization would modify the output.",
    )
    parser.add_argument(
        "--no-wrap",
        action="store_true",
        help="Do not wrap output in the styled container element.",
    )
    parser.add_argument(
        "--container-class",
        help="CSS class to apply to the wrapping container (default: markdown-body).",
    )
    parser.add_argument(
        "--no-css",
        action="store_true",
        help="Disable embedding of the default Markdown CSS theme.",
    )
    parser.add_argument(
        "--css-file",
        type=Path,
        help="Path to a CSS file to embed instead of the default theme.",
    )
    parser.add_argument(
        "--extensions",
        nargs="*",
        default=None,
        help="Additional Markdown extensions to enable.",
    )
    parser.add_argument(
        "--extension-config",
        type=Path,
        help="Path to JSON file providing markdown extension configuration overrides.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
        help="Logging verbosity (default: INFO).",
    )
    return parser


def run_cli(argv: Optional[List[str]] = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    if args.no_css and args.css_file:
        parser.error("--no-css cannot be used with --css-file")

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    extensions = args.extensions
    extension_configs = None
    if args.extension_config:
        extension_configs = _load_extension_config(args.extension_config)

    config = ConverterConfig()
    if extensions:
        config.extensions.extend(ext for ext in extensions if ext not in config.extensions)
    if extension_configs:
        config.extension_configs.update(extension_configs)

    config.sanitize_html = not args.no_sanitize
    config.fail_on_unsafe_html = bool(args.fail_on_unsafe)
    config.wrap_html = not args.no_wrap
    if args.container_class:
        config.container_class = args.container_class
    if args.no_css:
        config.embed_css = False
        config.css_text = None
    else:
        config.embed_css = True
        if args.css_file:
            config.css_text = _load_css_text(args.css_file)

    converter = MarkdownConverter(config=config)

    try:
        if args.input == "-":
            html = converter.convert_stream(sys.stdin.buffer if hasattr(sys.stdin, "buffer") else sys.stdin)
        else:
            html = converter.convert_file(Path(args.input), encoding=args.input_encoding)
    except ConversionError as exc:
        logging.getLogger("MarkdownConverter").error(str(exc))
        return 1

    if args.output:
        try:
            Path(args.output).write_text(html, encoding=args.output_encoding)
        except OSError as exc:
            logging.getLogger("MarkdownConverter").error("Failed to write output: %s", exc)
            return 1
    else:
        if isinstance(html, str):
            sys.stdout.write(html)
            if not html.endswith("\n"):
                sys.stdout.write("\n")
        else:  # pragma: no cover - defensive branch
            sys.stdout.buffer.write(html)

    return 0


def main() -> None:
    sys.exit(run_cli())


if __name__ == "__main__":
    main()
