"""License audit fixtures never depend on the checkout's installed packages."""

import json
from pathlib import Path

import pytest
from coalsense_audit.licenses import approved, audit


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    (tmp_path / "tools/audit").mkdir(parents=True)
    (tmp_path / "tools/audit/approved_licenses.yaml").write_text(
        json.dumps(
            {
                "licenses": ["MIT", "BSD-3-Clause", "Apache-2.0", "MPL-2.0", "PSF-2.0"],
                "font_packages": [],
                "exceptions": [],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "pnpm-lock.yaml").write_text(
        "lockfileVersion: '9.0'\nimporters:\n  .: {}\npackages:\n"
        "  'example@1.0.0':\n    resolution: {}\nsnapshots: {}\n",
        encoding="utf-8",
    )
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"example": "1.0.0"}}', encoding="utf-8"
    )
    installed = tmp_path / "node_modules/.pnpm/example@1.0.0/node_modules/example"
    installed.mkdir(parents=True)
    (installed / "package.json").write_text(
        '{"name":"example","version":"1.0.0","license":"MIT"}', encoding="utf-8"
    )
    (tmp_path / "uv.lock").write_text(
        'version = 1\n[[package]]\nname = "indirect"\nversion = "2.0"\n'
        'source = { registry = "https://example.invalid" }\nlicense = "MIT"\n',
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text('[project]\nname="fixture"\n', encoding="utf-8")
    (tmp_path / "THIRD_PARTY.md").write_text(
        "| Paquete | Versión | Licencia | Origen | Por qué |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| example | 1.0.0 | MIT | npm | prueba |\n",
        encoding="utf-8",
    )
    return tmp_path


def test_approved_passes(tree: Path) -> None:
    assert audit(tree) == []


@pytest.mark.parametrize(
    "license_text", ["GPL-3.0-only", "AGPL-3.0", "LGPL-2.1", "SSPL-1.0", "EULA", ""]
)
def test_unapproved_fails(tree: Path, license_text: str) -> None:
    path = tree / "uv.lock"
    path.write_text(path.read_text().replace('license = "MIT"', f'license = "{license_text}"'))
    assert any("LICENCIA" in finding for finding in audit(tree))


def test_unregistered_fails(tree: Path) -> None:
    (tree / "THIRD_PARTY.md").write_text("")
    assert any("REGISTRO" in finding for finding in audit(tree))


def test_wrong_registered_version(tree: Path) -> None:
    path = tree / "THIRD_PARTY.md"
    path.write_text(path.read_text(encoding="utf-8").replace("1.0.0", "9.0.0"), encoding="utf-8")
    assert any("REGISTRO" in finding for finding in audit(tree))


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("MIT OR GPL-3.0-only", True),
        ("MIT AND GPL-3.0-only", False),
        ("(MIT OR GPL-3.0-only) AND Apache-2.0", True),
        ("MIT OR", False),
        ("MIT WITH unknown", False),
        ("OFL-1.1", False),
    ],
)
def test_expressions(expression: str, expected: bool) -> None:
    assert approved(expression, {"MIT", "Apache-2.0"}) is expected


def test_missing_npm_metadata_fails(tree: Path) -> None:
    for path in (tree / "node_modules").rglob("package.json"):
        path.unlink()
    assert any("LICENCIA" in finding for finding in audit(tree))


@pytest.mark.integration
def test_repository_smoke() -> None:
    assert audit(Path(__file__).resolve().parents[3]) == []


def test_font_allowlist_and_exception(tree: Path) -> None:
    lock = tree / "uv.lock"
    lock.write_text(lock.read_text().replace('license = "MIT"', 'license = "OFL-1.1"'))
    assert audit(tree)
    path = tree / "tools/audit/approved_licenses.yaml"
    policy = json.loads(path.read_text())
    policy["font_packages"] = ["pypi:indirect"]
    path.write_text(json.dumps(policy))
    assert audit(tree) == []
    lock.write_text(lock.read_text().replace("OFL-1.1", "custom"))
    policy["exceptions"] = [
        {
            "ecosystem": "pypi",
            "name": "indirect",
            "version": "2.0",
            "license": "custom",
            "reason": "Revisión ficticia para prueba",
        }
    ]
    path.write_text(json.dumps(policy))
    assert audit(tree) == []
    policy["exceptions"][0]["reason"] = ""
    path.write_text(json.dumps(policy))
    assert any("ENTRADA" in f for f in audit(tree))


