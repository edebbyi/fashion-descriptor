# src/cli.py
from __future__ import annotations
import argparse, json, os, sys, glob, traceback
from typing import List, Dict, Any
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from src.visual_descriptor.engine import Engine

# Optional rich exporter (descriptors.csv + prompt_text.txt)
HAS_EXPORTER = False
try:
    from src.visual_descriptor.export_csv_prompt import CSVExporter, prompt_line
    HAS_EXPORTER = True
except Exception:
    CSVExporter, prompt_line = None, None  # type: ignore

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def list_images(root: str) -> List[str]:
    paths: List[str] = []
    for ext in IMAGE_EXTS:
        paths.extend(glob.glob(os.path.join(root, f"**/*{ext}"), recursive=True))
    return sorted(paths)


def ensure_dir(p: str) -> None:
    if p:
        os.makedirs(p, exist_ok=True)


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Visual Descriptor CLI")
    p.add_argument("--in", dest="inp", required=True, help="Input folder containing images")
    p.add_argument("--out", dest="out", required=True, help="Output folder (CSV & extras go here)")
    p.add_argument("--passes", default="A", help="Comma-separated passes (e.g., A,B,C)")
    p.add_argument("--normalize", default="yes", choices=["yes","no"], help="Normalize vocab in engine")
    p.add_argument("--model", default="openai", help="stub | blip2 | openai (matches your Engine choices)")
    p.add_argument("--csv", default="colors.csv", help="(fallback) CSV filename in --out")
    return p.parse_args(argv)


def record_id_from_path(path: str | Path) -> str:
    return Path(str(path)).stem


def _fallback_export_csv(recs: List[Dict[str, Any]], path: str) -> None:
    """
    Minimal CSV writer for key color/pattern fields.
    Always works, independent of your custom exporter.
    """
    import csv
    fields = [
        "image_id", "image_path",
        "colors.primary", "colors.secondary",
        "pattern.type", "pattern.foreground", "pattern.background",
        "pattern.scale", "pattern.density",
    ]

    def _get(d: Dict[str, Any], dotted: str):
        cur = d
        for part in dotted.split("."):
            if not isinstance(cur, dict):
                return None
            cur = cur.get(part)
        return cur

    ensure_dir(os.path.dirname(path))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in recs:
            row = {}
            for k in fields:
                if "." in k:
                    val = _get(r, k)
                    if isinstance(val, dict) and "name" in val:
                        val = val.get("name")
                else:
                    val = r.get(k)
                row[k] = val
            w.writerow(row)


def _export_descriptors_and_prompts(results: List[Dict[str, Any]], out_dir: str) -> None:
    """
    Uses your rich exporter if available.
    - descriptors.csv at outputs/descriptors.csv
    - prompt_text.txt at outputs/prompt_text.txt
    """
    if not HAS_EXPORTER or not results:
        print("[info] rich exporter not available; skipping descriptors.csv & prompt_text.txt")
        return

    # Build rows via your CSVExporter
    exporter = CSVExporter()
    for rec in results:
        try:
            exporter.add_flat(rec)
        except Exception as e:
            # keep going even if a single row fails
            print(f"[warn] exporter failed on {rec.get('image_id')}: {e}", file=sys.stderr)

    rows = exporter.export()
    if rows:
        # descriptors.csv — dynamic columns from first row keys
        import csv
        desc_path = os.path.join(out_dir, "descriptors.csv")
        with open(desc_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = list(rows[0].keys())
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print(f"[info] wrote descriptors -> {desc_path}")
    else:
        print("[info] no descriptor rows produced")

    # prompt_text.txt — one line per record
    try:
        prompt_path = os.path.join(out_dir, "prompt_text.txt")
        with open(prompt_path, "w", encoding="utf-8") as f:
            for rec in results:
                line = ""
                try:
                    pid = rec.get("image_id") or rec.get("id") or record_id_from_path(rec.get("image_path", ""))
                    text = prompt_line(rec) if prompt_line else ""
                    line = f"{pid}: {text}".strip()
                except Exception:
                    # if prompt_line fails, write a minimal fallback
                    line = f"{rec.get('image_id', '')}".strip()
                if line:
                    f.write(line + "\n")
        print(f"[info] wrote prompts -> {prompt_path}")
    except Exception as e:
        print(f"[warn] failed to write prompt_text.txt: {e}", file=sys.stderr)


def main(argv=None):
    args = parse_args(argv)
    in_dir = args.inp
    out_dir = args.out

    # Ensure outputs/ and outputs/json/ exist
    ensure_dir(out_dir)
    json_dir = os.path.join(out_dir, "json")
    ensure_dir(json_dir)

    engine = Engine(model=args.model, normalize=(args.normalize == "yes"))

    images = list_images(in_dir)
    if not images:
        print(f"[warn] no images found in: {in_dir}", file=sys.stderr)
        return 2

    pass_list = [p.strip() for p in args.passes.split(",") if p.strip()]
    results: List[Dict[str, Any]] = []

    print(f"[info] found {len(images)} images")
    for i, img in enumerate(images, 1):
        try:
            path = Path(img)
            out = engine.describe_image(path=path, passes=pass_list)
            out.setdefault("image_path", str(path))
            rid = out.get("image_id") or record_id_from_path(path)

            # WRITE JSON INTO outputs/json/<id>.json
            json_path = os.path.join(json_dir, f"{rid}.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
            print(f"[{i:>4}/{len(images)}] wrote {json_path}")

            results.append(out)
        except Exception as e:
            print(f"[error] failed on {img}: {e}", file=sys.stderr)
            traceback.print_exc()

    # Always write the simple colors.csv as a baseline
    csv_path = os.path.join(out_dir, args.csv)
    try:
        _fallback_export_csv(results, csv_path)
        print(f"[info] wrote CSV -> {csv_path}")
    except Exception as e:
        print(f"[error] failed to export CSV: {e}", file=sys.stderr)
        traceback.print_exc()

    # If available, also write descriptors.csv + prompt_text.txt in outputs/
    try:
        _export_descriptors_and_prompts(results, out_dir)
    except Exception as e:
        print(f"[warn] exporter phase failed: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())