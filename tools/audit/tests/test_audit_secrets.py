"""Synthetic credentials are assembled at runtime, exclusively under tmp_path."""

import json
import subprocess
from pathlib import Path

import pytest
from coalsense_audit import secrets


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    git(tmp_path, "init")
    target = tmp_path / secrets.POLICY
    target.parent.mkdir(parents=True)
    target.write_text('{"exceptions": []}', encoding="utf-8")
    return tmp_path


def sample(rule: str) -> str:
    suffix = "Ab9Cd8Ef7Gh6Ij5Kl4Mn3Op2Qr1St0Uv"
    return {
        "PEM": "-----BEGIN " + "RSA PRIVATE KEY-----",
        "AWS": "AKIA" + "A1" * 8,
        "GITHUB": "ghp_" + suffix + "Ab12",
        "GITHUB_PAT": "github_pat_" + suffix * 2,
        "SLACK": "xoxb-" + suffix,
        "ANTHROPIC": "sk-ant-" + suffix,
        "OPENAI": "sk-" + suffix,
        "GOOGLE": "AIza" + suffix + "Ab1",
        "STRIPE": "sk_live_" + suffix,
        "JWT": "eyJ" + "hbGciOiJIUzI1NiJ9" + ".eyJ" + "zdWIiOiIxIn0" + "." + suffix,
        "CONNECTION": "postgres://user:" + suffix + "@localhost/db",
        "ASSIGNMENT": 'api_key = "' + suffix + '"',
    }[rule]


@pytest.mark.parametrize(
    "rule",
    [
        "PEM",
        "AWS",
        "GITHUB",
        "GITHUB_PAT",
        "SLACK",
        "ANTHROPIC",
        "OPENAI",
        "GOOGLE",
        "STRIPE",
        "JWT",
        "CONNECTION",
        "ASSIGNMENT",
    ],
)
def test_patterns(tree: Path, rule: str) -> None:
    value = sample(rule)
    (tree / "input.txt").write_text("clean\n" + value, encoding="utf-8")
    findings = secrets.audit(tree)
    assert any(f"input.txt:2: {rule}:" in f for f in findings)
    assert all(value not in f and "Ab9Cd8" not in f for f in findings)


@pytest.mark.parametrize(
    "value",
    ["changeme", "example", "x" * 24, "<insert credential here>", "${LONG_ENVIRONMENT_NAME}"],
)
def test_placeholders(tree: Path, value: str) -> None:
    (tree / "input.txt").write_text(
        'password = "' + value + '"\npostgres://user:' + value + "@host/db",
        encoding="utf-8",
    )
    assert secrets.audit(tree) == []


def test_clean_binary_and_git_selection(tree: Path) -> None:
    (tree / ".gitignore").write_text("ignored.txt\ntracked.txt\n", encoding="utf-8")
    (tree / "ignored.txt").write_text(sample("AWS"), encoding="utf-8")
    (tree / "binary.dat").write_bytes(b"\x00" + sample("AWS").encode())
    assert secrets.audit(tree) == []
    (tree / "tracked.txt").write_text(sample("AWS"), encoding="utf-8")
    git(tree, "add", "-f", "tracked.txt")
    assert len(secrets.audit(tree)) == 1
    (tree / "untracked.txt").write_text(sample("AWS"), encoding="utf-8")
    assert len(secrets.audit(tree)) == 2


def test_allowlist_is_exact(tree: Path) -> None:
    (tree / "one.txt").write_text(sample("AWS") + "\n" + sample("GOOGLE"), encoding="utf-8")
    (tree / "two.txt").write_text(sample("AWS"), encoding="utf-8")
    (tree / secrets.POLICY).write_text(
        json.dumps(
            {"exceptions": [{"path": "one.txt", "rule": "AWS", "reason": "Ejemplo revisado"}]}
        ),
        encoding="utf-8",
    )
    findings = secrets.audit(tree)
    assert len(findings) == 2
    assert not any("one.txt:1:" in f for f in findings)


