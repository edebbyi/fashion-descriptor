#!/usr/bin/env python3
"""Debug script to understand ZIP file processing issues."""

import zipfile
import tempfile
from pathlib import Path
import sys

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from visual_descriptor.engine import Engine
from visual_descriptor.utils import is_image

def debug_zip_processing(zip_path: str):
    """Debug ZIP file processing to understand why images aren't found."""
    zip_path = Path(zip_path)
    
    if not zip_path.exists():
        print(f"❌ ZIP file not found: {zip_path}")
        return
    
    print(f"🔍 Debugging ZIP file: {zip_path}")
    print(f"📁 File size: {zip_path.stat().st_size} bytes")
    
    # Create temporary extraction directory
    with tempfile.TemporaryDirectory() as temp_dir:
        extracted_dir = Path(temp_dir) / "extracted"
        extracted_dir.mkdir(exist_ok=True)
        
        print(f"\n📂 Extracting to: {extracted_dir}")
        
        try:
            # Extract ZIP file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extracted_dir)
                
            print("✅ ZIP extracted successfully")
            
            # List all extracted files
            print(f"\n📋 Files in extracted directory:")
            all_files = []
            for item in extracted_dir.rglob("*"):
                if item.is_file():
                    all_files.append(item)
                    rel_path = item.relative_to(extracted_dir)
                    print(f"  📄 {rel_path} (size: {item.stat().st_size} bytes)")
                    print(f"      Extension: {item.suffix}")
                    print(f"      Is image (current logic): {is_image(item)}")
            
            if not all_files:
                print("  ❌ No files found after extraction!")
                return
                
            # Test current enumerate_inputs logic
            print(f"\n🔍 Testing current enumerate_inputs logic:")
            engine = Engine()
            found_images = engine.enumerate_inputs(extracted_dir)
            print(f"  Found {len(found_images)} images: {[img.name for img in found_images]}")
            
            # Test recursive search
            print(f"\n🔍 Testing recursive image search:")
            recursive_images = []
            for item in extracted_dir.rglob("*"):
                if item.is_file() and is_image(item):
                    recursive_images.append(item)
            
            print(f"  Found {len(recursive_images)} images recursively: {[img.name for img in recursive_images]}")
            
            # Show directory structure
            print(f"\n🌳 Directory structure:")
            for item in extracted_dir.rglob("*"):
                if item.is_dir():
                    rel_path = item.relative_to(extracted_dir)
                    print(f"  📁 {rel_path}/")
                    
        except zipfile.BadZipFile:
            print("❌ Invalid ZIP file!")
        except Exception as e:
            print(f"❌ Error extracting ZIP: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_zip.py <path_to_zip_file>")
        sys.exit(1)
    
    debug_zip_processing(sys.argv[1])