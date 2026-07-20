"""Tests for scan scope tracking and filename matching in file_reader."""

from __future__ import annotations

import os
import shutil
import tempfile

import pytest

from redteam_arena.core.file_reader import read_codebase
from redteam_arena.reports.scope_notice import format_scan_scope
from redteam_arena.types import ScanScope

_temp_dirs: list[str] = []


def create_temp_dir() -> str:
    d = tempfile.mkdtemp(prefix="scan-scope-test-")
    _temp_dirs.append(d)
    return d


def write(d: str, name: str, content: str) -> None:
    with open(os.path.join(d, name), "w", encoding="utf-8") as f:
        f.write(content)


@pytest.fixture(autouse=True)
def cleanup_temp_dirs():
    yield
    for d in _temp_dirs[:]:
        try:
            shutil.rmtree(d)
        except OSError:
            pass
    _temp_dirs.clear()


class TestExtensionlessFilenames:
    """Regression: splitext gives no extension for Dockerfile or bare dotfiles."""

    @pytest.mark.asyncio
    async def test_reads_dockerfile(self) -> None:
        d = create_temp_dir()
        write(d, "Dockerfile", "FROM python:3.12\nUSER root\n")

        result = await read_codebase(d)

        assert result.ok is True
        assert any(f.path == "Dockerfile" for f in result.value)

    @pytest.mark.asyncio
    async def test_reads_env_file(self) -> None:
        d = create_temp_dir()
        write(d, ".env", "API_KEY=sk-not-a-real-key\n")

        result = await read_codebase(d)

        assert result.ok is True
        env = next((f for f in result.value if f.path == ".env"), None)
        assert env is not None
        assert "API_KEY" in env.content

    @pytest.mark.asyncio
    async def test_reads_suffixed_variants(self) -> None:
        d = create_temp_dir()
        write(d, "Dockerfile.prod", "FROM alpine\n")
        write(d, ".env.staging", "DEBUG=true\n")

        result = await read_codebase(d)

        paths = {f.path for f in result.value}
        assert "Dockerfile.prod" in paths
        assert ".env.staging" in paths

    @pytest.mark.asyncio
    async def test_ignores_unrelated_extensionless_files(self) -> None:
        d = create_temp_dir()
        write(d, "LICENSE", "MIT")

        result = await read_codebase(d)

        assert all(f.path != "LICENSE" for f in result.value)


class TestScanScope:
    @pytest.mark.asyncio
    async def test_records_complete_scan(self) -> None:
        d = create_temp_dir()
        write(d, "a.py", "a = 1\n")
        scope = ScanScope()

        await read_codebase(d, scope=scope)

        assert scope.files_read == 1
        assert scope.bytes_read > 0
        assert scope.is_partial is False
        assert scope.skipped_count == 0

    @pytest.mark.asyncio
    async def test_flags_budget_exhaustion(self) -> None:
        d = create_temp_dir()
        for i in range(6):
            write(d, f"file{i}.py", "x = 1\n" * 200)
        scope = ScanScope()

        await read_codebase(d, max_total_size=1024, scope=scope)

        assert scope.is_partial is True
        assert scope.budget_exhausted or scope.skipped_over_budget

    @pytest.mark.asyncio
    async def test_records_oversize_skips(self) -> None:
        d = create_temp_dir()
        write(d, "huge.py", "x = 1\n" * 5000)
        write(d, "small.py", "y = 2\n")
        scope = ScanScope()

        await read_codebase(d, max_file_size=100, scope=scope)

        assert "huge.py" in scope.skipped_too_large
        assert scope.is_partial is True

    @pytest.mark.asyncio
    async def test_scope_is_optional(self) -> None:
        """Callers that pass no scope must still work."""
        d = create_temp_dir()
        write(d, "a.py", "a = 1\n")

        result = await read_codebase(d)

        assert result.ok is True


class TestFormatScanScope:
    def test_none_renders_nothing(self) -> None:
        assert format_scan_scope(None) == []

    def test_complete_scan_has_no_warning(self) -> None:
        scope = ScanScope(files_read=3, bytes_read=2048, max_total_size=102400)

        text = "\n".join(format_scan_scope(scope))

        assert "Files examined: **3**" in text
        assert "partial" not in text.lower()

    def test_partial_scan_warns(self) -> None:
        scope = ScanScope(
            files_read=2,
            bytes_read=102400,
            max_total_size=102400,
            budget_exhausted=True,
        )

        text = "\n".join(format_scan_scope(scope))

        assert "partial" in text.lower()
        assert "context budget was exhausted" in text

    def test_truncates_long_skip_lists(self) -> None:
        scope = ScanScope(
            files_read=1,
            max_total_size=102400,
            skipped_over_budget=[f"f{i}.py" for i in range(25)],
        )

        text = "\n".join(format_scan_scope(scope))

        assert "and 15 more" in text
        assert "f24.py" not in text
