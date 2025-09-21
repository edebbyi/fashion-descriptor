# src/visual_descriptor/export_csv_prompt.py
from __future__ import annotations
import csv, pathlib
from typing import Any, Dict, Iterable, Sequence

# Export order
FIELDS = [
    "image_id", "garment_type", "silhouette",
    "fabric.type", "fabric.texture", "fabric.weight", "fabric.finish",
    "garment.top", "garment.bottom",
    "garment.layers", "garment.top_length", "garment.bottom_length",
    "construction.seams", "construction.stitching",
    "construction.hems", "construction.closure",
    "construction.top", "construction.bottom",
    "fit_and_drape", "pose",
    "environment_lighting.setup", "environment_lighting.mood", "environment_lighting.background",
    "photo_style", "footwear.type", "footwear.color",
    "model.framing", "model.expression", "model.gaze",
    "camera.view", "camera.multiview", "camera.views", "camera.angle",
]

NUKES = {"string or null", "null", "none", "None", "", None}

def clean_token(x: Any) -> str:
    if x in NUKES:
        return ""
    s = str(x).strip()
    if s.lower() in {"string or null", "null", "none"}:
        return ""
    return s

class CSVExporter:
    """Tiny CSV writer with legacy-compatible shims used by cli.py."""
    def __init__(self, path: str | pathlib.Path, fields: Sequence[str] | None = None):
        self.path = pathlib.Path(path)
        self.fields = list(fields) if fields else list(FIELDS)
        self._f = None
        self._w = None
        self._header_written = False

    # lifecycle
    def open(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._f = self.path.open("w", newline="", encoding="utf-8")
        self._w = csv.writer(self._f)
        return self

    def __enter__(self): return self.open()
    def __exit__(self, *exc): self.close()

    def close(self):
        if self._f:
            self._f.flush()
            self._f.close()
        self._f = None
        self._w = None
        self._header_written = False

    # header/rows
    def write_header(self):
        if not self._w:
            self.open()
        if not self._header_written:
            self._w.writerow(self.fields)
            self._header_written = True

    def row_from_record(self, rec: Dict[str, Any]) -> list[str]:
        return [clean_token(rec.get(k, "")) for k in self.fields]

    # --- legacy shims ---
    def add_flat(self, flat: Dict[str, Any]) -> None:
        if not self._w:
            self.open()
        if not self._header_written:
            self.write_header()
        self._w.writerow(self.row_from_record(flat))

    def add_flats(self, flats: Iterable[Dict[str, Any]]) -> None:
        for f in flats:
            self.add_flat(f)

    def write_record(self, rec: Dict[str, Any]) -> None:
        self.add_flat(rec)

    def write_records(self, records: Iterable[Dict[str, Any]]) -> None:
        for r in records:
            self.add_flat(r)

    def write_rows(self, rows: Iterable[Sequence[Any]]) -> None:
        if not self._w:
            self.open()
        if not self._header_written:
            self.write_header()
        for r in rows:
            self._w.writerow([clean_token(x) for x in r])

    def finalize(self) -> None:
        self.close()


def prompt_line(rec: Dict[str, Any]) -> str:
    """One-line prompt text for image regeneration; sanitized & compact."""
    parts: list[str] = []

    def add(x: Any):
        x = clean_token(x)
        if x:
            parts.append(x)

    # garment & fabric
    add(rec.get("garment_type"))
    add(rec.get("silhouette"))
    fabric = ", ".join(filter(None, [
        clean_token(rec.get("fabric.type")),
        clean_token(rec.get("fabric.texture")),
        clean_token(rec.get("fabric.weight")),
        clean_token(rec.get("fabric.finish")),
    ]))
    add(fabric)

    # top/bottom components
    if clean_token(rec.get("garment.top")):
        parts.append(f"top: {clean_token(rec.get('garment.top'))}")
    if clean_token(rec.get("garment.bottom")):
        parts.append(f"bottom: {clean_token(rec.get('garment.bottom'))}")

    # construction (keep concise)
    for k in ("construction.seams", "construction.stitching", "construction.hems", "construction.closure"):
        add(rec.get(k))

    # fit / pose / model
    add(rec.get("fit_and_drape"))
    add(rec.get("pose"))
    add(rec.get("model.framing"))
    if clean_token(rec.get("model.expression")):
        parts.append(f"expression: {clean_token(rec.get('model.expression'))}")
    if clean_token(rec.get("model.gaze")):
        parts.append(f"gaze: {clean_token(rec.get('model.gaze'))}")

    # environment
    env = ", ".join(filter(None, [
        clean_token(rec.get("environment_lighting.setup")),
        clean_token(rec.get("environment_lighting.mood")),
        clean_token(rec.get("environment_lighting.background")),
    ]))
    add(env)

    # camera
    if clean_token(rec.get("camera.multiview")) == "yes":
        parts.append(f"views: {clean_token(rec.get('camera.views') or 'front, back')}")
    else:
        add(rec.get("camera.view"))
    add(rec.get("camera.angle"))

    # style & footwear
    add(rec.get("photo_style"))
    fw = ", ".join(filter(None, [clean_token(rec.get("footwear.type")), clean_token(rec.get("footwear.color"))]))
    add(fw)

    return " ".join(p for p in parts if p)