import pytest

from pdfextract.core import ExtractionResult
from pdfextract.plugin import ExtractionPlugin, PluginRegistry


class DummyPlugin(ExtractionPlugin):
    name = "dummy"

    def __init__(self, handles=".dummy"):
        self._handles = handles

    def can_handle(self, source: str) -> bool:
        return source.endswith(self._handles)

    def extract(self, source: str, **options) -> ExtractionResult:
        return ExtractionResult(tables=[], source=source, plugin=self.name)


def test_register_and_get():
    reg = PluginRegistry()
    reg.register(DummyPlugin())
    assert reg.get("dummy").name == "dummy"
    assert [p.name for p in reg.plugins()] == ["dummy"]


def test_duplicate_registration_raises():
    reg = PluginRegistry()
    reg.register(DummyPlugin())
    with pytest.raises(ValueError):
        reg.register(DummyPlugin())


def test_register_rejects_non_plugin():
    reg = PluginRegistry()
    with pytest.raises(TypeError):
        reg.register(object())


def test_find_by_source():
    reg = PluginRegistry()
    reg.register(DummyPlugin())
    assert reg.find("a.dummy").name == "dummy"
    assert reg.find("a.pdf") is None


def test_extract_dispatch_and_no_plugin():
    reg = PluginRegistry()
    reg.register(DummyPlugin())
    result = reg.extract("a.dummy")
    assert result.plugin == "dummy"
    with pytest.raises(LookupError):
        reg.extract("a.pdf")


def test_get_unknown_raises():
    reg = PluginRegistry()
    with pytest.raises(KeyError):
        reg.get("nope")


def test_default_registry_has_pdf_plugin():
    import pdfextract

    names = {p.name for p in pdfextract.default_registry.plugins()}
    assert "pdf_table" in names
