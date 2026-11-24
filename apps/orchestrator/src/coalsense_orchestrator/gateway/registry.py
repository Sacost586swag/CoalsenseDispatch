"""Catálogo explícito. Registrar no habilita, conecta ni ejecuta herramientas."""

from .manifest import ManifestError, ToolManifest


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolManifest] = {}

    def register(self, value: object) -> ToolManifest:
        manifest = ToolManifest.parse(value)
        if manifest.name in self._tools:
            raise ManifestError("gateway.tool.duplicate")
        self._tools[manifest.name] = manifest
        return manifest

    def get(self, name: str) -> ToolManifest:
        manifest = self._tools.get(name)
        if manifest is None:
            raise ManifestError("gateway.tool.unknown")
        return manifest

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._tools))
