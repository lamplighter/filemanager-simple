#!/usr/bin/env python3
"""Generate app icon for File Queue Viewer - Card File Box style"""

from PIL import Image, ImageDraw
import os

# Create icon sizes for macOS
SIZES = [16, 32, 64, 128, 256, 512, 1024]

# Create iconset directory
iconset_dir = "AppIcon.iconset"
os.makedirs(iconset_dir, exist_ok=True)

for size in SIZES:
    # Create image with gradient background
    img = Image.new('RGB', (size, size), color='#E8EAF6')  # Light indigo background
    draw = ImageDraw.Draw(img)

    # Card file box design - like an index card holder
    margin = size // 8
    box_height = int(size * 0.6)
    box_width = int(size * 0.7)
    box_x = (size - box_width) // 2
    box_y = (size - box_height) // 2 + margin // 2

    # Main box body (darker gray-blue)
    draw.rounded_rectangle(
        [(box_x, box_y), (box_x + box_width, box_y + box_height)],
        radius=size // 20,
        fill='#5C6BC0'  # Indigo
    )

    # Draw 3 cards/tabs sticking up from the box
    card_width = box_width // 4
    card_height = box_height // 3
    card_spacing = (box_width - card_width * 3) // 4

    for i in range(3):
        card_x = box_x + card_spacing + i * (card_width + card_spacing)
        card_y = box_y - card_height // 2

        # Card/tab
        draw.rounded_rectangle(
            [(card_x, card_y), (card_x + card_width, card_y + card_height)],
            radius=size // 40,
            fill='#7986CB' if i == 1 else '#9FA8DA'  # Middle card lighter
        )

    # Add a subtle checkmark or indicator on the front
    check_size = size // 6
    check_x = box_x + box_width // 2 - check_size // 2
    check_y = box_y + box_height // 2

    # Small badge/circle for the checkmark
    badge_radius = check_size
    draw.ellipse(
        [(check_x - badge_radius//2, check_y - badge_radius//2),
         (check_x + badge_radius + badge_radius//2, check_y + badge_radius + badge_radius//2)],
        fill='#4CAF50'  # Green
    )

    # Checkmark
    check_thickness = max(2, size // 48)
    draw.line(
        [(check_x, check_y + check_size//4),
         (check_x + check_size//3, check_y + check_size//2)],
        fill='white',
        width=check_thickness
    )
    draw.line(
        [(check_x + check_size//3, check_y + check_size//2),
         (check_x + check_size, check_y - check_size//4)],
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

print(f"✓ Created icon files in {iconset_dir}/ (card file box design)")
print("Converting to .icns format...")

# Convert to .icns using iconutil
os.system(f"iconutil -c icns {iconset_dir}")

# Move to Resources
os.system(f"mv AppIcon.icns FileQueueViewer.app/Contents/Resources/")

# Clean up
os.system(f"rm -rf {iconset_dir}")

print("✓ AppIcon.icns created and installed")
