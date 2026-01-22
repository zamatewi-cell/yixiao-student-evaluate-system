"""
Font Renderer Tool
- Generate standard character template images from TTF font files
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont


class FontRenderer:
    """Font Renderer - Generate standard character images from TTF font"""
    
    def __init__(self, font_path: str, font_size: int = 200):
        """
        Initialize font renderer
        Args:
            font_path: TTF font file path
            font_size: Font size in pixels
        """
        self.font_path = Path(font_path)
        self.font_size = font_size
        
        if not self.font_path.exists():
            raise FileNotFoundError(f"Font file not found: {font_path}")
        
        # Load font
        self.font = ImageFont.truetype(str(self.font_path), self.font_size)
        
        # Cache rendered characters
        self._cache = {}
    
    def render_char(self, char: str, target_size: Tuple[int, int] = (256, 256),
                    padding: int = 20) -> np.ndarray:
        """
        Render a single character to image
        Args:
            char: Character to render
            target_size: Target image size (width, height)
            padding: Inner padding
        Returns:
            Binary image (numpy array, black background with white strokes)
        """
        # Check cache
        cache_key = (char, target_size, padding)
        if cache_key in self._cache:
            return self._cache[cache_key].copy()
        
        # Create temporary large canvas
        canvas_size = (self.font_size * 2, self.font_size * 2)
        image = Image.new('L', canvas_size, color=255)  # White background
        draw = ImageDraw.Draw(image)
        
        # Get character bounding box
        bbox = draw.textbbox((0, 0), char, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center the text
        x = (canvas_size[0] - text_width) // 2 - bbox[0]
        y = (canvas_size[1] - text_height) // 2 - bbox[1]
        
        draw.text((x, y), char, font=self.font, fill=0)  # Black text
        
        # Convert to numpy array
        img_array = np.array(image)
        
        # Crop to content area
        coords = np.column_stack(np.where(img_array < 255))
        if len(coords) > 0:
            y_min, x_min = coords.min(axis=0)
            y_max, x_max = coords.max(axis=0)
            
            # Add padding
            y_min = max(0, y_min - padding)
            x_min = max(0, x_min - padding)
            y_max = min(canvas_size[1], y_max + padding)
            x_max = min(canvas_size[0], x_max + padding)
            
            img_array = img_array[y_min:y_max, x_min:x_max]
        
        # Resize to target size
        img_array = cv2.resize(img_array, target_size, interpolation=cv2.INTER_AREA)
        
        # Binarize and invert (black background, white strokes)
        _, binary = cv2.threshold(img_array, 127, 255, cv2.THRESH_BINARY_INV)
        
        # Cache result
        self._cache[cache_key] = binary.copy()
        
        return binary
    
    def render_chars_batch(self, chars: str, target_size: Tuple[int, int] = (256, 256),
                           output_dir: Optional[str] = None) -> dict:
        """
        Render multiple characters in batch
        Args:
            chars: Characters to render
            target_size: Target image size
            output_dir: Optional output directory to save images
        Returns:
            Dictionary {char: image_array}
        """
        results = {}
        
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        
        for char in chars:
            if char.strip():  # Skip whitespace
                img = self.render_char(char, target_size)
                results[char] = img
                
                if output_dir:
                    # Save as PNG file
                    save_path = output_path / f"{char}.png"
                    cv2.imwrite(str(save_path), img)
        
        return results
    
    def has_char(self, char: str) -> bool:
        """
        Check if font contains the specified character
        Args:
            char: Character to check
        Returns:
            Whether the character is available
        """
        try:
            # Try to render, if font doesn't contain the char, it will show as box
            img = self.render_char(char, target_size=(64, 64))
            # Check if there's actual content (not blank)
            return np.sum(img > 0) > 100
        except:
            return False


class TemplateManager:
    """Standard character template manager"""
    
    def __init__(self, config: dict):
        self.config = config
        templates_path = config.get('paths', {}).get('templates', 'data/templates')
        self.templates_dir = Path(templates_path)
        
        # Find font file
        self.font_path = None
        self.renderer = None
        
        for font_file in self.templates_dir.glob('*.ttf'):
            self.font_path = font_file
            break
        
        if self.font_path:
            self.renderer = FontRenderer(str(self.font_path))
            print(f"Font loaded: {self.font_path.name}")
        else:
            print("Warning: No TTF font file found")
        
        # Template cache
        self._cache = {}
    
    def get_template(self, char: str, target_size: Tuple[int, int] = (256, 256)) -> Optional[np.ndarray]:
        """
        Get standard template for specified character
        Args:
            char: Character
            target_size: Target size
        Returns:
            Template image (binary, black background with white strokes)
        """
        cache_key = (char, target_size)
        if cache_key in self._cache:
            return self._cache[cache_key].copy()
        
        # First check for pre-rendered PNG file
        png_path = self.templates_dir / f"{char}.png"
        if png_path.exists():
            img = cv2.imread(str(png_path), cv2.IMREAD_GRAYSCALE)
            if img is not None:
                img = cv2.resize(img, target_size, interpolation=cv2.INTER_AREA)
                self._cache[cache_key] = img.copy()
                return img
        
        # Use font rendering
        if self.renderer:
            img = self.renderer.render_char(char, target_size)
            self._cache[cache_key] = img.copy()
            return img
        
        return None
