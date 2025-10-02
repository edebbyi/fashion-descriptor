# src/visual_descriptor/schema.py
from __future__ import annotations
from typing import Any, Dict, List, Optional, ClassVar
from pydantic import BaseModel, Field, ConfigDict, field_validator

def _default_fabric() -> Dict[str, Optional[str]]:
    return {"type": None, "texture": None, "weight": None, "finish": None}

def _default_garment() -> Dict[str, Optional[str]]:
    return {"top": None, "bottom": None, "top_style": None, "top_sleeve": None}

def _default_garment_components() -> Dict[str, Any]:
    return {"top_length": None, "bottom_length": None, "layers": []}

def _default_construction() -> Dict[str, Any]:
    return {
        "seams": None, "stitching": None, "stitching_color": None, "hems": None, "closure": None,
        "top": None, "bottom": None
    }

def _default_environment() -> Dict[str, Optional[str]]:
    return {"setup": None, "mood": None, "background": None}

def _default_footwear() -> Dict[str, Optional[str]]:
    return {"type": None, "color": None}

def _default_model() -> Dict[str, Optional[str]]:
    return {"framing": None, "expression": None, "gaze": None}

def _default_camera() -> Dict[str, Optional[str]]:
    return {"view": None, "multiview": None, "views": None, "angle": None}

