#!/usr/bin/env python
"""Quick test script for image generation.

Usage:
    # Mock mode (instant, no API needed)
    python test_generate.py "a cloud computing concept"
    
    # Replicate mode (real images, needs API token)
    REPLICATE_API_TOKEN=your_token python test_generate.py "a cloud computing concept" --backend replicate
"""

import asyncio
import sys
import webbrowser

# Add src to path
sys.path.insert(0, ".")

from src.core.types import AssetType, ModelId, QualityPreset


async def test_generation(prompt: str, backend: str = "mock"):
    """Test image generation with the specified backend."""
    from src.ml import get_generator
    
    print(f"\n🎨 Noisett Image Generation Test")
    print(f"=" * 50)
    print(f"Prompt: {prompt}")
    print(f"Backend: {backend}")
    print()
    
    try:
        generator = get_generator(backend)
        print(f"✓ Generator initialized: {type(generator).__name__}")
    except ValueError as e:
        print(f"✗ Error: {e}")
        return
    
    print(f"⏳ Generating 2 images...")
    
    try:
        images = await generator.generate(
            prompt=prompt,
            asset_type=AssetType.PRODUCT,
            model=ModelId.HIDREAM,
            quality=QualityPreset.STANDARD,
            count=2,
        )
        
        print(f"\n✅ Generated {len(images)} images!\n")
        
        for img in images:
            print(f"  Image {img.index + 1}:")
            print(f"    URL: {img.url}")
            print(f"    Size: {img.width}x{img.height}")
            if img.seed:
                print(f"    Seed: {img.seed}")
            print()
        
        # Open first image in browser
        if images:
            print(f"🌐 Opening first image in browser...")
            webbrowser.open(images[0].url)
            
    except Exception as e:
        print(f"✗ Generation failed: {e}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Noisett image generation")
    parser.add_argument("prompt", help="Text prompt for image generation")
    parser.add_argument(
        "--backend", 
        choices=["mock", "huggingface", "hf", "replicate"], 
        default="mock",
        help="Generation backend (default: mock)"
    )
    
    args = parser.parse_args()
    
    asyncio.run(test_generation(args.prompt, args.backend))


if __name__ == "__main__":
    main()
