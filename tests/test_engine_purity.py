"""Decision 42: the engine imports only numpy, math, json, dataclasses, typing; no file I/O."""

import ast
from pathlib import Path

MODEL = Path(__file__).resolve().parents[1] / "src" / "hre" / "model"
ALLOWED = {"numpy", "math", "json", "dataclasses", "typing", "__future__"}
FORBIDDEN_CALLS = {"open"}
FORBIDDEN_ATTRS = {"read_text", "write_text", "read_bytes", "write_bytes", "urlopen", "load", "dump"}


def _modules():
    files = sorted(MODEL.rglob("*.py"))
    assert files, "src/hre/model has no modules"
    return files


def test_engine_imports_only_the_allowed_packages():
    for py in _modules():
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom):
                if node.level:  # relative import inside hre.model
                    continue
                roots = {(node.module or "").split(".")[0]}
                if node.module and (node.module.startswith("hre.model") or node.module == "hre.schema"):
                    continue  # the engine's own modules and the input schema (itself pure, below)
            else:
                continue
            bad = roots - ALLOWED
            assert not bad, f"{py.name} imports {bad}"


def test_input_schema_is_itself_pure():
    schema = MODEL.parent / "schema.py"
    tree = ast.parse(schema.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            assert {n.split(".")[0] for n in names} <= ALLOWED, names


def test_engine_does_no_file_io():
    for py in _modules():
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                f = node.func
                if isinstance(f, ast.Name):
                    assert f.id not in FORBIDDEN_CALLS, f"{py.name} calls {f.id}()"
                if isinstance(f, ast.Attribute) and f.attr in FORBIDDEN_ATTRS:
                    owner = f.value.id if isinstance(f.value, ast.Name) else ""
                    assert owner != "json" or f.attr not in {"load", "dump"}, f"{py.name} json.{f.attr}"
                    assert f.attr not in {"read_text", "write_text", "read_bytes", "write_bytes",
                                          "urlopen"}, f"{py.name} calls .{f.attr}()"


def test_engine_never_imports_the_pipeline():
    for py in _modules():
        text = py.read_text(encoding="utf-8")
        assert "hre.data" not in text and "hre.build" not in text, py.name