@pytest.mark.parametrize(
    "data",
    [
        "private input",
        "{}",
        '{"exceptions": [{}]}',
        '{"exceptions": [{"path": "*", "rule": "AWS", "reason": ""}]}',
    ],
)
def test_invalid_policy(tree: Path, data: str) -> None:
    (tree / secrets.POLICY).write_text(data, encoding="utf-8")
    findings = secrets.audit(tree)
    assert len(findings) == 1 and "ENTRADA" in findings[0]
    assert "private input" not in findings[0]


def locked(monkeypatch: pytest.MonkeyPatch, name: str) -> None:
    original = Path.read_bytes

    def read(path: Path) -> bytes:
        if path.name == name:
            raise PermissionError("private input")
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", read)


def test_unreadable_text_file_fails(tree: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tree / "locked.txt").write_text("clean", encoding="utf-8")
    (tree / "locked.bin").write_text("clean", encoding="utf-8")
    locked(monkeypatch, "locked.txt")
    locked(monkeypatch, "locked.bin")
    findings, skipped = secrets.scan(tree)
    assert findings == ["locked.txt:1: ILEGIBLE: Archivo de texto ilegible o no decodificable."]
    assert skipped == 2
    assert "private input" not in findings[0]


def test_unreadable_text_file_exit_code(
    tree: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        secrets, "__file__", str(tree / "tools/audit/src/coalsense_audit/secrets.py")
    )
    (tree / "locked.yaml").write_text("clean", encoding="utf-8")
    locked(monkeypatch, "locked.yaml")
    assert secrets.main() == 1
    captured = capsys.readouterr()
    assert "locked.yaml:1: ILEGIBLE" in captured.out
    assert "omitidos: 1 archivos (ilegibles o binarios)" in captured.err


def test_undecodable_text_file_fails_binary_only_counts(tree: Path) -> None:
    (tree / "latin.md").write_bytes(b"caf\xe9")
    (tree / "image.dat").write_bytes(b"\x00\x01" + sample("AWS").encode())
    findings, skipped = secrets.scan(tree)
    assert findings == ["latin.md:1: ILEGIBLE: Archivo de texto ilegible o no decodificable."]
    assert skipped == 2


def test_unreadable_text_file_can_be_allowlisted(tree: Path) -> None:
    (tree / "latin.md").write_bytes(b"caf\xe9")
    (tree / secrets.POLICY).write_text(
        json.dumps(
            {"exceptions": [{"path": "latin.md", "rule": "ILEGIBLE", "reason": "Latin-1 heredado"}]}
        ),
        encoding="utf-8",
    )
    assert secrets.audit(tree) == []


@pytest.mark.parametrize("encoding", ["utf-16", "utf-16-be", "utf-8-sig"])
def test_bom_encodings_are_scanned(tree: Path, encoding: str) -> None:
    text = "JWT_SECRET=" + CRED + "\r\n"
    data = text.encode(encoding)
    if encoding == "utf-16-be":
        data = b"\xfe\xff" + data
    (tree / ".env.example").write_bytes(data)
    assert secrets.scan(tree) == (
        ["" + ".env.example:1: ASSIGNMENT: Posible secreto detectado."],
        0,
    )


