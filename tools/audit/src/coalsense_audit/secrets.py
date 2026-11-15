"""Offline Git inventory secret audit; policy uses the JSON subset of YAML."""

import json
import math
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path, PurePosixPath

POLICY = "tools/audit/secrets_allowlist.yaml"

# Named groups select only the credential (not the surrounding assignment/URL).
PATTERNS = {
    "PEM": r"-----BEGIN (?:[A-Z0-9]+ )?PRIVATE KEY-----",
    "AWS": r"\bAKIA[A-Z0-9]{16}\b",
    "GITHUB": r"\bghp_[A-Za-z0-9]{36,}\b",
    "GITHUB_PAT": r"\bgithub_pat_[A-Za-z0-9_]{22,}\b",
    "SLACK": r"\bxox[baprs]-[A-Za-z0-9-]{10,}",
    "ANTHROPIC": r"\bsk-ant-[A-Za-z0-9_-]{20,}",
    "OPENAI": r"\bsk-(?!ant-)[A-Za-z0-9_-]{20,}",
    "GOOGLE": r"\bAIza[A-Za-z0-9_-]{35}\b",
    "STRIPE": r"\bsk_live_[A-Za-z0-9]{16,}",
    "JWT": r"\beyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]{16,}",
    "CONNECTION": (
        r"(?i)\b[a-z][a-z0-9+.-]*://[^\s/:@]+:"
        r"(?P<value>[^\s@/]+)@"
    ),
    # Name may be embedded (DB_PASSWORD, access_token); value quoted (also JSON-escaped) or bare.
    "ASSIGNMENT": (
        r"""(?i)(?:password|passwd|secret|token|api[_-]?key|private[_-]?key)[A-Za-z0-9_]*"""
        r"""\\?["']?[ \t]*(?:=>|[:=])(?!=)[ \t]*"""
        r"""(?:\\?(?P<quote>["'])(?P<value>[^\r\n]{0,512}?)\\?(?P=quote)"""
        r"""|(?P<bare>[^\s#"',;()\[\]<>{}]+))"""
    ),
}
RULES = {name: re.compile(pattern) for name, pattern in PATTERNS.items()}
# Not a pattern: a text-extension file that cannot be read or decoded. Allowlistable like a rule.
UNREADABLE = "ILEGIBLE"
TEXT_SUFFIXES = {
    *(".yaml", ".yml", ".json", ".toml", ".ini", ".cfg", ".py", ".ts", ".tsx"),
    *(".js", ".md", ".txt", ".sh", ".ps1"),
}
# shortcut: assignment values with whitespace are prose/commands (misses passphrases).
# shortcut: bare (unquoted) values are secrets only if high-entropy and not a reference,
# path/URL/call or lowercase/UPPER word identifier (misses all-lowercase letter-only keys).
WORDS = re.compile(r"(?:[a-z]+(?:[_-][a-z]+)*|[A-Z]+(?:_[A-Z]+)*)")


def bare_secret(value: str) -> bool:
    if value[0] in "$%" or any(c in value for c in "./(") or "::" in value:
        return False
    if WORDS.fullmatch(value) or not (any(c.isdigit() for c in value) or value != value.lower()):
        return False
    counts = Counter(value)
    return -sum(n / len(value) * math.log2(n / len(value)) for n in counts.values()) >= 3.5


def is_text_path(path: str) -> bool:
    name = PurePosixPath(path).name.lower()
    return name.startswith(".env") or PurePosixPath(name).suffix in TEXT_SUFFIXES


def decode(raw: bytes) -> str | None:
    """UTF-8 (with or without BOM) or BOM-marked UTF-16; None means binary or undecodable."""
    try:
        if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
            return raw.decode("utf-16")
        if b"\0" in raw:
            return None
        return raw.decode("utf-8-sig")
    except UnicodeError:
        return None


