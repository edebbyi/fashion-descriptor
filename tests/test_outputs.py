from pathlib import Path
from src.visual_descriptor.engine import Engine
from src.visual_descriptor.schema import Record




def test_roundtrip_stub(tmp_path: Path):
    # Create a tiny blank image
    from PIL import Image
    img = tmp_path / "test.jpg"
    Image.new("RGB", (64, 64), color=(240,240,240)).save(img)


    eng = Engine(model="stub")
    rec = eng.describe_image(img, passes=["A","B","C"])
    # Validate JSON
    Record(**rec) # will raise if invalid
    assert rec["garment_type"] == "dress"
    assert rec["fabric"]["type"] == "cotton"