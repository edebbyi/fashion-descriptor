# src/visual_descriptor/multipass_merge.py
from __future__ import annotations
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple, List
import math

CONF_DELTA = 0.05  # how much confidence must differ to be "clearly higher"

def _is_empty(x: Any) -> bool:
    return x is None or x == "" or x == [] or x == {}

def _specificity_score(x: Any) -> float:
    if x is None: return 0.0
    if isinstance(x, str): return min(1.0, len(x) / 200.0)
    if isinstance(x, (list, tuple, set)): return min(1.0, len(x) / 50.0)
    if isinstance(x, dict): return min(1.0, len(x) / 50.0)
    return 0.5

def _prefer_by_conf(ca: Optional[float], cb: Optional[float]) -> Optional[int]:
    if ca is None or cb is None:
        return None
    if abs(ca - cb) > CONF_DELTA:
        return 0 if ca > cb else 1
    return None

def _choose_scalar(a: Any, ca: Optional[float], b: Any, cb: Optional[float]) -> Tuple[Any, Optional[float]]:
    if _is_empty(a): return b, cb
    if _is_empty(b): return a, ca

    by_conf = _prefer_by_conf(ca, cb)
    if by_conf is not None:
        return (a, ca) if by_conf == 0 else (b, cb)

    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if math.isclose(float(a), float(b), rel_tol=1e-6, abs_tol=1e-12):
            return (a, ca) if (ca or 0) >= (cb or 0) else (b, cb)
        return (a, ca) if (ca or 0) >= (cb or 0) else (b, cb)

    if isinstance(a, str) and isinstance(b, str)):
        sa, sb = _specificity_score(a), _specificity_score(b)
        if sa != sb:
            return (a, ca) if sa > sb else (b, cb)
        return b, cb  # deterministic "incoming wins"

    if isinstance(a, bool) and isinstance(b, bool):
        if by_conf is not None:
            return (a, ca) if by_conf == 0 else (b, cb)
        if a != b:
            return (True, ca if a else cb) if (a or b) else (a, ca)
        return b, cb

    sa, sb = _specificity_score(a), _specificity_score(b)
    if sa != sb:
        return (a, ca) if sa > sb else (b, cb)
    return b, cb

def _merge_lists(a: List[Any], b: List[Any]) -> List[Any]:
    seen = set()
    out: List[Any] = []
    for item in a + b:
        key = repr(item)
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out

def _merge_dicts(
    base: Dict[str, Any],
    incoming: Dict[str, Any],
    conf_in: Optional[Mapping[str, float]] = None,
    conf_base: Optional[Mapping[str, float]] = None,
) -> Dict[str, Any]:
    result: Dict[str, Any] = dict(base) if base else {}
    keys = set(result.keys()) | set(incoming.keys())
    for k in keys:
        a = result.get(k, None)
        b = incoming.get(k, None)
        ca = (conf_base or {}).get(k)
        cb = (conf_in or {}).get(k)

        if isinstance(a, dict) and isinstance(b, dict):
            result[k] = _merge_dicts(a, b, conf_in, conf_base)
            continue
        if isinstance(a, list) and isinstance(b, list):
            result[k] = _merge_lists(a, b)
            continue

        chosen, _c = _choose_scalar(a, ca, b, cb)
        result[k] = chosen
    return result

# Legacy-compatible API expected by engine.describe_image(...)
def merge_pass(
    base: Dict[str, Any] | None,
    incoming: Dict[str, Any] | None,
    conf_in: Optional[Mapping[str, float]] = None,
    conf_base: Optional[Mapping[str, float]] = None,
    fields_scope=None,  # accepted (ignored)
) -> Dict[str, Any]:
    base = base or {}
    incoming = incoming or {}
    return _merge_dicts(base, incoming, conf_in=conf_in, conf_base=conf_base)