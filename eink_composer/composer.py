import numpy as np
from PIL import Image
from typing import List, Dict, Optional, Literal, Any, Union
from dataclasses import dataclass, field
import uuid

from .dithering import floyd_steinberg_dither, threshold_dither, pack_bits
from .image_ops import resize_image, flip_horizontal, rotate_ccw_90, invert_colors
from .text import render_text, measure_text


@dataclass
class Layer:
    """Base layer class."""
    id: str
    type: str
    visible: bool = True
    x: int = 0
    y: int = 0


@dataclass
class ImageLayer(Layer):
    """Image layer with processing options."""
    type: str = field(default="image", init=False)
    image_path: Optional[str] = None
    image_data: Optional[np.ndarray] = None
    resize_mode: Literal['stretch', 'fit', 'crop'] = 'fit'
    dither_mode: Literal['floyd-steinberg', 'threshold', 'none'] = 'floyd-steinberg'
    brightness: float = 1.0
    contrast: float = 0.0
    rotate: int = 0  # Rotation in degrees (0, 90, 180, 270)
    flip_h: bool = False  # Horizontal flip
    flip_v: bool = False  # Vertical flip
    crop_x: Optional[int] = None  # X position for crop (None = center)
    crop_y: Optional[int] = None  # Y position for crop (None = center)


@dataclass
class TextLayer(Layer):
    """Text layer."""
    type: str = field(default="text", init=False)
    text: str = ""
    color: int = 0  # 0=black, 255=white


@dataclass
class RectangleLayer(Layer):
    """Rectangle layer."""
    type: str = field(default="rectangle", init=False)
    width: int = 10
    height: int = 10
    filled: bool = True
    color: int = 0


