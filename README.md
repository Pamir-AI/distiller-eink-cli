# E-ink Composer

A Python library and CLI tool for creating layered image compositions optimized for e-ink displays. Features Floyd-Steinberg dithering, layer-based composition, and built-in text rendering.

## Features

- **Layer-based composition**: Add images, text, and shapes in layers
- **Advanced dithering**: Floyd-Steinberg and threshold dithering for optimal e-ink display
- **Image processing**: Resize (stretch/fit/crop), brightness/contrast adjustment, transformations
- **Built-in text rendering**: Scalable 6x8 bitmap font with rotation, flipping, and background options
- **Multiple output formats**: PNG, BMP, and binary (packed bits)
- **CLI and Python API**: Use as command-line tool or Python library
- **Hardware integration**: Direct display on Distiller CM5 e-ink hardware

## Installation

### Distiller CM5 (Pre-installed)

The e-ink composer is pre-installed on Distiller CM5 systems at `/home/distiller/projects/eink-ui`.

To use it:
```bash
cd /home/distiller/projects/eink-ui
source venv/bin/activate
source /opt/distiller-cm5-sdk/activate.sh  # For hardware support
```

### Other Systems

```bash
git clone <repository>
cd eink-ui
python -m venv venv
source venv/bin/activate
pip install -e .
```

## Quick Start

### Python One-Liners

Quick examples for common tasks:

```python
# Display "Hello World" on e-ink hardware
python -c "from eink_composer import EinkComposer; from distiller_cm5_sdk.hardware.eink import Display; c = EinkComposer(128, 250); c.add_text_layer('hi', 'HELLO WORLD', x=20, y=120); c.save('/tmp/hi.png'); Display().display_image('/tmp/hi.png')"

# Create a simple display with border
python -c "from eink_composer import EinkComposer; c = EinkComposer(128, 250); c.add_rectangle_layer('bg', width=128, height=250, filled=True, color=255); c.add_text_layer('text', 'E-INK', x=40, y=120); c.add_rectangle_layer('border', width=128, height=250, filled=False); c.save('quick.png')"

# Display current time
python -c "import time; from eink_composer import EinkComposer; from distiller_cm5_sdk.hardware.eink import Display; c = EinkComposer(128, 250); c.add_text_layer('time', time.strftime('%H:%M'), x=35, y=120); c.save('/tmp/time.png'); Display().display_image('/tmp/time.png')"

# Show system info
python -c "import os; from eink_composer import EinkComposer; from distiller_cm5_sdk.hardware.eink import Display; c = EinkComposer(128, 250); c.add_text_layer('t1', 'SYSTEM INFO', x=25, y=30); c.add_text_layer('t2', f'CPU: {os.cpu_count()} cores', x=10, y=60); c.add_text_layer('t3', f'User: {os.getlogin()}', x=10, y=80); c.save('/tmp/info.png'); Display().display_image('/tmp/info.png')"

# Display with dithered image (requires PIL)
python -c "from eink_composer import EinkComposer; from distiller_cm5_sdk.hardware.eink import Display; c = EinkComposer(128, 250); c.add_image_layer('img', 'photo.jpg', resize_mode='fit', dither_mode='floyd-steinberg'); c.save('/tmp/photo.png'); Display().display_image('/tmp/photo.png')"

# Display image with rotation and custom crop
python -c "from eink_composer import EinkComposer; from distiller_cm5_sdk.hardware.eink import Display; c = EinkComposer(128, 250); c.add_image_layer('img', 'photo.jpg', resize_mode='crop', rotate=90, crop_x=50, crop_y=100); c.save('/tmp/photo.png'); Display().display_image('/tmp/photo.png')"
```

### Hardware Display (Distiller CM5)

If you have the Distiller CM5 hardware with e-ink display:

```bash
# Setup (one time)
cd /home/distiller/projects/eink-ui
source venv/bin/activate
source /opt/distiller-cm5-sdk/activate.sh

# IMPORTANT: Always create composition first!
# Standard e-ink display is 128x250 (width x height)

# Working example:
eink-compose create --size 128x250
eink-compose add-text hello "HELLO E-INK" --x 20 --y 120
eink-compose add-rect border --width 128 --height 250 --filled false
eink-compose display

# More complete example:
eink-compose create --size 128x250
eink-compose add-rect bg --width 128 --height 250 --filled true --color 255
eink-compose add-text title "E-INK DISPLAY" --x 15 --y 50
eink-compose add-text info "128 x 250 px" --x 25 --y 70
eink-compose add-rect frame --x 10 --y 100 --width 108 --height 50 --filled false
eink-compose display --save-preview preview.png

# Hardware controls
eink-compose hardware info    # Show display info
eink-compose hardware clear   # Clear display
eink-compose hardware sleep   # Put display to sleep
```

### Python API