class Record(BaseModel):
    model_config = ConfigDict(extra="ignore", arbitrary_types_allowed=True)

    image_id: str

    garment_type: Optional[str] = None
    silhouette: Optional[str] = None

    fabric: Dict[str, Optional[str]] = Field(default_factory=_default_fabric)
    garment: Dict[str, Optional[str]] = Field(default_factory=_default_garment)
    garment_components: Dict[str, Any] = Field(default_factory=_default_garment_components)
    construction: Dict[str, Any] = Field(default_factory=_default_construction)

    fit_and_drape: Optional[str] = None
    pose: Optional[str] = None

    environment_lighting: Dict[str, Optional[str]] = Field(default_factory=_default_environment)
    photo_style: Optional[str] = None

    footwear: Dict[str, Optional[str]] = Field(default_factory=_default_footwear)

    model: Dict[str, Optional[str]] = Field(default_factory=_default_model)
    camera: Dict[str, Optional[str]] = Field(default_factory=_default_camera)

    color_palette: List[str] = Field(default_factory=list)
    
    # ADD THESE TWO FIELDS FOR TOP-LEVEL COLOR ACCESS
    color_primary: Optional[str] = None
    color_secondary: Optional[str] = None
    
    details: List[str] = Field(default_factory=list)
    styling: Dict[str, Optional[str]] = Field(default_factory=lambda: {"layering": None, "accessories": None})
    notes_uncertain: List[str] = Field(default_factory=list)

    photo_metrics: Dict[str, float] = Field(default_factory=dict)

    confidence: Dict[str, float] = Field(default_factory=dict)
    
    prompt_text: Optional[str] = None  # Human-readable description
    
    version: Optional[str] = None
    source_hash: Optional[str] = None

    @field_validator("garment_components", mode="before")
    @classmethod
    def _coerce_gcs(cls, v: Any) -> Dict[str, Any]:
        if not isinstance(v, dict):
            return _default_garment_components()
        out = dict(_default_garment_components())
        out.update(v or {})
        layers = out.get("layers", [])
        if layers is None:
            layers = []
        elif isinstance(layers, str):
            layers = [s.strip() for s in layers.split(",") if s.strip()]
        elif isinstance(layers, list):
            layers = [str(x).strip() for x in layers if str(x).strip()]
        else:
            layers = [str(layers).strip()] if str(layers).strip() else []
        out["layers"] = layers
        return out

    @field_validator("construction", mode="before")
    @classmethod
    def _coerce_cons(cls, v: Any) -> Dict[str, Any]:
        if not isinstance(v, dict):
            return _default_construction()
        out = dict(_default_construction())
        out.update(v or {})
        # normalize per-piece dict-or-null
        for part in ("top", "bottom"):
            blk = out.get(part)
            if isinstance(blk, list):
                out[part] = ", ".join([str(x).strip() for x in blk if str(x).strip()]) or None
            elif blk is not None and not isinstance(blk, (str, dict)):
                out[part] = str(blk).strip() or None
        return out

    @field_validator("camera", mode="before")
    @classmethod
    def _coerce_camera(cls, v: Any) -> Dict[str, Optional[str]]:
        """
        Ensure camera fields are strings (or None). Coerce lists to comma-joined strings
        and numerics/bools to canonical strings. Normalize multiview to 'yes'/'no'.
        """
        def as_str(x: Any) -> Optional[str]:
            if x is None:
                return None
            if isinstance(x, (list, tuple)):
                vals = [str(i).strip() for i in x if str(i).strip()]
                return ", ".join(vals) if vals else None
            if isinstance(x, bool):
                return "yes" if x else "no"
            if isinstance(x, (int, float)):
                s = str(x).strip()
                return s if s else None
            s = str(x).strip()
            return s if s else None

        out: Dict[str, Optional[str]] = {"view": None, "multiview": None, "views": None, "angle": None}
        if not isinstance(v, dict):
            return out

        for key in ("view", "multiview", "views", "angle"):
            out[key] = as_str(v.get(key))

        # normalize multiview
        mv = (out.get("multiview") or "").lower()
        if mv in {"true", "yes", "1"}:
            out["multiview"] = "yes"
        elif mv in {"false", "no", "0"}:
            out["multiview"] = "no"
        elif mv == "":
            out["multiview"] = None  # leave unset

        # normalize views: "front, back"
        if out.get("views"):
            toks = [t.strip() for t in str(out["views"]).split(",") if t.strip()]
            out["views"] = ", ".join(toks) if toks else None

        return out

    @staticmethod
    def _listify(v: Any) -> List[str]:
        if v is None:
            return []
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        if isinstance(v, str):
            s = v.strip()
            return [s] if s else []
        s = str(v).strip()
        return [s] if s else []

    # THIS IS THE KEY FIX: Add ClassVar to prevent CSV_FIELDS from being serialized
    CSV_FIELDS: ClassVar[List[str]] = [
        "image_id",
        "garment_type", "silhouette",
        "garment.top_style", "garment.top_sleeve", "garment.top",
        "garment.bottom", "garment.top_length", "garment.bottom_length",
        "garment.layers",
        "fabric.type", "fabric.texture", "fabric.weight", "fabric.finish",
        "color_primary", "color_secondary",
        "construction.seams", "construction.stitching", "construction.stitching_color",
        "construction.hems", "construction.closure",
        "construction.top.seams", "construction.top.stitching", "construction.top.stitching_color",
        "construction.top.hems", "construction.top.closure",
        "construction.bottom.seams", "construction.bottom.stitching", "construction.bottom.stitching_color",
        "construction.bottom.hems", "construction.bottom.closure",
        "fit_and_drape",
        "footwear.type", "footwear.color",
        "pose", "model.framing", "model.expression", "model.gaze",
        "camera.view", "camera.multiview", "camera.views", "camera.angle",
        "environment_lighting.setup", "environment_lighting.mood", "environment_lighting.background",
        "photo_style",
        "photo_metrics.specularity", "photo_metrics.translucency",
        "prompt_text",
    ]

    def dict_flat(self) -> Dict[str, str]:
        def g(d: Dict, k: str) -> str:
            return (d or {}).get(k) or ""

        colors = [c for c in (self.color_palette or []) if c]
        color_primary = self.color_primary or (colors[0] if len(colors) > 0 else "")
        color_secondary = self.color_secondary or (colors[1] if len(colors) > 1 else "")

        gc = self.garment_components if isinstance(self.garment_components, dict) else {}
        layers_val = gc.get("layers")
        layers_str = ", ".join(layers_val) if isinstance(layers_val, list) else (layers_val or "")

        def part(d: Any, key: str) -> Dict[str, str]:
            if isinstance(d, dict) and isinstance(d.get(key), dict):
                blk = d.get(key)
                return {
                    f"construction.{key}.seams": blk.get("seams") or "",
                    f"construction.{key}.stitching": blk.get("stitching") or "",
                    f"construction.{key}.stitching_color": blk.get("stitching_color") or "",
                    f"construction.{key}.hems": blk.get("hems") or "",
                    f"construction.{key}.closure": blk.get("closure") or "",
                }
            return {
                f"construction.{key}.seams": "",
                f"construction.{key}.stitching": "",
                f"construction.{key}.stitching_color": "",
                f"construction.{key}.hems": "",
                f"construction.{key}.closure": "",
            }

        cam = self.camera if isinstance(self.camera, dict) else {}
        multiview = g(cam, "multiview")
        mv_norm = multiview if multiview in ("yes", "no") else (multiview.lower() if multiview else "")

        flat: Dict[str, str] = {
            "image_id": self.image_id or "",
            "garment_type": self.garment_type or "",
            "silhouette": self.silhouette or "",
            "garment.top_style": g(self.garment, "top_style"),
            "garment.top_sleeve": g(self.garment, "top_sleeve"),
            "garment.top": g(self.garment, "top"),
            "garment.bottom": g(self.garment, "bottom"),
            "garment.top_length": gc.get("top_length") or "",
            "garment.bottom_length": gc.get("bottom_length") or "",
            "garment.layers": layers_str,
            "fabric.type": g(self.fabric, "type"),
            "fabric.texture": g(self.fabric, "texture"),
            "fabric.weight": g(self.fabric, "weight"),
            "fabric.finish": g(self.fabric, "finish"),
            "color_primary": color_primary,
            "color_secondary": color_secondary,
            "construction.seams": g(self.construction, "seams"),
            "construction.stitching": g(self.construction, "stitching"),
            "construction.stitching_color": g(self.construction, "stitching_color"),
            "construction.hems": g(self.construction, "hems"),
            "construction.closure": g(self.construction, "closure"),
            "fit_and_drape": self.fit_and_drape or "",
            "footwear.type": g(self.footwear, "type"),
            "footwear.color": g(self.footwear, "color"),
            "pose": self.pose or "",
            "model.framing": g(self.model, "framing"),
            "model.expression": g(self.model, "expression"),
            "model.gaze": g(self.model, "gaze"),
            "camera.view": g(self.camera, "view"),
            "camera.multiview": mv_norm,
            "camera.views": g(self.camera, "views"),
            "camera.angle": g(self.camera, "angle"),
            "environment_lighting.setup": g(self.environment_lighting, "setup"),
            "environment_lighting.mood": g(self.environment_lighting, "mood"),
            "environment_lighting.background": g(self.environment_lighting, "background"),
            "photo_style": self.photo_style or "",
            "photo_metrics.specularity": str((self.photo_metrics or {}).get("specularity", "")),
            "photo_metrics.translucency": str((self.photo_metrics or {}).get("translucency", "")),
            "prompt_text": self.prompt_text or "",
        }

        flat.update(part(self.construction, "top"))
        flat.update(part(self.construction, "bottom"))
        return flat