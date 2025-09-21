# src/visual_descriptor/engine.py
from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List

from .multipass_merge import merge_pass
from .normalize_vocab import normalize_record
from .schema import Record
from .captioners import StubCaptioner, Blip2Captioner, OpenAIVLM
from .utils import img_hash, is_image


class Engine:
    def __init__(self, model: str = "stub", normalize: bool = True):
        self.normalize = normalize
        # choose captioner
        if model == "openai" and OpenAIVLM is not None:
            self.model = OpenAIVLM()
        elif model == "blip2" and Blip2Captioner is not None:
            self.model = Blip2Captioner()
        else:
            self.model = StubCaptioner()

    def describe_image(self, path: Path, passes: List[str]) -> Dict[str, Any]:
        base: Dict[str, Any] = {"image_id": path.stem, "source_hash": img_hash(path)}
        rec = base
        for pid in passes:
            out, conf = self.model.run(path, pass_id=pid)
            rec = merge_pass(rec, out, conf, fields_scope=None)

        if self.normalize:
            rec = normalize_record(rec)

        # metadata + field defaults
        rec.setdefault("version", "vd_v1.0.0")
        rec.setdefault("confidence", {})
        # ensure footwear exists even if the model omitted it
        rec.setdefault("footwear", {"type": None, "color": None})

        # validate against schema (filter unknown keys)
        allowed = set(Record.model_fields.keys())
        r = Record(**{k: v for k, v in rec.items() if k in allowed})

        # include keys even if values are None (so footwear always appears)
        return r.model_dump(mode="python", exclude_none=False)

    def enumerate_inputs(self, in_path: Path) -> List[Path]:
        p = Path(in_path)
        if p.is_file():
            return [p] if is_image(p) else []
        return [q for q in p.iterdir() if is_image(q)]
