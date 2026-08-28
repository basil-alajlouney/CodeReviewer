#!/usr/bin/env python3
"""
review.py, CLI code reviewer that checks a file or directory against your
team's guidelines + examples, using the persona in persona.md as the system
prompt. Runs against a local Ollama server, no API key required.

Usage:
    ollama pull codellama:13b        # or any model you prefer
    python review.py --references ./refs --target ./src/app.py
    python review.py --references ./refs --target ./src --fix
    python review.py --references ./refs --target ./src --fix --output review.md
    python review.py --references ./refs --target ./src --model llama3.1 --host http://localhost:11434

Expected --references directory layout:
    refs/
      guidelines.md
      examples/
        anything.md / .py / .js / ...   (before/after snippets, any text files)
"""

import argparse
import re
import sys
from pathlib import Path

try:
    import ollama
except ImportError:
    sys.exit(
        "Missing dependency: ollama\n"
        "Install it with:  pip install ollama\n"
        "And make sure the Ollama server is running (https://ollama.com)."
    )

SCRIPT_DIR = Path(__file__).resolve().parent
PERSONA_PATH = SCRIPT_DIR / "persona.md"

DEFAULT_MODEL = "codellama:13b"
DEFAULT_HOST = "http://localhost:11434"

# Files/dirs to skip when walking a target directory or examples/ dir.
SKIP_DIR_NAMES = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".idea", ".vscode",
}
SKIP_FILE_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".pdf",
    ".lock", ".pyc", ".zip", ".tar", ".gz", ".woff", ".woff2",
}


def is_reviewable_file(path: Path) -> bool:
    if path.name.startswith("."):
        return False
    if path.suffix.lower() in SKIP_FILE_SUFFIXES:
        return False
    return path.is_file()


def collect_files(root: Path) -> list[Path]:
    """Return a sorted list of reviewable files under a file or directory path."""
    if root.is_file():
        return [root] if is_reviewable_file(root) else []

    files = []
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if is_reviewable_file(path):
            files.append(path)
    return files


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def render_file_block(path: Path, relative_to: Path) -> str:
    try:
        rel = path.relative_to(relative_to)
    except ValueError:
        rel = path.name
    return f"### {rel}\n```\n{read_text(path)}\n```"


def load_guidelines(references_dir: Path) -> str:
    guidelines_path = references_dir / "guidelines.md"
    if not guidelines_path.exists():
        sys.exit(f"Error: no guidelines.md found in {references_dir}")
    return read_text(guidelines_path)


def load_examples(references_dir: Path) -> str:
    examples_dir = references_dir / "examples"
    if not examples_dir.exists():
        return "(no examples/ directory provided)"

    files = collect_files(examples_dir)
    if not files:
        return "(examples/ directory is empty)"

    blocks = [render_file_block(f, examples_dir) for f in files]
    return "\n\n".join(blocks)


def load_target(target_path: Path) -> str:
    files = collect_files(target_path)
    if not files:
        sys.exit(f"Error: no reviewable files found at {target_path}")

    base = target_path if target_path.is_dir() else target_path.parent
    blocks = [render_file_block(f, base) for f in files]
    return "\n\n".join(blocks)


def build_user_message(guidelines: str, examples: str, code: str) -> str:
    return (
        f"## Guidelines\n{guidelines}\n\n"
        f"## Examples\n{examples}\n\n"
        f"## Code to review\n{code}"
    )


def run_review(client: "ollama.Client", model: str, system_prompt: str,
               user_message: str) -> tuple[str, list]:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    response = client.chat(model=model, messages=messages)
    review_text = response["message"]["content"]
    history = messages + [{"role": "assistant", "content": review_text}]
    return review_text, history


FILE_BLOCK_RE = re.compile(
    r"<<<FILE:\s*(?P<path>.+?)\s*>>>\n(?P<body>.*?)\n<<<END FILE>>>",
    re.DOTALL,
)
FENCE_RE = re.compile(r"^```[^\n]*\n(?P<code>.*?)\n```$", re.DOTALL)