class EinkComposer:
    """
    E-ink display composer for creating layered templates.
    """
    
    def __init__(self, width: int = 250, height: int = 128):
        """
        Initialize composer with display dimensions.
        
        Args:
            width: Display width in pixels
            height: Display height in pixels
        """
        self.width = width
        self.height = height
        self.layers: List[Layer] = []
        self.canvas = np.full((height, width), 255, dtype=np.uint8)  # White background
        
    def add_image_layer(self, layer_id: str, image_path: str, 
                       x: int = 0, y: int = 0,
                       resize_mode: Literal['stretch', 'fit', 'crop'] = 'fit',
                       dither_mode: Literal['floyd-steinberg', 'threshold', 'none'] = 'floyd-steinberg',
                       brightness: float = 1.0, contrast: float = 0.0,
                       rotate: int = 0, flip_h: bool = False, flip_v: bool = False,
                       crop_x: Optional[int] = None, crop_y: Optional[int] = None) -> str:
        """
        Add an image layer.
        
        Args:
            layer_id: Unique layer identifier
            image_path: Path to image file
            x, y: Position on canvas
            resize_mode: How to resize image
            dither_mode: Dithering algorithm to use
            brightness: Brightness adjustment
            contrast: Contrast adjustment
            rotate: Rotation in degrees (0, 90, 180, 270)
            flip_h: Horizontal flip
            flip_v: Vertical flip
            crop_x: X position for crop when resize_mode='crop' (None = center)
            crop_y: Y position for crop when resize_mode='crop' (None = center)
            
        Returns:
            Layer ID
        """
        layer = ImageLayer(
            id=layer_id,
            x=x, y=y,
            image_path=image_path,
            resize_mode=resize_mode,
            dither_mode=dither_mode,
            brightness=brightness,
            contrast=contrast,
            rotate=rotate,
            flip_h=flip_h,
            flip_v=flip_v,
            crop_x=crop_x,
            crop_y=crop_y
        )
        self.layers.append(layer)
        return layer_id
    
    def add_text_layer(self, layer_id: str, text: str, 
                      x: int = 0, y: int = 0, color: int = 0) -> str:
        """
        Add a text layer.
        
        Args:
            layer_id: Unique layer identifier
            text: Text to render
            x, y: Position on canvas
            color: Text color (0=black, 255=white)
            
        Returns:
            Layer ID
        """
        layer = TextLayer(id=layer_id, text=text, x=x, y=y, color=color)
        self.layers.append(layer)
        return layer_id
    
    def add_rectangle_layer(self, layer_id: str, 
                           x: int = 0, y: int = 0,
                           width: int = 10, height: int = 10,
                           filled: bool = True, color: int = 0) -> str:
        """
        Add a rectangle layer.
        
        Args:
            layer_id: Unique layer identifier
            x, y: Top-left position
            width, height: Rectangle dimensions
            filled: Whether to fill the rectangle
            color: Rectangle color (0=black, 255=white)
            
        Returns:
            Layer ID
        """
        layer = RectangleLayer(
            id=layer_id, x=x, y=y,
            width=width, height=height,
            filled=filled, color=color
        )
        self.layers.append(layer)
        return layer_id
    
    def remove_layer(self, layer_id: str) -> bool:
        """Remove a layer by ID."""
        self.layers = [l for l in self.layers if l.id != layer_id]
        return True
    
    def update_layer(self, layer_id: str, **kwargs) -> bool:
        """Update layer properties."""
        for layer in self.layers:
            if layer.id == layer_id:
                for key, value in kwargs.items():
                    if hasattr(layer, key):
                        setattr(layer, key, value)
                return True
        return False
    
    def toggle_layer(self, layer_id: str) -> bool:
        """Toggle layer visibility."""
        for layer in self.layers:
            if layer.id == layer_id:
                layer.visible = not layer.visible
                return True
        return False
    
    def _render_image_layer(self, layer: ImageLayer):
        """Render an image layer to canvas."""
        if not layer.visible:
            return
            
        # Load image
        if layer.image_data is not None:
            img = layer.image_data
        elif layer.image_path:
            pil_img = Image.open(layer.image_path).convert('L')
            img = np.array(pil_img)
        else:
            return
        
        # Apply transformations first (before resizing)
        if layer.flip_h:
            img = flip_horizontal(img)
        if layer.flip_v:
            from .image_ops import flip_vertical
            img = flip_vertical(img)
        
        # Apply rotation
        if layer.rotate != 0:
            # Normalize rotation to 0, 90, 180, 270
            rotations = (layer.rotate % 360) // 90
            for _ in range(rotations):
                img = rotate_ccw_90(img)
        
        # Calculate target size based on position and canvas size
        # After rotation, dimensions might have changed
        target_width = self.width - layer.x
        target_height = self.height - layer.y
        
        # Resize after transformations
        if img.shape != (target_height, target_width):
            img = resize_image(img, target_width, target_height, 
                             mode=layer.resize_mode, 
                             crop_x=layer.crop_x, 
                             crop_y=layer.crop_y)
        
        # Apply brightness/contrast
        if layer.brightness != 1.0 or layer.contrast != 0:
            from .image_ops import adjust_brightness_contrast
            img = adjust_brightness_contrast(img, layer.brightness, layer.contrast)
        
        # Apply dithering
        if layer.dither_mode == 'floyd-steinberg':
            img = floyd_steinberg_dither(img)
        elif layer.dither_mode == 'threshold':
            img = threshold_dither(img)
        
        # Composite onto canvas
        h, w = img.shape
        y_end = min(layer.y + h, self.height)
        x_end = min(layer.x + w, self.width)
        
        if layer.y < self.height and layer.x < self.width:
            self.canvas[layer.y:y_end, layer.x:x_end] = img[:y_end-layer.y, :x_end-layer.x]
    
    def _render_text_layer(self, layer: TextLayer):
        """Render a text layer to canvas."""
        if not layer.visible or not layer.text:
            return
            
        render_text(layer.text, layer.x, layer.y, self.canvas, layer.color)
    
    def _render_rectangle_layer(self, layer: RectangleLayer):
        """Render a rectangle layer to canvas."""
        if not layer.visible:
            return
            
        x1 = max(0, layer.x)
        y1 = max(0, layer.y)
        x2 = min(self.width, layer.x + layer.width)
        y2 = min(self.height, layer.y + layer.height)
        
        if x1 >= x2 or y1 >= y2:
            return
            
        if layer.filled:
            self.canvas[y1:y2, x1:x2] = layer.color
        else:
            # Draw outline
            self.canvas[y1, x1:x2] = layer.color  # Top
            self.canvas[y2-1, x1:x2] = layer.color  # Bottom
            self.canvas[y1:y2, x1] = layer.color  # Left
            self.canvas[y1:y2, x2-1] = layer.color  # Right
    
    def render(self, background_color: int = 255, 
               final_dither: Optional[Literal['floyd-steinberg', 'threshold']] = None,
               transformations: Optional[List[Literal['flip-h', 'flip-v', 'rotate-90', 'invert']]] = None) -> np.ndarray:
        """
        Render all layers to create final image.
        
        Args:
            background_color: Background color (0=black, 255=white)
            final_dither: Optional final dithering pass
            transformations: List of transformations to apply
            
        Returns:
            Rendered grayscale image
        """
        # Clear canvas
        self.canvas.fill(background_color)
        
        # Render each layer
        for layer in self.layers:
            if isinstance(layer, ImageLayer):
                self._render_image_layer(layer)
            elif isinstance(layer, TextLayer):
                self._render_text_layer(layer)
            elif isinstance(layer, RectangleLayer):
                self._render_rectangle_layer(layer)
        
        result = self.canvas.copy()
        
        # Apply final dithering if requested
        if final_dither == 'floyd-steinberg':
            result = floyd_steinberg_dither(result)
        elif final_dither == 'threshold':
            result = threshold_dither(result)
        
        # Apply transformations
        if transformations:
            for transform in transformations:
                if transform == 'flip-h':
                    result = flip_horizontal(result)
                elif transform == 'flip-v':
                    from .image_ops import flip_vertical
                    result = flip_vertical(result)
                elif transform == 'rotate-90':
                    result = rotate_ccw_90(result)
                elif transform == 'invert':
                    result = invert_colors(result)
        
        return result
    
    def render_binary(self, **kwargs) -> bytes:
        """
        Render and return as packed binary data.
        
        Returns:
            Packed binary data (8 pixels per byte)
        """
        img = self.render(**kwargs)
        return pack_bits(img)
    
    def save(self, filename: str, format: Literal['png', 'binary', 'bmp'] = 'png', **render_kwargs):
        """
        Save rendered image to file.
        
        Args:
            filename: Output filename
            format: Output format
            **render_kwargs: Arguments passed to render()
        """
        if format == 'binary':
            data = self.render_binary(**render_kwargs)
            with open(filename, 'wb') as f:
                f.write(data)
        else:
            img = self.render(**render_kwargs)
            pil_img = Image.fromarray(img, mode='L')
            
            if format == 'bmp':
                # Convert to 1-bit for true monochrome BMP
                pil_img = pil_img.point(lambda x: 255 if x > 128 else 0, mode='1')
            
            pil_img.save(filename)
    
    def get_layer_info(self) -> List[Dict[str, Any]]:
        """Get information about all layers."""
        info = []
        for layer in self.layers:
            layer_info = {
                'id': layer.id,
                'type': layer.type,
                'visible': layer.visible,
                'x': layer.x,
                'y': layer.y
            }
            
            if isinstance(layer, ImageLayer):
                layer_info.update({
                    'image_path': layer.image_path,
                    'resize_mode': layer.resize_mode,
                    'dither_mode': layer.dither_mode
                })
            elif isinstance(layer, TextLayer):
                layer_info.update({
                    'text': layer.text,
                    'color': layer.color
                })
            elif isinstance(layer, RectangleLayer):
                layer_info.update({
                    'width': layer.width,
                    'height': layer.height,
                    'filled': layer.filled,
                    'color': layer.color
                })
            
            info.append(layer_info)
        
        return info