```python
from eink_composer import EinkComposer

# Create a 128x250 composition (standard e-ink size)
composer = EinkComposer(128, 250)

# Add background (white)
composer.add_rectangle_layer("bg", width=128, height=250, filled=True, color=255)

# Add title text with styling
composer.add_text_layer("title", "Weather Station", x=10, y=10, font_size=2, background=True)

# Add background image with dithering
composer.add_image_layer("photo", "background.jpg", resize_mode="fit", dither_mode="floyd-steinberg")

# Add QR code image with custom size
composer.add_image_layer("qr", "qrcode.png", x=80, y=180, width=50, height=50)

# Add rotated image with custom crop position
composer.add_image_layer("banner", "banner.jpg", resize_mode="crop", rotate=90, crop_x=100, crop_y=0)

# Add a border
composer.add_rectangle_layer("border", x=0, y=0, width=128, height=250, filled=False)

# Render and save
composer.save("display.png", format="png")
composer.save("display.bin", format="binary")  # For e-ink hardware

# Display on hardware (if SDK available)
try:
    from distiller_cm5_sdk.hardware.eink import Display, DisplayMode
    display = Display()
    display.display_image("display.png", mode=DisplayMode.FULL)
except ImportError:
    print("SDK not available - saved to file only")
```

### CLI Usage

```bash
# Create new composition
eink-compose create --size 128x250

# Add layers
eink-compose add-image background background.jpg --resize-mode fit
eink-compose add-text title "Weather Station" --x 10 --y 10 --font-size 2 --background
eink-compose add-image qr qrcode.png --x 80 --y 50 --width 50 --height 50
eink-compose add-rect border --width 128 --height 250 --filled false

# Add image with rotation and custom crop
eink-compose add-image photo photo.jpg --resize-mode crop --rotate 90 --crop-x 50 --crop-y 100

# List layers
eink-compose list

# Render output
eink-compose render --output display.png --format png
eink-compose render --output display.bin --format binary --dither floyd-steinberg

# Display on hardware (requires SDK activated)
eink-compose display                    # Full refresh
eink-compose display --partial          # Fast refresh (may ghost)
eink-compose display --rotate --flip-h  # With transformations

# Save/load compositions
eink-compose save weather-template.json
eink-compose load weather-template.json --render --output final.png
```

## Complete Example

A comprehensive example showing all SDK capabilities:

```python
from eink_composer import EinkComposer
from distiller_cm5_sdk.hardware.eink import Display, DisplayMode
import numpy as np

# Create composer
composer = EinkComposer(128, 250)

# 1. Add gradient background
gradient = np.zeros((250, 128), dtype=np.uint8)
for y in range(250):
    gradient[y, :] = int(255 * (y / 250))
    
# Add as image layer with dithering
from eink_composer.composer import ImageLayer
bg_layer = ImageLayer(id="bg", image_data=gradient, dither_mode="floyd-steinberg")
composer.layers.append(bg_layer)

# 2. Add shapes
composer.add_rectangle_layer("header", x=0, y=0, width=128, height=30, 
                            filled=True, color=0)

# 3. Add text
composer.add_text_layer("title", "E-INK DISPLAY", x=20, y=10, color=255)
composer.add_text_layer("info", "Hello World!", x=10, y=50)

# 4. Add image
composer.add_image_layer("logo", "logo.png", x=10, y=80, 
                        resize_mode="fit", dither_mode="floyd-steinberg")

# 4b. Add rotated and cropped image
composer.add_image_layer("photo", "photo.jpg", x=10, y=140,
                        resize_mode="crop", rotate=90, 
                        crop_x=0, crop_y=0)  # Crop from top-left after rotation

# 5. Add graphics (bar chart)
for i in range(5):
    height = 10 + i * 5
    composer.add_rectangle_layer(f"bar_{i}", x=10+i*20, y=150-height, 
                                width=15, height=height, filled=True)

# 6. Save and display
composer.save("display.png")
display = Display()
display.display_image("display.png", mode=DisplayMode.FULL)
```

### Full Showcase Demo

Run the complete showcase demonstrating all features:

```bash
# Activates SDK and runs full demo
source /opt/distiller-cm5-sdk/activate.sh
cd /home/distiller/projects/eink-ui
source venv/bin/activate

# Run showcase (creates multiple examples)
python showcase_full_demo.py

# Or run the complete example
python complete_example.py
```

The showcase includes:
- **Backgrounds**: Solid colors, gradients, patterns
- **Text**: Multiple fonts sizes, positioning, white-on-black
- **Shapes**: Rectangles, borders, progress bars, charts
- **Images**: With resize modes and dithering options
- **Composition**: Layered elements with transparency effects
- **Real-world examples**: Weather display, badges, menus

## Advanced Features

### Text Styling Options

- **Font scaling**: `font_size` parameter scales the 6x8 bitmap font
  - `font_size=1`: Normal 6x8 pixels per character
  - `font_size=2`: Double size 12x16 pixels per character
  - `font_size=3`: Triple size 18x24 pixels per character

- **Text transformations**:
  - `rotate`: Rotation in degrees (supports any value, including negatives)
  - `flip_h`: Horizontal flip (useful for mirrored displays)
  - `flip_v`: Vertical flip

- **Text background**:
  - `background=True`: Adds white background behind text
  - `padding`: Controls spacing around background (default: 2 pixels)

```python
# Text examples
composer.add_text_layer("title", "Big Title", font_size=3, background=True, padding=5)
composer.add_text_layer("rotated", "Rotated Text", rotate=90, flip_h=True)
```

