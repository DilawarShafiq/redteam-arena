"""
Codebase file reader -- recursively reads source files with filtering.
Respects extension filters, directory exclusions, and size caps.
"""

from __future__ import annotations

import os

from redteam_arena.types import Err, FileEntry, Ok, Result, ScanScope

SOURCE_EXTENSIONS: set[str] = {
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".py", ".pyw",
    ".java", ".kt", ".kts",
    ".go",
    ".rb", ".erb",
    ".php",
    ".cs",
    ".rs",
    ".c", ".cpp", ".h", ".hpp",
    ".swift",
    ".scala",
    ".sql",
    ".html", ".htm", ".vue", ".svelte",
    ".css", ".scss", ".less",
    ".yaml", ".yml", ".toml", ".json", ".xml",
    ".sh", ".bash", ".zsh",
    ".env", ".env.example",
    ".dockerfile",
    ".tf",
}

# Files matched by exact name rather than extension. os.path.splitext returns an
# empty extension for extensionless names ("Dockerfile") and for bare dotfiles
# (".env" -> (".env", "")), so neither is reachable via SOURCE_EXTENSIONS.
SOURCE_FILENAMES: set[str] = {
    "dockerfile", "containerfile",
    ".env", ".env.example", ".env.local", ".env.production",
    "makefile", "jenkinsfile", "vagrantfile", "procfile",
    ".htaccess", ".npmrc", ".dockerignore",
}

EXCLUDED_DIRS: set[str] = {
    "node_modules", ".git", "dist", "build", "vendor",
    ".next", ".nuxt", "__pycache__", ".venv", "venv",
    "target", ".gradle", ".idea", ".vscode",
    "coverage", ".specify", ".claude", "specs", "history",
}

EXCLUDED_FILES: set[str] = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "bun.lockb", "Cargo.lock", "Gemfile.lock",
    "poetry.lock", "composer.lock",
}

MAX_FILE_SIZE = 64 * 1024  # 64KB per file
MAX_TOTAL_SIZE = 100 * 1024  # 100KB total context budget


async def read_codebase(
    target_dir: str,
    *,
    max_file_size: int = MAX_FILE_SIZE,
    max_total_size: int = MAX_TOTAL_SIZE,
    scope: ScanScope | None = None,
) -> Result[list[FileEntry], Exception]:
    """Recursively read source files from target_dir.

    Pass a ScanScope to record what was read and what was skipped; the reader
    stops at max_total_size, so callers that report results to a user should
    always pass one and disclose the coverage.
    """
    if not os.path.isdir(target_dir):
        return Err(error=Exception(f"Directory not found: {target_dir}"))

    files: list[FileEntry] = []
    scope = scope if scope is not None else ScanScope()
    scope.max_total_size = max_total_size

    try:
        _walk_directory(
            root_dir=target_dir,
            current_dir=target_dir,
            files=files,
            total_size_ref=[0],
            max_file_size=max_file_size,
            max_total_size=max_total_size,
            scope=scope,
        )
        scope.files_read = len(files)
        return Ok(value=files)
    except Exception as exc:
        return Err(error=Exception(f"Failed to read codebase: {exc}"))


def _is_source_file(entry_name: str) -> bool:
    """Return True if a filename should be read, by exact name or extension."""
    name = entry_name.lower()
    if name in SOURCE_FILENAMES:
        return True
    # "Dockerfile.prod", ".env.staging" and friends.
    if any(name.startswith(f"{known}.") for known in ("dockerfile", ".env")):
        return True
    return os.path.splitext(name)[1] in SOURCE_EXTENSIONS


def _walk_directory(
    root_dir: str,
    current_dir: str,
    files: list[FileEntry],
    total_size_ref: list[int],
    max_file_size: int,
    max_total_size: int,
    scope: ScanScope,
) -> None:
    """Walk directory tree collecting source files."""
    try:
        entries = sorted(os.listdir(current_dir))
    except OSError:
        return

    for entry_name in entries:
        if total_size_ref[0] >= max_total_size:
            scope.budget_exhausted = True
            break

        full_path = os.path.join(current_dir, entry_name)

        if os.path.isdir(full_path):
            if entry_name in EXCLUDED_DIRS:
                continue
            _walk_directory(
                root_dir, full_path, files, total_size_ref,
                max_file_size, max_total_size, scope,
            )
        elif os.path.isfile(full_path):
            if entry_name in EXCLUDED_FILES:
                continue

            if not _is_source_file(entry_name):
                continue

            relative_path = os.path.relpath(full_path, root_dir)
            try:
                file_size = os.path.getsize(full_path)
                if file_size > max_file_size:
                    scope.skipped_too_large.append(relative_path)
                    continue
                if total_size_ref[0] + file_size > max_total_size:
                    scope.skipped_over_budget.append(relative_path)
                    continue

                with open(full_path, encoding="utf-8") as f:
                    content = f.read()

                files.append(FileEntry(path=relative_path, content=content))
                total_size_ref[0] += file_size
                scope.bytes_read = total_size_ref[0]
            except (OSError, UnicodeDecodeError):
                # Skip unreadable files
                continue


def format_files_for_prompt(files: list[FileEntry]) -> str:
    """Format file entries into a prompt-friendly string."""
    return "\n\n".join(f"=== {f.path} ===\n{f.content}" for f in files)


def has_source_files(files: list[FileEntry]) -> bool:
    """Return True if there is at least one source file."""
    return len(files) > 0
