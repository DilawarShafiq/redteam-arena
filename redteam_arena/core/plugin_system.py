"""
Plugin system -- importlib-based plugin loading and lifecycle management.
Supports agent, provider, reporter, and scorer plugin types.
"""

from __future__ import annotations

import importlib
import json
import os
from dataclasses import dataclass


@dataclass
class PluginManifest:
    name: str
    version: str
    description: str
    plugin_type: str  # "agent", "provider", "reporter", "scorer"
    entry_point: str
    author: str = ""
    homepage: str = ""


@dataclass
class LoadedPlugin:
    manifest: PluginManifest
    module: object
    active: bool = False


class PluginSystem:
    def __init__(self) -> None:
        self._plugins: dict[str, LoadedPlugin] = {}
        self._search_paths: list[str] = []

    def add_search_path(self, path: str) -> None:
        """Add a directory to search for plugins."""
        if path not in self._search_paths:
            self._search_paths.append(path)

    async def discover(self) -> list[PluginManifest]:
        """Discover plugins in search paths."""
        manifests: list[PluginManifest] = []

        for search_path in self._search_paths:
            if not os.path.isdir(search_path):
                continue

            for entry in os.listdir(search_path):
                plugin_dir = os.path.join(search_path, entry)
                manifest_path = os.path.join(plugin_dir, "redteam-plugin.json")

                if not os.path.isfile(manifest_path):
                    continue

                try:
                    with open(manifest_path, encoding="utf-8") as f:
                        data = json.load(f)

                    manifest = PluginManifest(
                        name=data.get("name", entry),
                        version=data.get("version", "0.0.0"),
                        description=data.get("description", ""),
                        plugin_type=data.get("type", "reporter"),
                        entry_point=data.get("entryPoint", "plugin"),
                        author=data.get("author", ""),
                        homepage=data.get("homepage", ""),
                    )
                    manifests.append(manifest)
                except (json.JSONDecodeError, OSError):
                    continue

        return manifests

    async def load(self, name: str) -> LoadedPlugin | None:
        """Load a plugin by name from search paths."""
        if name in self._plugins:
            return self._plugins[name]

        for search_path in self._search_paths:
            plugin_dir = os.path.join(search_path, name)
            manifest_path = os.path.join(plugin_dir, "redteam-plugin.json")

            if not os.path.isfile(manifest_path):
                continue

            try:
                with open(manifest_path, encoding="utf-8") as f:
                    data = json.load(f)

                manifest = PluginManifest(
                    name=data.get("name", name),
                    version=data.get("version", "0.0.0"),
                    description=data.get("description", ""),
                    plugin_type=data.get("type", "reporter"),
                    entry_point=data.get("entryPoint", "plugin"),
                    author=data.get("author", ""),
                    homepage=data.get("homepage", ""),
                )

                # Try to import the plugin module
                entry = manifest.entry_point
                module_path = os.path.join(plugin_dir, f"{entry}.py")

                if os.path.isfile(module_path):
                    spec = importlib.util.spec_from_file_location(
                        f"redteam_plugins.{name}", module_path
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        loaded = LoadedPlugin(
                            manifest=manifest,
                            module=module,
                            active=False,
                        )
                        self._plugins[name] = loaded
                        return loaded

            except Exception:
                continue

        return None

    async def activate(self, name: str) -> bool:
        """Activate a loaded plugin."""
        plugin = self._plugins.get(name)
        if not plugin:
            return False

        if hasattr(plugin.module, "activate"):
            activate_fn = getattr(plugin.module, "activate")
            if callable(activate_fn):
                try:
                    result = activate_fn()
                    if hasattr(result, "__await__"):
                        await result
                except Exception:
                    return False

        plugin.active = True
        return True

    async def deactivate(self, name: str) -> bool:
        """Deactivate a loaded plugin."""
        plugin = self._plugins.get(name)
        if not plugin:
            return False

        if hasattr(plugin.module, "deactivate"):
            deactivate_fn = getattr(plugin.module, "deactivate")
            if callable(deactivate_fn):
                try:
                    result = deactivate_fn()
                    if hasattr(result, "__await__"):
                        await result
                except Exception:
                    pass

        plugin.active = False
        return True

    def get_loaded(self) -> list[LoadedPlugin]:
        """Get all loaded plugins."""
        return list(self._plugins.values())

    def get_active(self) -> list[LoadedPlugin]:
        """Get all active plugins."""
        return [p for p in self._plugins.values() if p.active]

    def get_by_type(self, plugin_type: str) -> list[LoadedPlugin]:
        """Get all loaded plugins of a specific type."""
        return [
            p for p in self._plugins.values()
            if p.manifest.plugin_type == plugin_type
        ]
