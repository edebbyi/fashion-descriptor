#!/usr/bin/env python3
"""
Test script to verify Gemini captioner works correctly.
Run: python test_gemini.py
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def test_gemini_import():
    """Test that Gemini captioner can be imported"""
    print("✓ Testing Gemini import...")
    try:
        from src.visual_descriptor.captioners.gemini_vlm import GeminiVLM
        print("  ✅ GeminiVLM imported successfully")
        return True
    except ImportError as e:
        print(f"  ❌ Failed to import GeminiVLM: {e}")
        print("  Install: pip install google-generativeai")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_gemini_init():
    """Test that Gemini can be initialized"""
    print("\n✓ Testing Gemini initialization...")
    
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("  ⚠️  GEMINI_API_KEY not set (will fail on actual API call)")
        print("  Get key from: https://aistudio.google.com/app/apikey")
        return False
    
    try:
        from src.visual_descriptor.captioners.gemini_vlm import GeminiVLM
        vlm = GeminiVLM()
        print(f"  ✅ Initialized GeminiVLM successfully")
        print(f"  Model: gemini-2.0-flash-exp")
        return True
    except Exception as e:
        print(f"  ❌ Failed to initialize: {e}")
        return False

def test_engine():
    """Test that Engine can load Gemini backend"""
    print("\n✓ Testing Engine with Gemini...")
    
    try:
        from src.visual_descriptor.engine import Engine
        engine = Engine(model="gemini")
        backend_name = type(engine.model).__name__
        print(f"  ✅ Engine loaded with backend: {backend_name}")
        
        if backend_name == "GeminiVLM":
            print("  🎉 Gemini backend active!")
            return True
        else:
            print(f"  ⚠️  Expected GeminiVLM, got {backend_name}")
            return False
    except Exception as e:
        print(f"  ❌ Failed to load engine: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_schema():
    """Test that schema validation works"""
    print("\n✓ Testing schema validation...")
    
    try:
        from src.visual_descriptor.schema import Record
        
        # Test record
        test_data = {
            "image_id": "test",
            "garment_type": "dress",
            "silhouette": "A-line",
            "fabric": {
                "type": "jersey",
                "texture": "smooth",
                "weight": "medium",
                "finish": "matte"
            }
        }
        
        rec = Record(**test_data)
        print("  ✅ Schema validation passed")
        return True
    except Exception as e:
        print(f"  ❌ Schema validation failed: {e}")
        return False

def main():
    print("🧪 Visual Descriptor - Gemini Setup Test\n")
    print("=" * 50)
    
    results = []
    
    # Run tests
    results.append(("Import", test_gemini_import()))
    results.append(("Init", test_gemini_init()))
    results.append(("Engine", test_engine()))
    results.append(("Schema", test_schema()))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print()
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name:.<20} {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("  1. Set GEMINI_API_KEY environment variable")
        print("  2. Run: make api")
        print("  3. Test: curl http://localhost:8000/debug")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
