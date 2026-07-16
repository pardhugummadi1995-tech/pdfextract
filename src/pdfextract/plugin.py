"""Plugin contract and registry for the pdfextract application.

The host application discovers extraction plugins through a small registry.
Each plugin implements :class:`ExtractionPlugin`, advertises which sources it
can handle, and returns a normalized :class:`~pdfextract.core.ExtractionResult`.

This indirection keeps the host application decoupled from any particular
extraction backend, so additional plugins (e.g. for scanned PDFs, spreadsheets,
or HTML) can be added without touching the caller.
"""

from __future__ import annotations

import abc
from typing import Callable

from .core import ExtractionResult


class ExtractionPlugin(abc.ABC):
    """Abstract base class every extraction plugin must implement."""

    #: Human-readable, unique plugin identifier.
    name: str = "base"

    @abc.abstractmethod
    def can_handle(self, source: str) -> bool:
        """Return ``True`` if this plugin can extract from ``source``."""
        raise NotImplementedError

    @abc.abstractmethod
    def extract(self, source: str, **options) -> ExtractionResult:
        """Extract tabular data from ``source`` and return the result."""
        raise NotImplementedError


class PluginRegistry:
    """A minimal registry the host application uses to manage plugins."""

    def __init__(self) -> None:
        self._plugins: dict[str, ExtractionPlugin] = {}

    def register(self, plugin: ExtractionPlugin) -> ExtractionPlugin:
        """Register ``plugin``, raising if its name is already taken."""
        if not isinstance(plugin, ExtractionPlugin):
            raise TypeError("plugin must be an ExtractionPlugin instance")
        if plugin.name in self._plugins:
            raise ValueError(f"a plugin named {plugin.name!r} is already registered")
        self._plugins[plugin.name] = plugin
        return plugin

    def unregister(self, name: str) -> None:
        self._plugins.pop(name, None)

    def get(self, name: str) -> ExtractionPlugin:
        try:
            return self._plugins[name]
        except KeyError as exc:
            raise KeyError(f"no plugin named {name!r} is registered") from exc

    def plugins(self) -> list[ExtractionPlugin]:
        return list(self._plugins.values())

    def find(self, source: str) -> ExtractionPlugin | None:
        """Return the first registered plugin that can handle ``source``."""
        for plugin in self._plugins.values():
            if plugin.can_handle(source):
                return plugin
        return None

    def extract(self, source: str, *, plugin: str | None = None, **options) -> ExtractionResult:
        """Extract from ``source`` using ``plugin`` or the first capable one."""
        selected = self.get(plugin) if plugin else self.find(source)
        if selected is None:
            raise LookupError(f"no registered plugin can handle {source!r}")
        return selected.extract(source, **options)


#: A process-wide default registry for convenience.
default_registry = PluginRegistry()


def register(plugin_factory: Callable[[], ExtractionPlugin]) -> Callable[[], ExtractionPlugin]:
    """Class/factory decorator that instantiates and registers a plugin.

    Example::

        @register
        class MyPlugin(ExtractionPlugin):
            name = "my_plugin"
            ...
    """

    default_registry.register(plugin_factory())
    return plugin_factory