def test_malformed_inputs_do_not_leak(tree: Path) -> None:
    (tree / "uv.lock").write_text("PRIVATE_USER_TEXT")
    result = audit(tree)
    assert result and all("PRIVATE_USER_TEXT" not in f for f in result)


def test_transitive_version_of_direct_package_needs_no_registration(tree: Path) -> None:
    lock = tree / "pnpm-lock.yaml"
    lock.write_text(lock.read_text().replace("snapshots: {}", "  example@2.0.0: {}\nsnapshots: {}"))
    path = tree / "node_modules/.pnpm/example@2.0.0/node_modules/example"
    path.mkdir(parents=True)
    (path / "package.json").write_text('{"name":"example","version":"2.0.0","license":"MIT"}')
    assert audit(tree) == []


def test_python_direct_version_and_normalization(tree: Path) -> None:
    lock = tree / "uv.lock"
    lock.write_text(
        lock.read_text() + '\n[[package]]\nname="fixture"\nversion="0"\nsource={virtual="."}\n'
    )
    (tree / "pyproject.toml").write_text(
        '[project]\nname="fixture"\ndependencies=["Indirect==2.0"]\n'
    )
    assert any("REGISTRO" in f for f in audit(tree))
    path = tree / "THIRD_PARTY.md"
    path.write_text(
        path.read_text(encoding="utf-8") + "| indirect | 2.0 | MIT | PyPI | prueba |\n",
        encoding="utf-8",
    )
    assert audit(tree) == []


def test_python_metadata_version_must_match(monkeypatch: pytest.MonkeyPatch) -> None:
    from email.message import Message
    from types import SimpleNamespace

    from coalsense_audit.licenses import python_license

    metadata = Message()
    metadata["License-Expression"] = "MIT"
    monkeypatch.setattr(
        "importlib.metadata.distribution",
        lambda name: SimpleNamespace(version="1.0", metadata=metadata),
    )
    assert python_license("fixture", "1.0") == "MIT"
    assert python_license("fixture", "2.0") == ""


def test_finding_names_package_version_and_license(tree: Path) -> None:
    lock = tree / "uv.lock"
    lock.write_text(lock.read_text().replace('license = "MIT"', 'license = "GPL-3.0-only"'))
    expected = 'uv.lock:2: LICENCIA: indirect@2.0: licencia "{}" no aprobada'
    assert audit(tree) == [expected.format("GPL-3.0-only")]
    lock.write_text(lock.read_text().replace('license = "GPL-3.0-only"\n', ""))
    assert audit(tree) == [expected.format("desconocida")]


def test_finding_does_not_echo_hostile_license_text(tree: Path) -> None:
    lock = tree / "uv.lock"
    lock.write_text(lock.read_text().replace('license = "MIT"', 'license = "evil\\nSECRET=1"'))
    result = audit(tree)
    assert result and all("SECRET" not in f for f in result)


def _write_npm_license(tree: Path, body: str) -> None:
    path = tree / "node_modules/.pnpm/example@1.0.0/node_modules/example/package.json"
    path.write_text('{"name":"example","version":"1.0.0",' + body + "}", encoding="utf-8")


def test_npm_legacy_licenses_array(tree: Path) -> None:
    _write_npm_license(tree, '"licenses":[{"type":"GPL-3.0-only"},{"type":"MIT"}]')
    assert audit(tree) == []
    _write_npm_license(tree, '"licenses":[{"type":"GPL-3.0-only"}]')
    assert audit(tree) == [
        'pnpm-lock.yaml:5: LICENCIA: example@1.0.0: licencia "GPL-3.0-only" no aprobada'
    ]


