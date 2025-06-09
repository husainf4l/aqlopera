"""
Computer Vision tools for web element detection and analysis
"""
import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from PIL import Image, ImageDraw, ImageFont
import base64
from io import BytesIO

from core.logging import app_logger


class VisionTool:
    """Computer vision utilities for web automation"""
    
    def __init__(self):
        self.confidence_threshold = 0.8
        
    def find_text_in_image(self, image_path: str, target_text: str) -> Optional[Tuple[int, int]]:
        """Find text in an image using OCR (simplified version)"""
        try:
            # This is a simplified implementation
            # In production, you'd use pytesseract or similar OCR library
            app_logger.info(f"Searching for text '{target_text}' in {image_path}")
            
            # For now, return None as we'd need OCR library
            # TODO: Implement with pytesseract
            return None
            
        except Exception as e:
            app_logger.error(f"Text search failed: {e}")
            return None
    
    def find_similar_elements(self, image_path: str, template_path: str) -> List[Tuple[int, int]]:
        """Find similar visual elements using template matching"""
        try:
            # Load images
            image = cv2.imread(image_path)
            template = cv2.imread(template_path)
            
            if image is None or template is None:
                return []
            
            # Convert to grayscale
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            
            # Template matching
            result = cv2.matchTemplate(gray_image, gray_template, cv2.TM_CCOEFF_NORMED)
            
            # Find locations where matching exceeds threshold
            locations = np.where(result >= self.confidence_threshold)
            matches = []
            
            for pt in zip(*locations[::-1]):
                matches.append((pt[0], pt[1]))
            
            app_logger.info(f"Found {len(matches)} similar elements")
            return matches
            
        except Exception as e:
            app_logger.error(f"Element matching failed: {e}")
            return []
    
    def detect_buttons(self, image_path: str) -> List[Dict[str, Any]]:
        """Detect button-like elements in an image"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return []
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            buttons = []
            for contour in contours:
                # Filter by area and aspect ratio to find button-like shapes
                area = cv2.contourArea(contour)
                if area > 500:  # Minimum area for buttons
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    # Button-like aspect ratio
                    if 0.5 <= aspect_ratio <= 4.0:
                        buttons.append({
                            'x': int(x),
                            'y': int(y),
                            'width': int(w),
                            'height': int(h),
                            'center': (int(x + w/2), int(y + h/2)),
                            'area': area
                        })
            
            app_logger.info(f"Detected {len(buttons)} button-like elements")
            return buttons
            
        except Exception as e:
            app_logger.error(f"Button detection failed: {e}")
            return []
    
    def highlight_element(self, image_path: str, coordinates: Tuple[int, int], 
                         size: Tuple[int, int], output_path: str) -> bool:
        """Highlight an element in an image"""
        try:
            # Open image with PIL
            image = Image.open(image_path)
            draw = ImageDraw.Draw(image)
            
            # Draw rectangle around element
            x, y = coordinates
            w, h = size
            
            # Draw red rectangle
            draw.rectangle([x, y, x + w, y + h], outline="red", width=3)
            
            # Save highlighted image
            image.save(output_path)
            app_logger.info(f"Element highlighted and saved to {output_path}")
            return True
            
        except Exception as e:
            app_logger.error(f"Element highlighting failed: {e}")
            return False
    
    def create_annotated_screenshot(self, image_path: str, elements: List[Dict], 
                                  output_path: str) -> bool:
        """Create an annotated screenshot with numbered elements"""
        try:
            image = Image.open(image_path)
            draw = ImageDraw.Draw(image)
            
            # Try to load a font (fallback to default if not available)
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()
            
            for i, element in enumerate(elements, 1):
                x = element.get('x', 0)
                y = element.get('y', 0)
                w = element.get('width', 50)
                h = element.get('height', 20)
                
                # Draw rectangle
                draw.rectangle([x, y, x + w, y + h], outline="red", width=2)
                
                # Draw number
                draw.text((x, y - 20), str(i), fill="red", font=font)
            
            image.save(output_path)
            app_logger.info(f"Annotated screenshot saved to {output_path}")
            return True
            
        except Exception as e:
            app_logger.error(f"Screenshot annotation failed: {e}")
            return False
    
    def image_to_base64(self, image_path: str) -> Optional[str]:
        """Convert image to base64 string"""
        try:
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
                return encoded_string
        except Exception as e:
            app_logger.error(f"Image to base64 conversion failed: {e}")
            return None


# Global vision tool instance
vision_tool = VisionTool()
