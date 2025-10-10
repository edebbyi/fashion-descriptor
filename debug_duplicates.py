#!/usr/bin/env python3
"""Debug script to check for duplicate detection in enumerate_inputs."""

import tempfile
import zipfile
from pathlib import Path
import sys
from collections import Counter

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from visual_descriptor.engine import Engine
from visual_descriptor.utils import is_image

def debug_duplicates():
    """Check if enumerate_inputs is producing duplicates."""
    
    # Create a minimal PNG image data
    png_data = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 dimensions
        0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,  # bit depth, color type, etc.
        0x89, 0x00, 0x00, 0x00, 0x0B, 0x49, 0x44, 0x41,  # IDAT chunk
        0x54, 0x78, 0x9C, 0x62, 0x00, 0x02, 0x00, 0x00,
        0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00,
        0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE,  # IEND chunk
        0x42, 0x60, 0x82
    ])
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        zip_path = temp_path / "test.zip"
        extract_dir = temp_path / "extracted"
        extract_dir.mkdir()
        
        # Create a ZIP with exactly 4 images
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr('image1.png', png_data)
            zf.writestr('image2.jpg', png_data)
            zf.writestr('folder/image3.png', png_data)
            zf.writestr('folder/image4.jpg', png_data)
        
        print(f"🔍 Created ZIP with 4 images")
        
        # Extract it
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            extracted_files = zip_ref.namelist()
            print(f"📦 ZIP contains: {extracted_files}")
        
        # Check all files after extraction
        all_files = [f for f in extract_dir.rglob("*") if f.is_file()]
        print(f"📂 After extraction, found {len(all_files)} files:")
        for f in all_files:
            rel_path = f.relative_to(extract_dir)
            print(f"  📄 {rel_path} -> is_image: {is_image(f)}")
        
        # Test enumerate_inputs
        engine = Engine()
        image_paths = engine.enumerate_inputs(extract_dir)
        print(f"\n🔍 enumerate_inputs found {len(image_paths)} images:")
        
        # Check for duplicates
        path_strings = [str(p) for p in image_paths]
        path_counter = Counter(path_strings)
        
        for image_path in image_paths:
            rel_path = image_path.relative_to(extract_dir)
            print(f"  🖼️  {rel_path}")
        
        # Report duplicates
        duplicates = [(path, count) for path, count in path_counter.items() if count > 1]
        if duplicates:
            print(f"\n❌ DUPLICATES FOUND:")
            for path, count in duplicates:
                print(f"  {path} appears {count} times")
        else:
            print(f"\n✅ No duplicates found")
        
        print(f"\nSummary:")
        print(f"  Files in ZIP: 4")
        print(f"  Files extracted: {len(all_files)}")
        print(f"  Images found: {len(image_paths)}")
        print(f"  Unique images: {len(set(path_strings))}")

if __name__ == "__main__":
    debug_duplicates()