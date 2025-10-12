# Testing and Validation Outline

1. **Unit Tests**
   - `test_headings_and_lists`: ensure headings, emphasis, lists render as expected and match golden HTML snapshots.
   - `test_code_blocks_with_highlighting`: verify fenced code blocks include `language-` classes and preserve indentation.
   - `test_tables_and_footnotes`: cover `markdown.extensions.extra` features such as tables and footnotes.
   - `test_sanitization_strips_scripts`: inject malicious `<script>` tag and assert `ConversionError` when `fail_on_unsafe_html=True` and sanitized output otherwise.
   - `test_unicode_handling`: confirm UTF-8 inputs with CJK characters or emoji survive conversion.
   - `test_presentation_layer`: assert wrapper div and default CSS appear by default, and that `--no-wrap` / `--no-css` disable them.

2. **Integration / CLI Tests**
   - `test_cli_reads_from_stdin`: simulate input via `subprocess` or `capsys` to confirm STDIN support and newline behavior.
   - `test_cli_writes_file`: ensure `--output` writes to disk with the requested encoding and respects sanitization flags.
   - `test_cli_extension_override`: supply JSON config overriding extension settings and assert they apply.
   - `test_cli_custom_css`: provide `--css-file` with bespoke styles and ensure they are embedded verbatim.

3. **Regression / Golden Tests**
   - Maintain fixtures for representative Markdown documents (basic content, docs with tables, nested lists) and compare outputs against curated HTML.
   - Include the provided few-shot sample as part of the regression suite.

4. **Performance Checks**
   - Benchmark conversion on large (~1 MB) Markdown files within acceptable time (<500 ms) using `pytest-benchmark` or timing harness.

5. **Observability Validation**
   - Use logging capture to ensure warnings emit when sanitization modifies HTML and remain silent when no change occurs.
