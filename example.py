#!/usr/bin/env python3
"""
Example usage of the E-ink Composer library
"""

from eink_composer import EinkComposer

# Example 1: Simple text display
print("Example 1: Simple text display")
composer = EinkComposer(250, 128)
composer.add_text_layer("title", "HELLO E-INK", x=70, y=50)
composer.save("example1_text.png")
print("  Created: example1_text.png")

# Example 2: Weather dashboard
print("\nExample 2: Weather dashboard")
composer = EinkComposer(250, 128)

# Add title
composer.add_text_layer("title", "WEATHER", x=90, y=5)

# Add temperature
composer.add_text_layer("temp", "22C", x=10, y=40)
composer.add_text_layer("temp_label", "TEMP", x=10, y=55)

# Add humidity  
composer.add_text_layer("humidity", "65%", x=200, y=40)
composer.add_text_layer("humidity_label", "HUM", x=200, y=55)

# Add border
composer.add_rectangle_layer("border", x=0, y=0, width=250, height=128, filled=False)

# Add divider line
composer.add_rectangle_layer("divider", x=0, y=25, width=250, height=1, filled=True)

composer.save("example2_weather.png")
print("  Created: example2_weather.png")

# Example 3: Image with text overlay
print("\nExample 3: Image with text overlay (using placeholder)")
composer = EinkComposer(250, 128)

# Create a gradient background using numpy
import numpy as np
gradient = np.linspace(0, 255, 250 * 128).reshape(128, 250).astype(np.uint8)

# Add as image layer
from eink_composer.composer import ImageLayer
img_layer = ImageLayer(id="gradient", image_data=gradient, dither_mode="floyd-steinberg")
composer.layers.append(img_layer)

# Add text overlay
composer.add_text_layer("overlay", "DITHERED", x=85, y=55, color=255)

composer.save("example3_dithered.png")
print("  Created: example3_dithered.png")

# Example 4: Multi-layer composition  
print("\nExample 4: Multi-layer composition")
composer = EinkComposer(250, 128)

# Background
composer.add_rectangle_layer("bg", x=0, y=0, width=250, height=128, filled=True, color=255)

# Header section
composer.add_rectangle_layer("header", x=0, y=0, width=250, height=30, filled=True, color=0)
composer.add_text_layer("header_text", "E-INK DISPLAY", x=75, y=10, color=255)

# Content boxes
composer.add_rectangle_layer("box1", x=10, y=40, width=110, height=70, filled=False)
composer.add_text_layer("box1_text", "ZONE 1", x=45, y=65)

composer.add_rectangle_layer("box2", x=130, y=40, width=110, height=70, filled=False)
composer.add_text_layer("box2_text", "ZONE 2", x=165, y=65)

composer.save("example4_layout.png")
print("  Created: example4_layout.png")

# Example 5: Binary output for hardware
print("\nExample 5: Binary output for e-ink hardware")
composer = EinkComposer(128, 64)  # Smaller display
composer.add_text_layer("msg", "READY", x=35, y=25)
composer.save("example5_binary.bin", format="binary")
print("  Created: example5_binary.bin (1024 bytes)")

# Show how to read binary data
with open("example5_binary.bin", "rb") as f:
    data = f.read()
    print(f"  Binary size: {len(data)} bytes")
    print(f"  First 8 bytes (hex): {data[:8].hex()}")

print("\nAll examples created successfully!")