def test_git_failure(tree: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("private input")

    monkeypatch.setattr(subprocess, "run", fail)
    result = secrets.audit(tree)
    assert len(result) == 1 and "ENTRADA" in result[0]
    assert "private input" not in result[0]


def test_main(
    tree: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        secrets, "__file__", str(tree / "tools/audit/src/coalsense_audit/secrets.py")
    )
    assert secrets.main() == 0
    assert capsys.readouterr().out == ""
    (tree / "input.txt").write_text(sample("AWS"), encoding="utf-8")
    assert secrets.main() == 1
    assert capsys.readouterr().out == "input.txt:1: AWS: Posible secreto detectado.\n"


@pytest.mark.integration
def test_repository_smoke() -> None:
    assert secrets.audit(Path(__file__).resolve().parents[3]) == []


def test_provider_placeholder_and_embedded_marker(tree: Path) -> None:
    target = tree / "input.txt"
    target.write_text("ghp_" + "x" * 36, encoding="utf-8")
    assert secrets.audit(tree) == []
    target.write_text("ghp_" + "example" + "Ab12" * 10, encoding="utf-8")
    assert len(secrets.audit(tree)) == 1


def test_missing_policy(tree: Path) -> None:
    (tree / secrets.POLICY).unlink()
    assert "ENTRADA" in secrets.audit(tree)[0]


def test_inventory_warning_is_not_printed(
    tree: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def result(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess("git", 0, b"missing.txt\0", b"private input")

    monkeypatch.setattr(subprocess, "run", result)
    assert secrets.audit(tree) == []
    assert capsys.readouterr() == ("", "")


CRED = "Ab9Cd8Ef7Gh6Ij5Kl4Mn3"


@pytest.mark.parametrize(
    "line",
    [
        "DB_PASSWORD=" + CRED,
        "SECRET_KEY=" + CRED,
        "JWT_SECRET=" + CRED + "\r",
        "access_token: " + CRED,
        "client_secret = '" + CRED + "'",
        "STRIPE_API_KEY=" + CRED,
        "password: " + CRED + " # comment",
        'password => "' + CRED + '"',
        '{\\"password\\": \\"' + CRED + '\\"}',
        '{"db_passwd": "' + CRED + '"}',
        'export TOKEN="' + CRED + '"',
    ],
)
def test_assignment_shapes(tree: Path, line: str) -> None:
    (tree / "settings.example").write_text("x\n" + line, encoding="utf-8")
    findings = secrets.audit(tree)
    assert findings == ["settings.example:2: ASSIGNMENT: Posible secreto detectado."]
    assert CRED not in findings[0]


@pytest.mark.parametrize(
    "line",
    [
        "JWT_SECRET=<value>",
        "JWT_SECRET=",
        "DB_PASSWORD=${DB_PASSWORD}",
        "DB_PASSWORD=changeme",
        "API_KEY=xxxxxxxxxxxxxxxxxxxx",
        "SECRET_KEY=example",
        'password: ""',
        "token = settings.access_token_value",
        "password == '" + CRED + "'",
        '"audit:secrets": "uv run --locked python -m coalsense_audit.secrets"',
        "integrity: sha512-" + CRED + "==",
    ],
)
def test_assignment_non_secrets(tree: Path, line: str) -> None:
    (tree / "settings.example").write_text(line, encoding="utf-8")
    assert secrets.audit(tree) == []


@pytest.mark.parametrize("separator", ["=", ": "])
@pytest.mark.parametrize("name", ["API_KEY", "api_key"])
def test_bare_letters_only_key(tree: Path, name: str, separator: str) -> None:
    key = "AbCdEfGhIjKlMnOpQrStUvWxYzAbCdEf"
    (tree / "settings.example").write_text(name + separator + key, encoding="utf-8")
    assert secrets.audit(tree) == ["settings.example:1: ASSIGNMENT: Posible secreto detectado."]


@pytest.mark.parametrize(
    "line",
    [
        "LOG_LEVEL=information_disclosure_mode",
        "token_mode: information-disclosure-mode",
        "SECRET_NAME=SOME_LONG_CONSTANT_NAME_HERE",
        "TOKEN_URL=https://example.com/oauth/token",
        "api_key=%API_KEY_FROM_ENVIRONMENT%",
        "api_key=$API_KEY_FROM_ENVIRONMENT",
        "password=settings::load_password_value",
        "token=os.environ.get_token_value",
        "secret=read_file_contents_and_strip_it",
    ],
)
def test_bare_references_are_not_secrets(tree: Path, line: str) -> None:
    (tree / "settings.example").write_text(line, encoding="utf-8")
    assert secrets.audit(tree) == []
