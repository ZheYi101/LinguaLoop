from __future__ import annotations

import importlib.util
import sys

import pytest


def test_desktop_app_module_imports_without_loading_qt() -> None:
    from lingualoop.desktop import app

    assert app.create_workbench
    assert app.create_engine
    assert app.parse_args([]).use_mock is False
    assert app.parse_args(["--mock"]).provider_label == "Mock 调试"
    assert app.parse_args(["--mock", "--smoke"]).smoke is True


def test_windows_craft_module_is_not_auto_loaded_into_pyside(monkeypatch) -> None:
    from lingualoop.desktop import app

    monkeypatch.setenv("QML2_IMPORT_PATH", r"C:\CraftRoot\qml")
    monkeypatch.setenv("LINGUALOOP_KIRIGAMI_MODE", "auto")
    assert app.kirigami_runtime_available()
    if sys.platform == "win32":
        assert not app.kirigami_runtime_usable()


def test_desktop_real_provider_missing_env_has_chinese_error(monkeypatch, tmp_path) -> None:
    from lingualoop.desktop import app

    monkeypatch.chdir(tmp_path)
    for name in [
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "OPENAI_REASONING_MODEL",
        "OPENAI_DIALOGUE_MODEL",
    ]:
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError, match="真实 AI 配置不可用"):
        app.create_workbench(use_mock=False)


@pytest.mark.skipif(
    importlib.util.find_spec("PySide6") is None,
    reason="PySide6 is not installed",
)
@pytest.mark.parametrize("width,height", [(1180, 780), (360, 740), (412, 915)])
def test_qml_engine_factory_works_offscreen(monkeypatch, width, height) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("LINGUALOOP_KIRIGAMI_MODE", "off")
    monkeypatch.setenv("QT_QUICK_CONTROLS_MOBILE", "1" if width < 600 else "0")
    from PySide6.QtCore import QObject
    from PySide6.QtGui import QGuiApplication

    from lingualoop.desktop import app
    from lingualoop.desktop.viewmodel import LearningViewModel

    qt_app = QGuiApplication.instance() or QGuiApplication(["lingualoop-desktop-test"])
    viewmodel = LearningViewModel(app.create_workbench(use_mock=True), "Mock 调试")
    engine = app.create_engine(viewmodel)

    assert engine.rootObjects()
    root = engine.rootObjects()[0]
    root.width = width
    root.height = height
    qt_app.processEvents()
    assert root.width == width
    assert root.height == height
    for object_name in ("materialScroll", "practiceScroll", "reviewScroll"):
        scroll = root.findChild(QObject, object_name)
        assert scroll is not None
        assert scroll.property("contentWidth") == scroll.property("availableWidth")
    assert app.desktop_dependencies_available()
    assert isinstance(app.kirigami_runtime_available(), bool)
    engine.deleteLater()
    qt_app.processEvents()
