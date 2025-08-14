#!/usr/bin/env python3
"""
Minimalist Web UI for E-ink Display Editing
Flask-based web application for the Distiller CM5 platform.
"""

from flask import Flask, render_template, request, jsonify, send_file, session
import os
import sys
import json
import uuid
import base64
import time
from io import BytesIO
from PIL import Image
import numpy as np
from pathlib import Path

# Add SDK path
sys.path.insert(0, '/opt/distiller-cm5-sdk/src')

from eink_composer import EinkComposer

# Try to import hardware display support
try:
    from distiller_cm5_sdk.hardware.eink import Display, DisplayMode
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False

app = Flask(__name__)
app.secret_key = 'eink-ui-secret-key'

# Serve templates directory as static files
from flask import send_from_directory

@app.route('/templates/<path:filename>')
def serve_template_files(filename):
    """Serve template package files."""
    return send_from_directory('templates', filename)

# Global storage for compositions (in production, use a database)
compositions = {}

def get_composition():
    """Get or create current composition."""
    session_id = session.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
    
    if session_id not in compositions:
        compositions[session_id] = EinkComposer(250, 128)
    
    return compositions[session_id]

def array_to_base64(img_array):
    """Convert numpy array to base64 image string."""
    pil_img = Image.fromarray(img_array, mode='L')
    buffer = BytesIO()
    pil_img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

@app.route('/')
def index():
    """Main page."""
    return render_template('index.html', hardware_available=HARDWARE_AVAILABLE)

@app.route('/api/preview')
def preview():
    """Get current composition preview."""
    composer = get_composition()
    img_array = composer.render()
    return jsonify({
        'image': array_to_base64(img_array),
        'width': composer.width,
        'height': composer.height
    })

@app.route('/api/layers')
def get_layers():
    """Get current layers."""
    composer = get_composition()
    return jsonify(composer.get_layer_info())

@app.route('/api/add-text', methods=['POST'])
def add_text():
    """Add text layer."""
    try:
        data = request.json
        composer = get_composition()
        
        text = data.get('text', 'TEXT').upper()  # Force uppercase for testing
        layer_id = f"text_{len(composer.layers)}"
        
        print(f"Adding text layer: '{text}' at ({data.get('x', 0)}, {data.get('y', 0)})")  # Debug
        
        composer.add_text_layer(
            layer_id=layer_id,
            text=text,
            x=int(data.get('x', 0)),
            y=int(data.get('y', 0)),
            color=int(data.get('color', 0)),
            font_size=int(data.get('font_size', 1)),
            background=data.get('background', False)
        )
        
        return jsonify({'success': True, 'layer_id': layer_id, 'debug_text': text})
    
    except Exception as e:
        print(f"Error adding text: {e}")  # Debug
        return jsonify({'error': str(e)}), 500

@app.route('/api/add-rect', methods=['POST'])
def add_rect():
    """Add rectangle layer."""
    data = request.json
    composer = get_composition()
    
    layer_id = f"rect_{len(composer.layers)}"
    composer.add_rectangle_layer(
        layer_id=layer_id,
        x=int(data.get('x', 0)),
        y=int(data.get('y', 0)),
        width=int(data.get('width', 50)),
        height=int(data.get('height', 30)),
        filled=data.get('filled', False),
        color=int(data.get('color', 0))
    )
    
    return jsonify({'success': True, 'layer_id': layer_id})

