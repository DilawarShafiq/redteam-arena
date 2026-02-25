"""Tests for redteam_arena.core.file_reader."""

from __future__ import annotations

import os
import tempfile
import shutil

import pytest

from redteam_arena.core.file_reader import read_codebase, format_files_for_prompt, has_source_files
from redteam_arena.types import FileEntry


# Tracks temp directories for cleanup
_temp_dirs: list[str] = []


def create_temp_dir() -> str:
    d = tempfile.mkdtemp(prefix="file-reader-test-")
    _temp_dirs.append(d)
    return d


@pytest.fixture(autouse=True)
def cleanup_temp_dirs():
    yield
    for d in _temp_dirs[:]:
        try:
            shutil.rmtree(d)
        except OSError:
            pass
    _temp_dirs.clear()


class TestReadCodebase:
    @pytest.mark.asyncio
    async def test_reads_ts_files(self) -> None:
        d = create_temp_dir()
        with open(os.path.join(d, "index.ts"), "w", encoding="utf-8") as f:
            f.write("export const x = 1;\n")

        result = await read_codebase(d)

        assert result.ok is True
        assert len(result.value) > 0
        file = next((f for f in result.value if f.path.endswith("index.ts")), None)
        assert file is not None
        assert "export const x = 1;" in file.content

    @pytest.mark.asyncio
    async def test_reads_multiple_source_files(self) -> None:
        d = create_temp_dir()
        with open(os.path.join(d, "a.ts"), "w", encoding="utf-8") as f:
            f.write("const a = 1;")
        with open(os.path.join(d, "b.js"), "w", encoding="utf-8") as f:
            f.write("const b = 2;")
        with open(os.path.join(d, "c.py"), "w", encoding="utf-8") as f:
            f.write("c = 3")

        result = await read_codebase(d)

        assert result.ok is True
        assert len(result.value) == 3

    @pytest.mark.asyncio
    async def test_excludes_node_modules(self) -> None:
        d = create_temp_dir()
        with open(os.path.join(d, "index.ts"), "w", encoding="utf-8") as f:
            f.write("export {};")

        nm_dir = os.path.join(d, "node_modules", "some-package")
        os.makedirs(nm_dir, exist_ok=True)
        with open(os.path.join(nm_dir, "index.js"), "w", encoding="utf-8") as f:
            f.write("module.exports = {};")

        result = await read_codebase(d)

        assert result.ok is True
        paths = [f.path for f in result.value]
        assert not any("node_modules" in p for p in paths)

    @pytest.mark.asyncio
    async def test_excludes_git_directory(self) -> None:
        d = create_temp_dir()
        with open(os.path.join(d, "app.ts"), "w", encoding="utf-8") as f:
            f.write("export {};")

        git_dir = os.path.join(d, ".git", "refs")
        os.makedirs(git_dir, exist_ok=True)
        with open(os.path.join(git_dir, "HEAD"), "w", encoding="utf-8") as f:
            f.write("ref: refs/heads/main")

        result = await read_codebase(d)

        assert result.ok is True
        paths = [f.path for f in result.value]
        assert not any(".git" in p for p in paths)

    @pytest.mark.asyncio
    async def test_excludes_non_source_extensions(self) -> None:
        d = create_temp_dir()
        with open(os.path.join(d, "source.ts"), "w", encoding="utf-8") as f:
            f.write("export {};")
        with open(os.path.join(d, "image.png"), "wb") as f:
            f.write(bytes([137, 80, 78, 71]))
        with open(os.path.join(d, "binary.exe"), "wb") as f:
            f.write(bytes([77, 90]))
        with open(os.path.join(d, "notes.docx"), "wb") as f:
            f.write(bytes([80, 75]))

        result = await read_codebase(d)

        assert result.ok is True
        paths = [f.path for f in result.value]
        assert not any(p.endswith(".png") for p in paths)
        assert not any(p.endswith(".exe") for p in paths)
        assert not any(p.endswith(".docx") for p in paths)
        assert any(p.endswith(".ts") for p in paths)

    @pytest.mark.asyncio
    async def test_returns_ok_with_empty_array_for_empty_dir(self) -> None:
        d = create_temp_dir()

        result = await read_codebase(d)

        assert result.ok is True
        assert len(result.value) == 0

    @pytest.mark.asyncio
    async def test_returns_err_for_nonexistent_dir(self) -> None:
        result = await read_codebase("/this/path/absolutely/does/not/exist")

        assert result.ok is False

    @pytest.mark.asyncio
    async def test_file_entries_contain_relative_paths(self) -> None:
        d = create_temp_dir()
        with open(os.path.join(d, "service.ts"), "w", encoding="utf-8") as f:
            f.write("export {};")

        result = await read_codebase(d)

        assert result.ok is True
        file = next((f for f in result.value if f.path.endswith("service.ts")), None)
        assert file is not None
        assert not os.path.isabs(file.path)


class TestFormatFilesForPrompt:
    def test_returns_empty_string_for_empty_list(self) -> None:
        output = format_files_for_prompt([])
        assert output == ""

    def test_formats_single_file_with_separator_header(self) -> None:
        files = [FileEntry(path="src/index.ts", content="export const x = 1;")]

        output = format_files_for_prompt(files)

        assert "=== src/index.ts ===" in output
        assert "export const x = 1;" in output

    def test_formats_multiple_files_separated_by_double_newlines(self) -> None:
        files = [
            FileEntry(path="a.ts", content="const a = 1;"),
            FileEntry(path="b.ts", content="const b = 2;"),
        ]

        output = format_files_for_prompt(files)

        assert "=== a.ts ===" in output
        assert "const a = 1;" in output
        assert "=== b.ts ===" in output
        assert "const b = 2;" in output

        parts = output.split("\n\n")
        assert len(parts) >= 2

    def test_preserves_file_content_verbatim(self) -> None:
        content = "function hello() {\n  return 'world';\n}\n"
        files = [FileEntry(path="hello.ts", content=content)]

        output = format_files_for_prompt(files)

        assert content in output


class TestHasSourceFiles:
    def test_returns_false_for_empty_array(self) -> None:
        assert has_source_files([]) is False

    def test_returns_true_for_one_file(self) -> None:
        files = [FileEntry(path="src/index.ts", content="export {};")]
        assert has_source_files(files) is True

    def test_returns_true_for_multiple_files(self) -> None:
        files = [
            FileEntry(path="a.ts", content=""),
            FileEntry(path="b.ts", content=""),
        ]
        assert has_source_files(files) is True