def test_uninstalled_platform_package_inherits_from_installed_sibling(tree: Path) -> None:
    lock = tree / "pnpm-lock.yaml"
    for plat in ("linux-64", "windows-64"):
        entry = f"  '@scope/{plat}@1.0.0':\n    resolution: {{}}\n    os: [x]\nsnapshots: {{}}"
        lock.write_text(lock.read_text().replace("snapshots: {}", entry))
    assert any("@scope/linux-64@1.0.0" in f for f in audit(tree))
    sibling = tree / "node_modules/.pnpm/@scope+windows-64@1.0.0/node_modules/@scope/windows-64"
    sibling.mkdir(parents=True)
    (sibling / "package.json").write_text(
        '{"name":"@scope/windows-64","version":"1.0.0","license":"MIT"}', encoding="utf-8"
    )
    assert audit(tree) == []


def test_platform_package_without_os_or_cpu_gets_no_inheritance(tree: Path) -> None:
    lock = tree / "pnpm-lock.yaml"
    for plat in ("linux-64", "windows-64"):
        entry = f"  '@scope/{plat}@1.0.0':\n    resolution: {{}}\nsnapshots: {{}}"
        lock.write_text(lock.read_text().replace("snapshots: {}", entry))
    sibling = tree / "node_modules/.pnpm/@scope+windows-64@1.0.0/node_modules/@scope/windows-64"
    sibling.mkdir(parents=True)
    (sibling / "package.json").write_text(
        '{"name":"@scope/windows-64","version":"1.0.0","license":"MIT"}', encoding="utf-8"
    )
    assert any("@scope/linux-64@1.0.0" in f for f in audit(tree))


def test_workspace_members_are_not_third_party(tree: Path) -> None:
    lock = tree / "uv.lock"
    member = '\n[[package]]\nname="member"\nversion="0"\nsource={editable="m"}\n'
    lock.write_text(lock.read_text() + member)
    (tree / "m").mkdir()
    (tree / "m/pyproject.toml").write_text('[project]\nname="member"\n', encoding="utf-8")
    assert audit(tree) == []


def _dist(tmp_path: Path, license_text: str) -> Path:
    info = tmp_path / "bsdpkg-1.0.dist-info"
    (info / "licenses").mkdir(parents=True)
    (info / "METADATA").write_text(
        "Metadata-Version: 2.4\nName: bsdpkg\nVersion: 1.0\n"
        "Classifier: License :: OSI Approved :: BSD License\nLicense-File: LICENSE.txt\n",
        encoding="utf-8",
    )
    (info / "licenses/LICENSE.txt").write_text(license_text, encoding="utf-8")
    return info


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Redistribution and use ...\n* Neither the name of the holders", "BSD-3-Clause"),
        (
            "Redistribution and use ... source code must retain ... binary form must reproduce",
            "BSD-2-Clause",
        ),
        ("Do whatever", "UNKNOWN"),
    ],
)
def test_generic_bsd_classifier_resolved_from_license_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, text: str, expected: str
) -> None:
    import importlib.metadata as md

    from coalsense_audit.licenses import python_license

    dist = md.PathDistribution(_dist(tmp_path, text))
    monkeypatch.setattr("importlib.metadata.distribution", lambda name: dist)
    assert python_license("bsdpkg", "1.0") == expected


def test_uninstalled_build_backend_uses_register(tree: Path) -> None:
    (tree / "pyproject.toml").write_text(
        '[project]\nname="fixture"\n[build-system]\nrequires=["fixture_backend==3.0"]\n',
        encoding="utf-8",
    )
    lock = tree / "uv.lock"
    root = '\n[[package]]\nname="fixture"\nversion="0"\nsource={virtual="."}\n'
    lock.write_text(lock.read_text() + root)
    assert any("fixture_backend@3.0" in f for f in audit(tree))
    path = tree / "THIRD_PARTY.md"
    row = "| fixture_backend | 3.0 | MIT OR Apache-2.0 | PyPI | prueba |\n"
    path.write_text(path.read_text(encoding="utf-8") + row, encoding="utf-8")
    assert audit(tree) == []
    path.write_text(
        path.read_text(encoding="utf-8").replace("MIT OR Apache-2.0", "GPL-3.0-only"),
        encoding="utf-8",
    )
    assert any("fixture_backend@3.0" in f for f in audit(tree))
