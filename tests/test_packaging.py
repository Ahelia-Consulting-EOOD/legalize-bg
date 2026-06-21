"""2.x-c packaging contract: console entry point + build-system are declared
and the entry-point target resolves."""

import pathlib
import tomllib

REPO = pathlib.Path(__file__).resolve().parents[1]


def test_console_entry_target_is_importable_and_callable():
    from mcp_server.__main__ import main
    assert callable(main)


def test_pyproject_declares_console_script_and_build_system():
    data = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["scripts"]["legalize-bg-mcp"] == "mcp_server.__main__:main"
    assert data["build-system"]["build-backend"] == "setuptools.build_meta"
    assert any("setuptools" in r for r in data["build-system"]["requires"])
