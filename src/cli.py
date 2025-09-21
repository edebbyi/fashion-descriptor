# src/cli.py
from __future__ import annotations
import argparse, json
from pathlib import Path
from tqdm import tqdm

from src.visual_descriptor.engine import Engine
from src.visual_descriptor.export_csv_prompt import CSVExporter, prompt_line
from src.visual_descriptor.schema import Record


from dotenv import load_dotenv   # <-- add this
load_dotenv()  

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_dir", required=True)
    ap.add_argument("--out", dest="out_dir", required=True)
    ap.add_argument("--model", default="stub")        # stub | blip2 (optional later)
    ap.add_argument("--passes", default="A,B,C")      # e.g., A or A,B or A,B,C
    ap.add_argument("--normalize", default="yes")     # yes | no
    args = ap.parse_args()

    engine = Engine(model=args.model, normalize=(args.normalize.lower() == "yes"))

    out = Path(args.out_dir)
    (out / "json").mkdir(parents=True, exist_ok=True)

    images = engine.enumerate_inputs(Path(args.in_dir))
    if not images:
        print(f"No images found at {args.in_dir}. Use a file (…/look1.jpg) or a folder with .jpg/.png.")
        return

    exporter = CSVExporter(out / "descriptors.csv")

    prompt_path = out / "prompt_text.txt"
    if prompt_path.exists():
        prompt_path.unlink()

    for img in tqdm(images, desc="Describing"):
        rec = engine.describe_image(img, passes=args.passes.split(","))

        # write JSON
        with open(out / "json" / f"{img.stem}.json", "w") as f:
            json.dump(rec, f, indent=2, ensure_ascii=False)

        # CSV row
        exporter.add_flat(Record(**rec).dict_flat())

        # prompt line
        with open(prompt_path, "a") as f:
            f.write(prompt_line(rec) + "\n")

    exporter.close()
    print(f"\nWrote JSON → {out/'json'}")
    print(f"CSV        → {out/'descriptors.csv'}")
    print(f"Prompts    → {prompt_path}")


if __name__ == "__main__":
    main()