def extract_corrected_files(fix_text: str) -> list[tuple[str, str]]:
    """Parse <<<FILE: path>>> ... <<<END FILE>>> blocks out of the model's
    correction-mode response. Strips a surrounding fenced code block if the
    model included one. Returns a list of (relative_path, content)."""
    results = []
    for match in FILE_BLOCK_RE.finditer(fix_text):
        rel_path = match.group("path").strip()
        body = match.group("body").strip("\n")
        fence_match = FENCE_RE.match(body.strip())
        if fence_match:
            body = fence_match.group("code")
        results.append((rel_path, body))
    return results


def write_corrected_files(files: list[tuple[str, str]], output_dir: Path) -> list[Path]:
    written = []
    for rel_path, content in files:
        dest = output_dir / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content + "\n", encoding="utf-8")
        written.append(dest)
    return written


def run_fix(client: "ollama.Client", model: str, history: list) -> str:
    history.append({
        "role": "user",
        "content": (
            "Produce the corrected version now, following the Correction Mode "
            "rules in your instructions."
        ),
    })
    response = client.chat(model=model, messages=history)
    return response["message"]["content"]


def main():
    parser = argparse.ArgumentParser(description="AI code reviewer CLI (Ollama-backed)")
    parser.add_argument(
        "--references", required=True, type=Path, default=SCRIPT_DIR / "refs",
        help="Directory containing guidelines.md and an examples/ subfolder",
    )
    parser.add_argument(
        "--target", required=True, type=Path,
        help="File or directory to review",
    )
    parser.add_argument(
        "--fix", action="store_true",
        help="Also request a corrected version after the review",
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help="Write the review report to a file instead of only printing to stdout",
    )
    parser.add_argument(
        "--fix-output", type=Path, default=Path("corrected"),
        help="Directory to write corrected files into when --fix is used "
             "(default: ./corrected)",
    )
    parser.add_argument(
        "--model", default=DEFAULT_MODEL,
        help=f"Ollama model tag to use (default: {DEFAULT_MODEL}). "
             f"Must already be pulled, run `ollama pull <model>` first.",
    )
    parser.add_argument(
        "--host", default=DEFAULT_HOST,
        help=f"Ollama server URL (default: {DEFAULT_HOST})",
    )
    args = parser.parse_args()

    references_dir = args.references.resolve()
    target_path = args.target.resolve()

    if not references_dir.is_dir():
        sys.exit(f"Error: --references path is not a directory: {references_dir}")
    if not target_path.exists():
        sys.exit(f"Error: --target path does not exist: {target_path}")
    if not PERSONA_PATH.exists():
        sys.exit(f"Error: persona.md not found next to this script ({PERSONA_PATH})")

    system_prompt = read_text(PERSONA_PATH)
    guidelines = load_guidelines(references_dir)
    examples = load_examples(references_dir)
    code = load_target(target_path)
    user_message = build_user_message(guidelines, examples, code)

    client = ollama.Client(host=args.host)

    try:
        client.show(args.model)
    except Exception:
        sys.exit(
            f"Error: model '{args.model}' isn't available on {args.host}.\n"
            f"Pull it first with:  ollama pull {args.model}"
        )

    print(f"Reviewing {target_path} against {references_dir} using '{args.model}'...\n",
          file=sys.stderr)
    review_text, history = run_review(client, args.model, system_prompt, user_message)

    print("## Review\n")
    print(review_text)

    report_sections = [review_text]

    if args.fix:
        print("\nDrafting corrected version...\n", file=sys.stderr)
        fix_text = run_fix(client, args.model, history)

        corrected_files = extract_corrected_files(fix_text)
        if not corrected_files:
            print(
                "Warning: model response didn't contain any parseable "
                "<<<FILE:...>>> blocks, nothing written to disk. Raw "
                "response is still included below/in --output.",
                file=sys.stderr,
            )
        else:
            written = write_corrected_files(corrected_files, args.fix_output)
            print(f"\n## Corrected Code (written to {args.fix_output}/)\n")
            for path in written:
                print(f"  - {path}")

        report_sections.append("\n\n---\n\n## Correction Response\n\n" + fix_text)

    full_output = "".join(report_sections)

    if args.output:
        args.output.write_text(full_output, encoding="utf-8")
        print(f"\nReport saved to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
