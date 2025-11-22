#!/usr/bin/env python3
"""Generate app icon for File Queue Viewer"""

from PIL import Image, ImageDraw, ImageFont
import os

# Create icon sizes for macOS
SIZES = [16, 32, 64, 128, 256, 512, 1024]

# Create iconset directory
iconset_dir = "AppIcon.iconset"
os.makedirs(iconset_dir, exist_ok=True)

for size in SIZES:
    # Create image with gradient background
    img = Image.new('RGB', (size, size), color='#4A90E2')
    draw = ImageDraw.Draw(img)

    # Draw folder icon representation (simple rounded rectangle)
    margin = size // 8
    folder_top = size // 3

    # Folder body
    draw.rounded_rectangle(
        [(margin, folder_top), (size - margin, size - margin)],
        radius=size // 16,
        fill='#5DA3F5'
    )

    # Folder tab
    tab_width = size // 2
    draw.rounded_rectangle(
        [(margin, folder_top - size//8), (margin + tab_width, folder_top)],
        radius=size // 32,
        fill='#5DA3F5'
    )

    # Add checkmark
    check_size = size // 4
    check_x = size - margin - check_size
    check_y = size - margin - check_size

    # Draw circle background for checkmark
    draw.ellipse(
        [(check_x - check_size//4, check_y - check_size//4),
         (check_x + check_size + check_size//4, check_y + check_size + check_size//4)],
        fill='#4CAF50'
    )

    # Draw checkmark (simplified)
    check_thickness = max(2, size // 64)
    draw.line(
        [(check_x + check_size//4, check_y + check_size//2),
         (check_x + check_size//2, check_y + check_size*3//4)],
        fill='white',
        width=check_thickness
    )
    draw.line(
        [(check_x + check_size//2, check_y + check_size*3//4),
         (check_x + check_size, check_y + check_size//4)],
        fill='white',
        width=check_thickness
    )

    # Save as PNG with proper naming for iconset
    filename = f"icon_{size}x{size}.png"
    if size >= 32:  # Also create @2x versions
        img.save(os.path.join(iconset_dir, filename))
        if size <= 512:
            filename_2x = f"icon_{size//2}x{size//2}@2x.png"
            img.save(os.path.join(iconset_dir, filename_2x))
    else:
        img.save(os.path.join(iconset_dir, filename))

print(f"✓ Created icon files in {iconset_dir}/")
print("Converting to .icns format...")

# Convert to .icns using iconutil
os.system(f"iconutil -c icns {iconset_dir}")

# Move to Resources
os.system(f"mv AppIcon.icns FileQueueViewer.app/Contents/Resources/")

# Clean up
os.system(f"rm -rf {iconset_dir}")

print("✓ AppIcon.icns created and installed")
