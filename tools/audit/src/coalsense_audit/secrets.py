"""Offline Git inventory secret audit; policy uses the JSON subset of YAML."""

import json
import re
import subprocess
import sys
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
    "ASSIGNMENT": (
        r"""(?i)\b(?:password|secret|token|api_key)\b["']?\s*[:=]\s*"""
        r"""(?P<quote>["'])(?P<value>[^\r\n]*?)(?P=quote)"""
    ),
}
RULES = {name: re.compile(pattern) for name, pattern in PATTERNS.items()}


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
            item["rule"] not in RULES
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


def audit(root: Path) -> list[str]:
    try:
        allowed = read_policy(root)
    except (OSError, ValueError, TypeError):
        return [f"{POLICY}:1: ENTRADA: No se pudo leer o validar la política de secretos."]
    try:
        paths = inventory(root)
    except (OSError, subprocess.SubprocessError):
        return [".:1: ENTRADA: No se pudo obtener el inventario de Git."]
    findings: set[str] = set()
    for path in paths:
        source = root / path
        try:
            # Do not follow links (including directory links) out of the inventory.
            # Only components below root: a symlinked checkout location is legitimate.
            if any(
                p.is_symlink()
                for p in (source, *source.parents)[: len(source.parts) - len(root.parts)]
            ):
                continue
            if not source.resolve().is_relative_to(root.resolve()):
                continue
            raw = source.read_bytes()
        except OSError:
            # Deleted tracked files and permission-locked paths are skipped gracefully.
            continue
        if b"\0" in raw:
            continue
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeError:
            continue
        for rule, pattern in RULES.items():
            if (path, rule) in allowed:
                continue
            for match in pattern.finditer(text):
                value = match.groupdict().get("value", match[0])
                if placeholder(value) or (rule == "ASSIGNMENT" and len(value) < 16):
                    continue
                line = text.count("\n", 0, match.start()) + 1
                safe_path = path.encode("unicode_escape").decode("ascii")
                findings.add(f"{safe_path}:{line}: {rule}: Posible secreto detectado.")
    return sorted(findings)


def main() -> int:
    findings = audit(Path(__file__).resolve().parents[4])
    for finding in findings:
        print(finding)
    return int(bool(findings))


if __name__ == "__main__":
    sys.exit(main())
