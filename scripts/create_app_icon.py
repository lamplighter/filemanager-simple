#!/usr/bin/env python3
"""Generate app icon for File Queue Viewer using emoji"""

from PIL import Image, ImageDraw, ImageFont
import os

# Create icon sizes for macOS
SIZES = [16, 32, 64, 128, 256, 512, 1024]

# Icon configuration
EMOJI = "🗂️"  # Card File Box
BACKGROUND_COLOR = "#F3F4F6"  # Light gray background for contrast

# Try to find a system font that supports emoji
FONT_PATHS = [
    "/System/Library/Fonts/Apple Color Emoji.ttc",
    "/System/Library/Fonts/AppleColorEmoji.ttf",
    "/Library/Fonts/Apple Color Emoji.ttc",
]

def get_emoji_font(size):
    """Get emoji font at specified size"""
    for font_path in FONT_PATHS:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except:
                pass
    # Fallback to default font
    return ImageFont.load_default()

# Create iconset directory
iconset_dir = "AppIcon.iconset"
os.makedirs(iconset_dir, exist_ok=True)

for size in SIZES:
    # Create image with light background
    img = Image.new('RGB', (size, size), color=BACKGROUND_COLOR)
    draw = ImageDraw.Draw(img)

    # Calculate emoji size (80% of icon size for nice padding)
    emoji_size = int(size * 0.8)
    font = get_emoji_font(emoji_size)

    # Get text bounding box to center it
    bbox = draw.textbbox((0, 0), EMOJI, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Center the emoji
    x = (size - text_width) // 2 - bbox[0]
    y = (size - text_height) // 2 - bbox[1]

    # Draw emoji
    draw.text((x, y), EMOJI, font=font, fill='black', embedded_color=True)

    # Save as PNG with proper naming for iconset
    filename = f"icon_{size}x{size}.png"
    if size >= 32:  # Also create @2x versions
        img.save(os.path.join(iconset_dir, filename))
        if size <= 512:
            filename_2x = f"icon_{size//2}x{size//2}@2x.png"
            img.save(os.path.join(iconset_dir, filename_2x))
    else:
        img.save(os.path.join(iconset_dir, filename))

print(f"✓ Created icon files in {iconset_dir}/ using {EMOJI} emoji")
print("Converting to .icns format...")

# Convert to .icns using iconutil
os.system(f"iconutil -c icns {iconset_dir}")

# Move to Resources
os.system(f"mv AppIcon.icns FileQueueViewer.app/Contents/Resources/")

# Clean up
os.system(f"rm -rf {iconset_dir}")

print("✓ AppIcon.icns created and installed")