def placeholder(value: str) -> bool:
    """Only whole obvious markers are exempt, never a substring of a credential."""
    value = re.sub(r"^(?:sk-ant-|sk_live_|sk-|github_pat_|ghp_|xox[baprs]-|AIza|AKIA)", "", value)
    return bool(re.fullmatch(r"(?i)(?:changeme|example|x{3,}|<[^<>]*>|\$\{[^{}]*\})", value))


def read_policy(root: Path) -> set[tuple[str, str]]:
    data = json.loads((root / POLICY).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"exceptions"}:
        raise ValueError
    if not isinstance(data["exceptions"], list):
        raise ValueError
    allowed = set()
    for item in data["exceptions"]:
        if not isinstance(item, dict) or set(item) != {"path", "rule", "reason"}:
            raise ValueError
        if any(not isinstance(v, str) or not v.strip() for v in item.values()):
            raise ValueError
        path = item["path"]
        if (
            item["rule"] not in {*RULES, UNREADABLE}
            or PurePosixPath(path).is_absolute()
            or any(p in {"", ".", ".."} for p in path.split("/"))
            or any(c in path for c in "\\:*?[]")
            or not path.isprintable()
        ):
            raise ValueError
        allowed.add((path, item["rule"]))
    return allowed


def inventory(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        capture_output=True,
        check=True,
    )
    # Do not relay Git stderr: it may contain uncontrolled paths or content.
    return sorted(
        set(p.decode("utf-8", errors="surrogateescape") for p in result.stdout.split(b"\0") if p)
    )


def scan(root: Path) -> tuple[list[str], int]:
    """Return (findings, count of binary/unreadable files skipped)."""
    try:
        allowed = read_policy(root)
    except (OSError, ValueError, TypeError):
        return [f"{POLICY}:1: ENTRADA: No se pudo leer o validar la política de secretos."], 0
    try:
        paths = inventory(root)
    except (OSError, subprocess.SubprocessError):
        return [".:1: ENTRADA: No se pudo obtener el inventario de Git."], 0
    findings: set[str] = set()
    skipped = 0
    for path in paths:
        safe_path = path.encode("unicode_escape").decode("ascii")
        source = root / path
        text = None
        try:
            # Do not follow links (including directory links) out of the inventory.
            # Only components below root: a symlinked checkout location is legitimate.
            if any(
                p.is_symlink()
                for p in (source, *source.parents)[: len(source.parts) - len(root.parts)]
            ):
                continue
            if not source.resolve().is_relative_to(root.resolve()) or source.is_dir():
                continue
            text = decode(source.read_bytes())
        except (FileNotFoundError, NotADirectoryError):
            continue  # tracked file deleted from the working tree
        except (OSError, ValueError):
            pass  # permission-locked or odd path: counted below, never echoed
        if text is None:
            skipped += 1
            if is_text_path(path) and (path, UNREADABLE) not in allowed:
                findings.add(
                    f"{safe_path}:1: {UNREADABLE}: Archivo de texto ilegible o no decodificable."
                )
            continue
        for rule, pattern in RULES.items():
            if (path, rule) in allowed:
                continue
            for match in pattern.finditer(text):
                groups = match.groupdict()
                value = groups.get("value") or groups.get("bare") or ""
                if rule not in {"CONNECTION", "ASSIGNMENT"}:
                    value = match[0]
                if placeholder(value) or (
                    rule == "ASSIGNMENT"
                    and (
                        len(value) < 16
                        or re.search(r"\s", value)
                        or (groups.get("bare") and not bare_secret(value))
                    )
                ):
                    continue
                line = text.count("\n", 0, match.start()) + 1
                findings.add(f"{safe_path}:{line}: {rule}: Posible secreto detectado.")
    return sorted(findings), skipped


def audit(root: Path) -> list[str]:
    return scan(root)[0]


def main() -> int:
    findings, skipped = scan(Path(__file__).resolve().parents[4])
    for finding in findings:
        print(finding)
    print(f"omitidos: {skipped} archivos (ilegibles o binarios)", file=sys.stderr)
    return int(bool(findings))


if __name__ == "__main__":
    sys.exit(main())
