#!/usr/bin/env python3
"""
Favicon Generator Script for NDtech POS
Generates missing favicon files from existing icon-512.png

Requirements: pip install Pillow

Usage: python generate_favicons.py
"""

import os
import sys
from PIL import Image

def create_favicons():
    """Generate missing favicon files from icon-512.png"""
    
    # Paths
    static_dir = "nano/static/nano"
    source_icon = os.path.join(static_dir, "icon-512.png")
    
    # Check if source icon exists
    if not os.path.exists(source_icon):
        print(f"❌ Error: Source icon {source_icon} not found!")
        print("Please ensure icon-512.png exists in nano/static/nano/")
        return False
    
    # Sizes to generate
    sizes = {
        "favicon.ico": [16, 32, 48],  # Multi-size ICO
        "icon-16.png": 16,
        "icon-32.png": 32,
        "icon-36.png": 36,
        "icon-48.png": 48,
        "icon-57.png": 57,
        "icon-60.png": 60,
        "icon-76.png": 76,
        "icon-114.png": 114,
        "icon-120.png": 120,
        "icon-180.png": 180,
        "icon-256.png": 256,
    }
    
    try:
        # Open source image
        print(f"📖 Opening source image: {source_icon}")
        with Image.open(source_icon) as img:
            # Convert to RGB if necessary (for ICO format)
            img_rgb = img.convert('RGB')
            
            # Generate PNG icons
            for filename, size in sizes.items():
                if filename == "favicon.ico":
                    continue  # Handle separately
                    
                output_path = os.path.join(static_dir, filename)
                
                # Skip if file exists
                if os.path.exists(output_path):
                    print(f"⏭️  Skipping {filename} (already exists)")
                    continue
                
                # Resize and save
                resized_img = img.resize((size, size), Image.Resampling.LANCZOS)
                resized_img.save(output_path, "PNG", optimize=True)
                print(f"✅ Generated {filename} ({size}x{size})")
            
            # Generate favicon.ico with multiple sizes
            favicon_path = os.path.join(static_dir, "favicon.ico")
            if not os.path.exists(favicon_path):
                # Create multiple sizes for ICO
                icon_sizes = [(16, 16), (32, 32), (48, 48)]
                icons = []
                
                for size in icon_sizes:
                    resized = img_rgb.resize(size, Image.Resampling.LANCZOS)
                    icons.append(resized)
                
                # Save as ICO
                icons[0].save(favicon_path, format="ICO", sizes=[(s.width, s.height) for s in icons])
                print(f"✅ Generated favicon.ico (multi-size)")
            else:
                print("⏭️  Skipping favicon.ico (already exists)")
            
            print("\n🎉 Favicon generation completed!")
            return True
            
    except Exception as e:
        print(f"❌ Error generating favicons: {e}")
        return False

def check_requirements():
    """Check if required packages are installed"""
    try:
        from PIL import Image
        return True
    except ImportError:
        print("❌ Error: PIL/Pillow is not installed!")
        print("Install it with: pip install Pillow")
        return False

def main():
    """Main function"""
    print("🚀 NDtech POS Favicon Generator")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Generate favicons
    if create_favicons():
        print("\n📋 Next Steps:")
        print("1. Restart Django development server")
        print("2. Clear browser cache")
        print("3. Test favicon in browser")
        print("4. Check for any 404 errors in DevTools")
        print("\n💡 Tip: Use https://realfavicongenerator.net/favicon_checker to test!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