```bash
# CLI text examples
eink-compose add-text title "Big Title" --font-size 3 --background --padding 5
eink-compose add-text rotated "Rotated Text" --rotate 90 --flip-h
```

### Image Processing Options

- **Custom dimensions**: Specify exact width and height for images
  - `width`: Custom width in pixels (overrides resize calculation)
  - `height`: Custom height in pixels (overrides resize calculation)

```python
# Fixed size image (great for QR codes)
composer.add_image_layer("qr", "qrcode.png", x=10, y=10, width=50, height=50)
```

```bash
# CLI custom size
eink-compose add-image qr qrcode.png --x 10 --y 10 --width 50 --height 50
```

- **Resize modes**: 
  - `stretch`: Resize to exact dimensions (may distort)
  - `fit`: Maintain aspect ratio, add background
  - `crop`: Maintain aspect ratio, crop excess

- **Crop positioning** (for `crop` mode):
  - `crop_x`: X position for crop (None = center)
  - `crop_y`: Y position for crop (None = center)
  - Coordinates are relative to the resized image before cropping

- **Dithering modes**:
  - `floyd-steinberg`: Error diffusion for smooth gradients
  - `threshold`: Simple threshold (faster)
  - `none`: No dithering

- **Image transformations** (applied before resizing):
  - `rotate`: Rotation in degrees (0, 90, 180, 270)
  - `flip_h`: Horizontal flip
  - `flip_v`: Vertical flip

- **Render transformations** (applied to final output):
  - `flip-h`: Horizontal flip
  - `flip-v`: Vertical flip  
  - `rotate-90`: Counter-clockwise rotation
  - `invert`: Invert colors

### Layer Management

```python
# Update layer properties
composer.update_layer("title", text="New Title", x=20)

# Toggle visibility
composer.toggle_layer("qr")

# Remove layer
composer.remove_layer("background")

# Get layer info
layers = composer.get_layer_info()
```

### Custom Rendering

```python
# Render with options
image = composer.render(
    background_color=255,  # White background
    final_dither="floyd-steinberg",  # Final dithering pass
    transformations=["flip-h", "invert"]  # Apply transformations
)

# Get binary data for e-ink hardware
binary_data = composer.render_binary()
```

## Examples

### Image Rotation and Cropping
```python
# Rotate image 90 degrees and crop from center (default)
composer = EinkComposer(128, 250)
composer.add_image_layer("photo", "portrait.jpg", resize_mode="crop", rotate=90)

# Rotate and crop from specific position
composer.add_image_layer("photo", "landscape.jpg", 
                        resize_mode="crop", rotate=90,
                        crop_x=100, crop_y=0)  # Crop from top after rotation

# Multiple transformations
composer.add_image_layer("photo", "image.jpg",
                        resize_mode="crop",
                        rotate=180,      # Rotate 180 degrees
                        flip_h=True,     # Then flip horizontally
                        crop_x=0,        # Crop from left
                        crop_y=50)       # 50 pixels from top

# CLI examples
eink-compose add-image photo1 image.jpg --resize-mode crop --rotate 90
eink-compose add-image photo2 image.jpg --resize-mode crop --rotate 90 --crop-x 0 --crop-y 0
eink-compose add-image photo3 image.jpg --resize-mode crop --flip-h --rotate 180
```

### Dashboard Display
```python
composer = EinkComposer(250, 128)
composer.add_text_layer("date", "2024-01-15", x=5, y=5)
composer.add_text_layer("time", "14:30", x=5, y=20)
composer.add_image_layer("icon", "weather-icon.png", x=200, y=5, resize_mode="fit")
composer.add_text_layer("temp", "22C", x=5, y=50)
composer.save("dashboard.png")
```

### QR Code Badge
```python
composer = EinkComposer(200, 200)
composer.add_rectangle_layer("bg", width=200, height=200, filled=True, color=255)
composer.add_image_layer("qr", "contact-qr.png", x=50, y=20, width=100, height=100)
composer.add_text_layer("name", "John Doe", x=60, y=150)
composer.add_text_layer("title", "Engineer", x=65, y=165)
composer.save("badge.png")
```

## Binary Format

The binary output format packs pixels as bits (8 pixels per byte, MSB first):
- White pixel = 1
- Black pixel = 0
- No row padding
- Total size = (width * height) / 8 bytes

## Troubleshooting

### "eink-compose not found"
```bash
cd /home/distiller/projects/eink-ui
source venv/bin/activate
pip install -e .  # Install in development mode
```

### "Failed to display PNG image"
Make sure you:
1. Created a composition first: `eink-compose create --size 128x250`
2. Added content to it (empty compositions fail)
3. Have the SDK activated: `source /opt/distiller-cm5-sdk/activate.sh`

### Wrong display dimensions
The standard e-ink display is **128x250** (width x height), not 250x128.

### Empty or tiny PNG files
This happens when no layers are added. Always add at least one layer:
```bash
eink-compose create --size 128x250
eink-compose add-text test "TEST" --x 50 --y 120
eink-compose display
```

## License

MIT License