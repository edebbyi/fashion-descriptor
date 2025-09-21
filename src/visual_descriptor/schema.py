# src/visual_descriptor/schema.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Record:
    image_id: str

    # Garment core
    garment_type: Optional[str] = None
    silhouette: Optional[str] = None

    # Fabric (now includes finish / reflectivity)
    fabric: Dict[str, Optional[str]] = field(default_factory=lambda: {
        "type": None,        # jersey, twill, chiffon...
        "texture": None,     # smooth, ribbed, brushed...
        "weight": None,      # light, medium, heavy
        "finish": None,      # matte, semi-gloss, glossy, satin
    })

    # Components
    garment: Dict[str, Optional[str]] = field(default_factory=lambda: {
        "top": None,
        "bottom": None,
    })

    garment_components: Dict[str, Optional[str]] = field(default_factory=lambda: {
        "top_length": None,        # cropped / waist / hip / thigh
        "bottom_length": None,     # short / midi / ankle / floor
        "layers": None,
    })

    # Construction (global + per-section compact strings/JSON)
    construction: Dict[str, Optional[str]] = field(default_factory=lambda: {
        "seams": None,
        "stitching": None,
        "hems": None,
        "closure": None,
        "top": None,
        "bottom": None,
    })

    # Fit / drape / pose
    fit_and_drape: Optional[str] = None
    pose: Optional[str] = None

    # Photography / environment
    environment_lighting: Dict[str, Optional[str]] = field(default_factory=lambda: {
        "setup": None,       # studio lighting / daylight / etc
        "mood": None,        # bright & clean / moody editorial
        "background": None,  # plain studio sweep / draped fabric / runway / textured wall
    })

    photo_style: Optional[str] = None

    # Footwear
    footwear: Dict[str, Optional[str]] = field(default_factory=lambda: {
        "type": None,
        "color": None,
    })

    # Model / framing (NEW)
    model: Dict[str, Optional[str]] = field(default_factory=lambda: {
        "framing": None,     # full-body / three-quarter / half-body / close-up
        "expression": None,  # neutral / soft smile / fierce / relaxed
        "gaze": None,        # to camera / off-camera
    })

    # Camera / views (NEW)
    camera: Dict[str, Optional[str]] = field(default_factory=lambda: {
        "view": None,        # front / back / side / three-quarter
        "multiview": None,   # yes / no
        "views": None,       # "front, back"
        "angle": None,       # eye level / low / high
    })

    # Optional color palette
    color_palette: List[str] = field(default_factory=list)

    # ---- CSV helper ----
    def dict_flat(self) -> Dict[str, str]:
        def g(d: Dict, k: str) -> str:
            return (d or {}).get(k) or ""
        return {
            "image_id": self.image_id or "",
            "garment_type": self.garment_type or "",
            "silhouette": self.silhouette or "",
            "fabric.type": g(self.fabric, "type"),
            "fabric.texture": g(self.fabric, "texture"),
            "fabric.weight": g(self.fabric, "weight"),
            "fabric.finish": g(self.fabric, "finish"),
            "garment.top": g(self.garment, "top"),
            "garment.bottom": g(self.garment, "bottom"),
            "garment.layers": self.garment_components.get("layers") or "",
            "garment.top_length": self.garment_components.get("top_length") or "",
            "garment.bottom_length": self.garment_components.get("bottom_length") or "",
            "construction.seams": g(self.construction, "seams"),
            "construction.stitching": g(self.construction, "stitching"),
            "construction.hems": g(self.construction, "hems"),
            "construction.closure": g(self.construction, "closure"),
            "construction.top": g(self.construction, "top"),
            "construction.bottom": g(self.construction, "bottom"),
            "fit_and_drape": self.fit_and_drape or "",
            "pose": self.pose or "",
            "environment_lighting.setup": g(self.environment_lighting, "setup"),
            "environment_lighting.mood": g(self.environment_lighting, "mood"),
            "environment_lighting.background": g(self.environment_lighting, "background"),
            "photo_style": self.photo_style or "",
            "footwear.type": g(self.footwear, "type"),
            "footwear.color": g(self.footwear, "color"),
            "model.framing": g(self.model, "framing"),
            "model.expression": g(self.model, "expression"),
            "model.gaze": g(self.model, "gaze"),
            "camera.view": g(self.camera, "view"),
            "camera.multiview": g(self.camera, "multiview"),
            "camera.views": g(self.camera, "views"),
            "camera.angle": g(self.camera, "angle"),
        }