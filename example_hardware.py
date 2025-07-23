#!/usr/bin/env python3
"""
Example: Using eink-composer with the Distiller CM5 hardware
"""

from eink_composer import EinkComposer
from distiller_cm5_sdk.hardware.eink import Display
import time

# Create a composition
print("Creating e-ink composition...")
composer = EinkComposer(250, 128)

# Add background
composer.add_rectangle_layer("bg", width=250, height=128, filled=True, color=255)

# Add header
composer.add_rectangle_layer("header", width=250, height=30, filled=True, color=0)
composer.add_text_layer("title", "DISTILLER CM5", x=75, y=10, color=255)

# Add current time
current_time = time.strftime("%H:%M:%S")
current_date = time.strftime("%Y-%m-%d")
composer.add_text_layer("time", f"TIME: {current_time}", x=10, y=45)
composer.add_text_layer("date", f"DATE: {current_date}", x=10, y=65)

# Add some status info
composer.add_text_layer("status", "STATUS: READY", x=10, y=85)
composer.add_text_layer("mode", "MODE: DEMO", x=10, y=100)

# Add a QR code placeholder (just a pattern for demo)
composer.add_rectangle_layer("qr_border", x=170, y=45, width=70, height=70, 
                            filled=False, color=0)
# Create QR-like pattern
for i in range(0, 60, 10):
    for j in range(0, 60, 10):
        if (i + j) % 20 == 0:
            composer.add_rectangle_layer(f"qr_{i}_{j}", 
                                       x=175+i, y=50+j, 
                                       width=8, height=8,
                                       filled=True, color=0)

# Save the composition
print("Saving composition...")
composer.save("hardware_demo.png", format="png")

# Display on e-ink hardware
print("Displaying on e-ink...")
try:
    display = Display()
    display.display_image("hardware_demo.png", refresh_mode=Display.RefreshMode.FULL)
    print("✓ Successfully displayed on e-ink hardware!")
except Exception as e:
    print(f"Note: E-ink hardware not available in this environment: {e}")
    print("The image was saved as 'hardware_demo.png'")

# Also save as binary for direct hardware use
composer.save("hardware_demo.bin", format="binary")
print("\nAlso saved as:")
print("- hardware_demo.png (for preview)")
print("- hardware_demo.bin (for direct hardware use)")

# Show how to use with different display modes
print("\nDisplay options:")
print("- Full refresh: display.display_image('image.png', refresh_mode=Display.RefreshMode.FULL)")
print("- With rotation: display.display_image('image.png', rotate_ccw_90=True)")
print("- With flip: display.display_image('image.png', flip_horizontal=True)")
print("- Clear display: display.clear()")
print("- Sleep mode: display.sleep()")