#!/usr/bin/env python3
"""Test script to verify ZIP file processing fix."""

import tempfile
import zipfile
from pathlib import Path
import sys

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from visual_descriptor.engine import Engine
from visual_descriptor.utils import is_image

def create_test_zip(zip_path: Path, structure: dict):
    """Create a test ZIP file with the given structure."""
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for file_path, content in structure.items():
            if isinstance(content, str):
                zf.writestr(file_path, content)
            elif isinstance(content, bytes):
                zf.writestr(file_path, content)

def create_sample_image_data():
    """Create minimal image data for testing."""
    # Minimal PNG file (1x1 pixel transparent)
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
    return png_data

def test_zip_structures():
    """Test different ZIP file structures."""
    
    # Test cases
    test_cases = [
        {
            "name": "Images in root directory",
            "structure": {
                "image1.png": create_sample_image_data(),
                "image2.jpg": create_sample_image_data(),
                "readme.txt": "This is a readme file"
            }
        },
        {
            "name": "Images in subdirectory",
            "structure": {
                "photos/image1.png": create_sample_image_data(),
                "photos/image2.jpg": create_sample_image_data(),
                "docs/readme.txt": "This is a readme file"
            }
        },
        {
            "name": "Mixed structure",
            "structure": {
                "root_image.png": create_sample_image_data(),
                "folder1/sub_image1.jpg": create_sample_image_data(),
                "folder1/subfolder/sub_image2.png": create_sample_image_data(),
                "folder2/document.txt": "Some text",
                "folder2/image3.webp": create_sample_image_data(),
            }
        },
        {
            "name": "No images (should fail)",
            "structure": {
                "document1.txt": "Some text",
                "folder/document2.pdf": "Fake PDF content",
                "data.json": '{"key": "value"}'
            }
        }
    ]
    
    engine = Engine()
    
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        print("=" * 50)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / "test.zip"
            extract_dir = temp_path / "extracted"
            extract_dir.mkdir()
            
            # Create test ZIP
            create_test_zip(zip_path, test_case["structure"])
            print(f"📦 Created test ZIP: {zip_path}")
            
            # Extract it
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            print(f"📂 Extracted to: {extract_dir}")
            
            # List all files in extraction
            all_files = [f for f in extract_dir.rglob("*") if f.is_file()]
            print(f"📋 All extracted files ({len(all_files)}):")
            for f in all_files:
                rel_path = f.relative_to(extract_dir)
                print(f"  📄 {rel_path} -> is_image: {is_image(f)}")
            
            # Test enumerate_inputs
            found_images = engine.enumerate_inputs(extract_dir)
            print(f"🔍 Found {len(found_images)} images via enumerate_inputs:")
            for img in found_images:
                rel_path = img.relative_to(extract_dir)
                print(f"  🖼️  {rel_path}")
            
            # Expected vs actual
            expected_images = len([f for f in all_files if is_image(f)])
            if len(found_images) == expected_images:
                print("✅ SUCCESS: Found expected number of images")
            else:
                print(f"❌ FAIL: Expected {expected_images} images, found {len(found_images)}")

if __name__ == "__main__":
    print("🧪 Testing ZIP file processing fixes...")
    test_zip_structures()
    print("\n🎉 Test complete!")