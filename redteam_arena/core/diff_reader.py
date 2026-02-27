"""
Diff-only file reader -- reads only files changed in git diff.
Used for faster CI runs that focus on new/modified code.
"""

from __future__ import annotations

import asyncio
import os

from redteam_arena.types import Err, FileEntry, Ok, Result


async def read_diff_files(
    target_dir: str,
    *,
    base: str = "HEAD~1",
) -> Result[list[FileEntry], Exception]:
    """Read only the files changed since `base` commit/branch."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "diff", "--name-only", "--diff-filter=ACMR", base,
            cwd=target_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            err_msg = stderr.decode("utf-8", errors="replace").strip()
            return Err(error=Exception(f"git diff failed: {err_msg}"))

        changed_paths = [
            line.strip()
            for line in stdout.decode("utf-8").strip().split("\n")
            if line.strip()
        ]

        if not changed_paths:
            return Ok(value=[])

        files: list[FileEntry] = []
        for file_path in changed_paths:
            full_path = os.path.join(target_dir, file_path)
            try:
                with open(full_path, encoding="utf-8") as f:
                    content = f.read()
                files.append(FileEntry(path=file_path, content=content))
            except (OSError, UnicodeDecodeError):
                continue

        return Ok(value=files)

    except Exception as exc:
        return Err(
            error=Exception(f"Failed to get diff: {exc}")
        )
