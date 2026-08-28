# code-reviewer-cli

A simple command-line tool that reviews a file or directory against your
team's guidelines and examples, using a local model via **Ollama**. No API
key, nothing leaves your machine.

## Setup

1. Install [Ollama](https://ollama.com) and make sure it's running.
2. Pull a model — pick something decent at code:
   ```bash
   ollama pull qwen2.5-coder
   # or: ollama pull codellama   /   ollama pull llama3.1   /   ollama pull deepseek-coder-v2
   ```
3. Install the Python dependency:
   ```bash
   pip install -r requirements.txt
   ```

## Folder layout expected for `--references`

```
refs/
  guidelines.md          # required — your team's coding guidelines
  examples/               # optional — before/after snippets, any text files
    naming.md
    error_handling.py
    ...
```

## Usage

Review a single file:
```bash
python review.py --references ./refs --target ./src/app.py
```

Review an entire directory:
```bash
python review.py --references ./refs --target ./src
```

Review and also generate a corrected version:
```bash
python review.py --references ./refs --target ./src --fix
```
Corrected files are written as real, ready-to-use files under `./corrected/`
(mirroring the original relative paths) — not just printed as text you'd
have to copy out by hand.

Choose where corrected files get written:
```bash
python review.py --references ./refs --target ./src --fix --fix-output ./out
```

Save the full text report (review + changelog) to a file:
```bash
python review.py --references ./refs --target ./src --fix --output review.md
```

Use a different model:
```bash
python review.py --references ./refs --target ./src --model codellama
```

Point at a remote/non-default Ollama server:
```bash
python review.py --references ./refs --target ./src --host http://192.168.1.50:11434
```

## How it works

1. `persona.md` is sent as the system message — it defines the reviewer's
   role, process, severity levels, and output format.
2. The script reads `guidelines.md`, everything under `examples/`, and every
   reviewable file under `--target`, and bundles them into one user message.
3. The model reviews the code and returns findings citing specific guideline
   sections.
4. With `--fix`, a follow-up turn asks the model to produce a corrected
   version that resolves the findings without changing behavior. The model
   is required to return each corrected file in a strict, parseable block:
   ```
   <<<FILE: relative/path.py>>>
   ```python
   [full corrected file]
   ```
   <<<END FILE>>>
   ```
   The script extracts these blocks and writes real files to `--fix-output`
   (default `./corrected/`), preserving relative paths — so you get usable
   files, not text to copy-paste out of a report. A `## Changelog` explaining
   each change stays in the printed/saved report, separate from the code.
5. Before running, the script checks the requested model is already pulled
   (`ollama pull <model>`) and fails fast with a clear message if not.

## Notes

- Binary/asset files (images, PDFs, lockfiles, etc.) and common noise
  directories (`.git`, `node_modules`, `__pycache__`, `dist`, `build`, ...)
  are skipped automatically when walking a directory.
- Model quality varies a lot more here than with a hosted frontier model —
  a small local model may under-cite or miss subtler guideline violations.
  `qwen2.5-coder` or `deepseek-coder-v2` tend to hold up best for this kind
  of structured, citation-heavy review task.
- For large codebases, point `--target` at one file or module at a time —
  everything gets bundled into a single request, and local models generally
  have smaller context windows than hosted ones, so this matters more here.
- No `ANTHROPIC_API_KEY` or any API key is needed — everything runs against
  your local Ollama server (default `http://localhost:11434`).
