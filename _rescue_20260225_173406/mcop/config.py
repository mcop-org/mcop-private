from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Paths:
    base_dir: Path
    data_dir: Path
    out_dir: Path
    archive_dir: Path

def get_paths(base_dir: str | None = None) -> Paths:
    bd = Path(base_dir).resolve() if base_dir else Path.cwd().resolve()
    data = bd / "data"
    out = bd / "out"
    arch = bd / "archive"
    out.mkdir(parents=True, exist_ok=True)
    arch.mkdir(parents=True, exist_ok=True)
    return Paths(base_dir=bd, data_dir=data, out_dir=out, archive_dir=arch)
