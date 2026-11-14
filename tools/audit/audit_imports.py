"""Thin entry point; also works without installing the workspace package."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from coalsense_audit.imports import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
