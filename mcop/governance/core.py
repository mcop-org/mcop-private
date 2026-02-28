
from __future__ import annotations

def is_core_reference(product_reference: str) -> bool:
    """
    Core lots are identified ONLY by product reference naming convention:
    Core-01, Core-02, Core-03, ...
    """
    if not product_reference:
        return False
    pr = str(product_reference).strip().lower()
    return pr.startswith("core-")

def target_precommit_pct(days_to_landing: int, is_core: bool) -> float:
    """
    Dynamic pre-sell target curve.
    - Non-core: stricter as landing approaches
    - Core: more forgiving (separate commercial logic)
    """
    d = int(days_to_landing)

    if is_core:
        # Core curve (more forgiving)
        if d <= 30:
            return 0.55
        if d <= 45:
            return 0.40
        if d <= 60:
            return 0.30
        return 0.20

    # Non-core curve (stricter)
    if d <= 30:
        return 0.70
    if d <= 60:
        return 0.45
    return 0.30