@app.route('/api/add-image', methods=['POST'])
def add_image():
    """Add image layer."""
    if 'image' not in request.files:
        return jsonify({'error': 'No image file'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    
    try:
        # Load image data directly instead of saving to temp file
        from PIL import Image as PILImage
        import numpy as np
        
        # Load image from memory
        pil_img = PILImage.open(file.stream).convert('L')
        img_array = np.array(pil_img)
        
        data = request.form
        composer = get_composition()
        
        layer_id = f"image_{len(composer.layers)}"
        
        # Create ImageLayer with image data instead of file path
        from eink_composer.composer import ImageLayer
        layer = ImageLayer(
            id=layer_id,
            x=int(data.get('x', 0)),
            y=int(data.get('y', 0)),
            image_data=img_array,
            resize_mode=data.get('resize_mode', 'fit'),
            dither_mode=data.get('dither_mode', 'floyd-steinberg')
        )
        composer.layers.append(layer)
        
        return jsonify({'success': True, 'layer_id': layer_id})
    
    except Exception as e:
        return jsonify({'error': f'Error processing image: {str(e)}'}), 500

@app.route('/api/remove-layer', methods=['POST'])
def remove_layer():
    """Remove layer."""
    data = request.json
    composer = get_composition()
    
    success = composer.remove_layer(data.get('layer_id'))
    return jsonify({'success': success})

@app.route('/api/toggle-layer', methods=['POST'])
def toggle_layer():
    """Toggle layer visibility."""
    data = request.json
    composer = get_composition()
    
    success = composer.toggle_layer(data.get('layer_id'))
    return jsonify({'success': success})

@app.route('/api/update-layer-position', methods=['POST'])
def update_layer_position():
    """Update layer position."""
    data = request.json
    composer = get_composition()
    
    layer_id = data.get('layer_id')
    x = int(data.get('x', 0))
    y = int(data.get('y', 0))
    
    success = composer.update_layer(layer_id, x=x, y=y)
    return jsonify({'success': success})

@app.route('/api/update-layer/<layer_id>', methods=['POST'])
def update_layer(layer_id):
    """Update layer properties."""
    data = request.json
    composer = get_composition()
    
    # Convert string values to proper types
    if 'font_size' in data:
        data['font_size'] = int(data['font_size'])
    if 'padding' in data:
        data['padding'] = int(data['padding'])
    if 'width' in data and data['width'] is not None:
        data['width'] = int(data['width'])
    if 'height' in data and data['height'] is not None:
        data['height'] = int(data['height'])
    if 'x' in data:
        data['x'] = int(data['x'])
    if 'y' in data:
        data['y'] = int(data['y'])
    
    success = composer.update_layer(layer_id, **data)
    return jsonify({'success': success})

@app.route('/api/move-layer', methods=['POST'])
def move_layer():
    """Move layer to new position."""
    data = request.json
    composer = get_composition()
    
    layer_id = data.get('layer_id')
    new_index = int(data.get('new_index', 0))
    
    success = composer.move_layer(layer_id, new_index)
    return jsonify({'success': success})

@app.route('/api/add-ip-placeholder', methods=['POST'])
def add_ip_placeholder():
    """Add IP address placeholder layer."""
    try:
        data = request.json
        composer = get_composition()
        
        layer_id = f"ip_placeholder_{len(composer.layers)}"
        
        # Create a special placeholder layer type
        from eink_composer.composer import TextLayer
        layer = TextLayer(
            id=layer_id,
            x=int(data.get('x', 0)),
            y=int(data.get('y', 0)),
            text="$IP_ADDRESS",  # Placeholder text
            color=int(data.get('color', 0)),
            font_size=int(data.get('font_size', 1)),
            background=data.get('background', False),
            rotate=int(data.get('rotation', 0)),
            flip_h=data.get('flip_h', False)
        )
        
        # Add metadata to identify this as a placeholder
        layer.placeholder_type = 'ip'
        composer.layers.append(layer)
        
        return jsonify({'success': True, 'layer_id': layer_id})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/add-qr-placeholder', methods=['POST'])
def add_qr_placeholder():
    """Add QR code placeholder layer."""
    try:
        data = request.json
        composer = get_composition()
        
        layer_id = f"qr_placeholder_{len(composer.layers)}"
        
        # Create placeholder QR code (small black square for preview)
        import numpy as np
        width = int(data.get('width', 70))
        height = int(data.get('height', 70))
        
        # Create a placeholder pattern for preview
        placeholder_img = np.full((height, width), 255, dtype=np.uint8)  # White background
        # Add a simple border and "QR" text pattern
        placeholder_img[0:2, :] = 0  # Top border
        placeholder_img[-2:, :] = 0  # Bottom border 
        placeholder_img[:, 0:2] = 0  # Left border
        placeholder_img[:, -2:] = 0  # Right border
        
        # Add "QR" text in center (simplified)
        center_y, center_x = height // 2, width // 2
        placeholder_img[center_y-5:center_y+5, center_x-10:center_x+10] = 0
        
        from eink_composer.composer import ImageLayer
        layer = ImageLayer(
            id=layer_id,
            x=int(data.get('x', 0)),
            y=int(data.get('y', 0)),
            image_data=placeholder_img,
            width=width,
            height=height
        )
        
        # Add metadata to identify this as a placeholder
        layer.placeholder_type = 'qr'
        layer.error_correction = 'M'
        composer.layers.append(layer)
        
        return jsonify({'success': True, 'layer_id': layer_id})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clear')
def clear_all():
    """Clear all layers."""
    composer = get_composition()
    composer.layers.clear()
    return jsonify({'success': True})

@app.route('/api/display', methods=['POST'])
def display_hardware():
    """Display on e-ink hardware."""
    if not HARDWARE_AVAILABLE:
        return jsonify({'error': 'Hardware SDK not available'}), 400
    
    temp_file = None
    display = None
    
    try:
        composer = get_composition()
        
        # Get the image and transform it for hardware orientation
        img_array = composer.render()  # (128, 250) array for 250x128 design
        
        # Apply flip vertical (always)
        img_array = np.flipud(img_array)  # Flip up-down
        
        # Rotate 90° counterclockwise: (128, 250) -> (250, 128) for hardware
        rotated_array = np.rot90(img_array, k=1)  # k=1 means 90° counterclockwise
        
        # Save rotated image
        temp_file = "/tmp/web_eink_display.png"
        from PIL import Image
        pil_img = Image.fromarray(rotated_array, mode='L')
        pil_img.save(temp_file)
        
        # Verify the PNG was created and is valid
        if not os.path.exists(temp_file):
            return jsonify({'error': 'Failed to create temporary PNG file'}), 500
        
        file_size = os.path.getsize(temp_file)
        if file_size == 0:
            return jsonify({'error': 'Created PNG file is empty'}), 500
        
        # Try to create display object
        try:
            display = Display(auto_init=False)
        except Exception as e:
            return jsonify({'error': f'Failed to create Display object: {str(e)}'}), 500
        
        # Try to initialize display
        try:
            display.initialize()
        except Exception as e:
            return jsonify({
                'error': f'Hardware initialization failed: {str(e)}',
                'details': 'The e-ink display hardware is not responding. This could be because:\n'
                          '• The hardware is not connected\n'
                          '• Drivers are not installed\n'
                          '• Insufficient permissions\n'
                          '• Running in development/simulation environment',
                'file_created': True,
                'file_size': file_size
            }), 500
        
        # Try to display the image
        data = request.json or {}
        mode = DisplayMode.PARTIAL if data.get('partial') else DisplayMode.FULL
        
        try:
            # Convert the rotated PNG to raw data and display
            raw_data = display.convert_png_to_raw(temp_file)
            display._display_raw(raw_data, mode)
            return jsonify({
                'success': True,
                'file_size': file_size,
                'mode': 'PARTIAL' if data.get('partial') else 'FULL'
            })
        except Exception as e:
            return jsonify({
                'error': f'Failed to display PNG image: {str(e)}',
                'details': 'The PNG file was created successfully but could not be displayed on hardware',
                'file_created': True,
                'file_size': file_size
            }), 500
    
    except Exception as e:
        return jsonify({
            'error': f'Unexpected error: {str(e)}',
            'details': 'An unexpected error occurred during the display process'
        }), 500
    
    finally:
        # Clean up resources
        try:
            if display:
                display.close()
        except:
            pass
        
        try:
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
        except:
            pass

@app.route('/api/hardware/clear', methods=['POST'])
def clear_hardware():
    """Clear e-ink hardware display."""
    if not HARDWARE_AVAILABLE:
        return jsonify({'error': 'Hardware SDK not available'}), 400
    
    display = None
    try:
        # Try to create display object
        try:
            display = Display(auto_init=False)
        except Exception as e:
            return jsonify({'error': f'Failed to create Display object: {str(e)}'}), 500
        
        # Try to initialize display
        try:
            display.initialize()
        except Exception as e:
            return jsonify({
                'error': f'Hardware initialization failed: {str(e)}',
                'details': 'Cannot clear display because hardware initialization failed'
            }), 500
        
        # Try to clear the display
        try:
            display.clear()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({
                'error': f'Failed to clear display: {str(e)}',
                'details': 'Hardware is initialized but clear operation failed'
            }), 500
    
    except Exception as e:
        return jsonify({
            'error': f'Unexpected error: {str(e)}',
            'details': 'An unexpected error occurred during the clear process'
        }), 500
    
    finally:
        try:
            if display:
                display.close()
        except:
            pass

@app.route('/api/hardware/info')
def hardware_info():
    """Get hardware information."""
    if not HARDWARE_AVAILABLE:
        return jsonify({
            'available': False,
            'error': 'Hardware SDK not available',
            'details': 'The distiller_cm5_sdk.hardware.eink module could not be imported'
        })
    
    info = {
        'available': True,
        'sdk_imported': True,
        'type': 'E-ink display'
    }
    
    # Try to get more detailed hardware information
    display = None
    try:
        display = Display(auto_init=False)
        info['display_object'] = True
        
        # Try to get dimensions without initializing
        try:
            width, height = display.get_dimensions()
            info['display_size'] = f'{width}x{height}'
            info['width'] = width
            info['height'] = height
        except Exception as e:
            info['display_size'] = 'Unknown'
            info['dimension_error'] = str(e)
        
        # Try to get firmware info
        try:
            firmware = display.get_firmware()
            info['firmware'] = firmware
        except Exception as e:
            info['firmware'] = 'Unknown'
            info['firmware_error'] = str(e)
        
        # Test initialization status
        try:
            display.initialize()
            info['hardware_init'] = True
            info['hardware_status'] = 'Available and working'
        except Exception as e:
            info['hardware_init'] = False
            info['hardware_status'] = 'SDK available but hardware initialization failed'
            info['init_error'] = str(e)
            
    except Exception as e:
        info['display_object'] = False
        info['display_error'] = str(e)
        info['hardware_status'] = 'SDK available but Display object creation failed'
    
    finally:
        try:
            if display:
                display.close()
        except:
            pass
    
    return jsonify(info)

@app.route('/api/save-template', methods=['POST'])
def save_template():
    """Save current composition as template."""
    composer = get_composition()
    
    # Get layer info and add placeholder metadata
    layers = composer.get_layer_info()
    for i, layer in enumerate(layers):
        composer_layer = composer.layers[i]
        if hasattr(composer_layer, 'placeholder_type'):
            layer['placeholder_type'] = composer_layer.placeholder_type
            if hasattr(composer_layer, 'error_correction'):
                layer['error_correction'] = composer_layer.error_correction
    
    template_data = {
        'width': composer.width,
        'height': composer.height,
        'layers': layers,
        'template_version': '1.0',
        'created_for': 'tunnel_service'
    }
    
    # In a real app, save to database or file system
    # For now, return the JSON for download
    return jsonify({
        'success': True,
        'template': template_data
    })

@app.route('/api/load-template', methods=['POST'])
def load_template():
    """Load template from JSON."""
    try:
        data = request.json
        template = data.get('template')
        
        if not template:
            return jsonify({'error': 'No template data'}), 400
        
        # Create new composer
        session_id = session['session_id']
        compositions[session_id] = EinkComposer(250, 128)
        composer = compositions[session_id]
        
        # Restore layers
        for layer_data in template.get('layers', []):
            _restore_layer(composer, layer_data)
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _restore_layer(composer, layer_data):
    """Restore a layer from saved data."""
    layer_type = layer_data['type']
    layer_id = layer_data['id']
    
    if layer_type == 'text':
        composer.add_text_layer(
            layer_id=layer_id,
            text=layer_data.get('text', ''),
            x=layer_data['x'], y=layer_data['y'],
            color=layer_data.get('color', 0),
            font_size=layer_data.get('font_size', 1),
            background=layer_data.get('background', False)
        )
    elif layer_type == 'rectangle':
        composer.add_rectangle_layer(
            layer_id=layer_id,
            x=layer_data['x'], y=layer_data['y'],
            width=layer_data.get('width', 10),
            height=layer_data.get('height', 10),
            filled=layer_data.get('filled', True),
            color=layer_data.get('color', 0)
        )
    # Note: Image layers require file paths, so they're harder to restore
    
    if not layer_data.get('visible', True):
        composer.toggle_layer(layer_id)

@app.route('/api/download-png')
def download_png():
    """Download current composition as PNG."""
    composer = get_composition()
    
    # Save to memory buffer
    img_array = composer.render()
    pil_img = Image.fromarray(img_array, mode='L')
    
    buffer = BytesIO()
    pil_img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return send_file(
        buffer,
        mimetype='image/png',
        as_attachment=True,
        download_name='eink_composition.png'
    )

@app.route('/api/export-template', methods=['POST'])
def export_template():
    """Export current composition as complete template package."""
    try:
        data = request.json
        template_name = data.get('name', 'untitled_template').replace('/', '_').replace('\\', '_')
        
        composer = get_composition()
        
        # Get all layer info at once
        layers_info = composer.get_layer_info()
        image_files = []  # Track image files to copy
        
        # Process each layer info and handle images
        for i, layer_info in enumerate(layers_info):
            layer = composer.layers[i]  # Get corresponding layer object
            
            # Handle background images - convert to relative paths
            if layer_info.get('type') == 'image':
                if hasattr(layer, 'image_path') and layer.image_path:
                    # File-based image with existing path
                    original_path = layer.image_path
                    filename = os.path.basename(original_path)
                    relative_path = f"./{filename}"
                    
                    # Update layer info to use relative path
                    layer_info['image_path'] = relative_path
                    
                    # Track file for copying
                    image_files.append({
                        'original': original_path,
                        'filename': filename,
                        'source_type': 'file'
                    })
                elif hasattr(layer, 'image_data') and layer.image_data is not None:
                    # Memory-based uploaded image (from Mac laptop, etc.)
                    filename = f"{layer.id}.png"  # Generate filename from layer ID
                    relative_path = f"./{filename}"
                    
                    # Update layer info to use relative path
                    layer_info['image_path'] = relative_path
                    
                    # Track image data for saving
                    image_files.append({
                        'filename': filename,
                        'image_data': layer.image_data,
                        'source_type': 'memory'
                    })
        
        # Create template package directory
        template_dir = f"templates/{template_name}"
        os.makedirs(template_dir, exist_ok=True)
        
        # Copy image files to template directory
        for img_file in image_files:
            try:
                dst_path = os.path.join(template_dir, img_file['filename'])
                
                if img_file['source_type'] == 'file':
                    # File-based image - copy from original path
                    import shutil
                    src_path = img_file['original']
                    if os.path.exists(src_path):
                        shutil.copy2(src_path, dst_path)
                    else:
                        print(f"Warning: Source file {src_path} not found")
                        
                elif img_file['source_type'] == 'memory':
                    # Memory-based uploaded image - save from image_data
                    from PIL import Image as PILImage
                    pil_img = PILImage.fromarray(img_file['image_data'], mode='L')
                    pil_img.save(dst_path)
                    
            except Exception as e:
                print(f"Warning: Could not save image file {img_file['filename']}: {e}")
        
        # Create template data
        template_data = {
            'template_version': '1.0',
            'name': template_name,
            'created': time.strftime('%Y-%m-%d %H:%M:%S'),
            'width': composer.width,
            'height': composer.height,
            'layers': layers_info
        }
        
        # Save template.json to package directory  
        template_json_path = os.path.join(template_dir, 'template.json')
        with open(template_json_path, 'w') as f:
            json.dump(template_data, f, indent=2)
        
        return jsonify({
            'success': True,
            'message': f'Template package saved to {template_dir}',
            'path': template_dir,
            'files': len(image_files) + 1  # +1 for template.json
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/import-template', methods=['POST'])
def import_template():
    """Import template package and replace current composition."""
    try:
        template_data = request.json.get('template_data')
        template_path = request.json.get('template_path', '')  # Path to template folder
        
        if not template_data:
            return jsonify({'error': 'No template data provided'}), 400
        
        # Clear current composition
        session_id = session.get('session_id')
        if session_id and session_id in compositions:
            del compositions[session_id]
        
        # Create new composition with template dimensions
        width = template_data.get('width', 250)
        height = template_data.get('height', 128)
        composer = EinkComposer(width, height)
        
        # Get system IP address for dynamic replacement
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
            s.close()
        except:
            ip_address = "192.168.0.147"  # Fallback
        
        # Add layers from template
        for layer_data in template_data.get('layers', []):
            layer_type = layer_data.get('type', '')
            
            # Handle dynamic IP replacement
            if layer_data.get('placeholder_type') == 'ip' and layer_type == 'text':
                layer_data['text'] = ip_address
            
            # Add layer based on type
            if layer_type == 'text':
                composer.add_text_layer(
                    layer_id=layer_data.get('id', f"text_{len(composer.layers)}"),
                    text=layer_data.get('text', ''),
                    x=layer_data.get('x', 0),
                    y=layer_data.get('y', 0),
                    color=layer_data.get('color', 0),
                    font_size=layer_data.get('font_size', 1),
                    background=layer_data.get('background', False),
                    rotate=layer_data.get('rotate', 0),
                    flip_h=layer_data.get('flip_h', False),
                    flip_v=layer_data.get('flip_v', False),
                    padding=layer_data.get('padding', 2)
                )
            elif layer_type == 'rectangle':
                composer.add_rectangle_layer(
                    layer_id=layer_data.get('id', f"rect_{len(composer.layers)}"),
                    x=layer_data.get('x', 0),
                    y=layer_data.get('y', 0),
                    width=layer_data.get('width', 50),
                    height=layer_data.get('height', 50),
                    filled=layer_data.get('filled', True),
                    color=layer_data.get('color', 0)
                )
            elif layer_type == 'image':
                # For QR placeholder, create a simple placeholder (same logic as add_qr_placeholder endpoint)
                if layer_data.get('placeholder_type') == 'qr':
                    import numpy as np
                    from eink_composer.composer import ImageLayer
                    
                    width = int(layer_data.get('width', 70))
                    height = int(layer_data.get('height', 70))
                    
                    # Create placeholder pattern for preview
                    placeholder_img = np.full((height, width), 255, dtype=np.uint8)
                    placeholder_img[0:2, :] = 0  # Top border
                    placeholder_img[-2:, :] = 0  # Bottom border
                    placeholder_img[:, 0:2] = 0  # Left border 
                    placeholder_img[:, -2:] = 0  # Right border
                    
                    # Add "QR" text in center
                    center_y, center_x = height // 2, width // 2
                    if height > 10 and width > 20:
                        placeholder_img[max(0, center_y-5):min(height, center_y+5), 
                                      max(0, center_x-10):min(width, center_x+10)] = 0
                    
                    layer = ImageLayer(
                        id=layer_data.get('id', f"qr_placeholder_{len(composer.layers)}"),
                        x=int(layer_data.get('x', 0)),
                        y=int(layer_data.get('y', 0)),
                        image_data=placeholder_img,
                        width=width,
                        height=height
                    )
                    layer.placeholder_type = 'qr'
                    layer.error_correction = layer_data.get('error_correction', 'M')
                    composer.layers.append(layer)
                elif layer_data.get('image_path'):
                    # Resolve relative image paths
                    image_path = layer_data.get('image_path')
                    if image_path.startswith('./') and template_path:
                        # Convert relative path to absolute path
                        image_path = os.path.join(template_path, image_path[2:])
                    
                    composer.add_image_layer(
                        layer_id=layer_data.get('id', f"img_{len(composer.layers)}"),
                        image_path=image_path,
                        x=layer_data.get('x', 0),
                        y=layer_data.get('y', 0),
                        resize_mode=layer_data.get('resize_mode', 'fit'),
                        dither_mode=layer_data.get('dither_mode', 'floyd-steinberg'),
                        brightness=layer_data.get('brightness', 1.0),
                        contrast=layer_data.get('contrast', 0.0),
                        rotate=layer_data.get('rotate', 0),
                        flip_h=layer_data.get('flip_h', False),
                        flip_v=layer_data.get('flip_v', False),
                        width=layer_data.get('width'),
                        height=layer_data.get('height')
                    )
        
        # Store in session
        if not session.get('session_id'):
            session['session_id'] = str(uuid.uuid4())
        compositions[session['session_id']] = composer
        
        return jsonify({'success': True, 'message': 'Template imported successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/list-templates')
def list_templates():
    """List available template packages."""
    try:
        templates = []
        templates_dir = 'templates'
        
        if os.path.exists(templates_dir):
            for item in os.listdir(templates_dir):
                item_path = os.path.join(templates_dir, item)
                template_json_path = os.path.join(item_path, 'template.json')
                
                if os.path.isdir(item_path) and os.path.exists(template_json_path):
                    try:
                        with open(template_json_path, 'r') as f:
                            template_data = json.load(f)
                        
                        templates.append({
                            'name': item,
                            'display_name': template_data.get('name', item),
                            'created': template_data.get('created', ''),
                            'path': item_path,
                            'layers_count': len(template_data.get('layers', []))
                        })
                    except Exception as e:
                        print(f"Warning: Could not read template {item}: {e}")
        
        return jsonify({'templates': templates})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system-info')
def get_system_info():
    """Get system information including IP address."""
    import socket
    try:
        # Get local IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
    except:
        ip_address = "192.168.1.100"  # Fallback
    
    return jsonify({
        'ip_address': ip_address,
        'hardware_available': HARDWARE_AVAILABLE
    })

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    print("Starting E-ink Web UI...")
    print(f"Hardware available: {HARDWARE_AVAILABLE}")
    print("Access at: http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=True)