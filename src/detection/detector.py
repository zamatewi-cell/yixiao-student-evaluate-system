"""
文字检测与识别模块
- 使用 PaddleOCR 进行文字检测和识别
- 支持单字框定位
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from paddleocr import PaddleOCR


class TextDetector:
    """文字检测与识别器"""
    
    def __init__(self, config: dict):
        self.config = config
        detection_config = config.get('detection', {})
        recognition_config = config.get('recognition', {})
        
        # Initialize PaddleOCR
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang=recognition_config.get('lang', 'ch')
        )
    
    def detect_and_recognize(self, image: np.ndarray) -> List[Dict]:
        """
        Detect and recognize all text in image
        Args:
            image: Input image (BGR format)
        Returns:
            Detection results list
        """
        # Try new API first, then fall back to old API
        try:
            # New PaddleOCR API (v3+)
            result = self.ocr.predict(image)
            return self._parse_new_api_result(result)
        except (TypeError, AttributeError):
            try:
                # Old PaddleOCR API
                result = self.ocr.ocr(image, cls=True)
                return self._parse_old_api_result(result)
            except TypeError:
                # Very old API without cls parameter
                result = self.ocr.ocr(image)
                return self._parse_old_api_result(result)
    
    def _parse_new_api_result(self, result) -> List[Dict]:
        """Parse new PaddleOCR API result"""
        detections = []
        
        if result is None:
            return detections
        
        # New API returns dict with 'rec_texts', 'rec_scores', 'dt_polys', etc.
        if isinstance(result, dict):
            texts = result.get('rec_texts', [[]])
            scores = result.get('rec_scores', [[]])
            polys = result.get('dt_polys', [[]])
            
            # Handle nested list structure
            if texts and isinstance(texts[0], list):
                texts = texts[0]
                scores = scores[0] if scores else []
                polys = polys[0] if polys else []
            
            for i, text in enumerate(texts):
                if not text:
                    continue
                bbox = polys[i] if i < len(polys) else [[0,0],[0,0],[0,0],[0,0]]
                confidence = scores[i] if i < len(scores) else 1.0
                detections.append({
                    'bbox': bbox,
                    'text': text,
                    'confidence': float(confidence)
                })
        
        return detections
    
    def _parse_old_api_result(self, result) -> List[Dict]:
        """Parse old PaddleOCR API result"""
        detections = []
        
        if result and result[0]:
            for line in result[0]:
                bbox = line[0]  # Four corners
                text = line[1][0]  # Recognized text
                confidence = line[1][1]  # Confidence
                
                detections.append({
                    'bbox': bbox,
                    'text': text,
                    'confidence': confidence
                })
        
        return detections
    
    def detect_single_chars(self, image: np.ndarray, filter_printed: bool = True) -> List[Dict]:
        """
        Detect single characters (split by char)
        Args:
            image: Input image
            filter_printed: Whether to filter out printed characters (keep only handwritten)
        Returns:
            Single character detection results
        """
        # Get detection results
        detections = self.detect_and_recognize(image)
        
        single_chars = []
        for det in detections:
            text = det['text']
            bbox = np.array(det['bbox'])
            
            # Split multi-char text
            if len(text) > 1:
                chars = self._split_text_bbox(text, bbox)
                single_chars.extend(chars)
            else:
                single_chars.append({
                    'char': text,
                    'bbox': bbox,
                    'confidence': det['confidence']
                })
        
        # Filter printed characters if enabled
        if filter_printed:
            # First try grid-based filtering
            grid_chars = self._filter_by_grid_position(image, single_chars)
            if grid_chars:
                return grid_chars
            # Fallback to feature-based filtering
            single_chars = self._filter_handwritten_chars(image, single_chars)
        
        return single_chars
    
    def _filter_by_grid_position(self, image: np.ndarray, chars: List[Dict]) -> List[Dict]:
        """
        Filter characters based on grid structure.
        Only keep characters that are:
        1. Inside a detected table/grid area
        2. In the right half of each cell (student's handwriting area)
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        img_height, img_width = gray.shape[:2]
        
        # Detect grid lines
        grid_info = self._detect_grid_structure(gray)
        
        if grid_info is None:
            return []  # No grid detected, fallback to other methods
        
        vertical_lines = grid_info.get('vertical_lines', [])
        horizontal_lines = grid_info.get('horizontal_lines', [])
        
        if len(vertical_lines) < 2 or len(horizontal_lines) < 2:
            return []
        
        # Determine table boundaries (exclude title area)
        # Table typically starts after some top margin and has multiple horizontal lines
        table_top = min(horizontal_lines)
        table_bottom = max(horizontal_lines)
        table_left = min(vertical_lines)
        table_right = max(vertical_lines)
        
        # Filter: table should be in reasonable position (not at very top = title area)
        min_table_top = img_height * 0.15  # Table should start below 15% of image height
        
        if table_top < min_table_top:
            # Adjust table_top to exclude title rows
            for hl in sorted(horizontal_lines):
                if hl > min_table_top:
                    table_top = hl
                    break
        
        # For each character, check if it's in a valid grid cell
        filtered_chars = []
        
        for char_info in chars:
            bbox = np.array(char_info['bbox'])
            char_center_x = np.mean(bbox[:, 0])
            char_center_y = np.mean(bbox[:, 1])
            
            # First check: is the character inside the table area?
            if not (table_left <= char_center_x <= table_right and 
                    table_top <= char_center_y <= table_bottom):
                continue  # Skip characters outside table
            
            # Find which cell this character belongs to
            cell = self._find_cell_for_point(char_center_x, char_center_y, 
                                              vertical_lines, horizontal_lines)
            
            if cell is not None:
                cell_left, cell_right, cell_top, cell_bottom = cell
                cell_width = cell_right - cell_left
                
                # Only keep characters in the right 55% of the cell
                # (student writing area, excluding printed reference)
                right_threshold = cell_left + cell_width * 0.45
                
                if char_center_x > right_threshold:
                    char_info['cell_position'] = 'right'
                    char_info['in_table'] = True
                    filtered_chars.append(char_info)
        
        return filtered_chars
    
    def _detect_grid_structure(self, gray: np.ndarray) -> Optional[Dict]:
        """
        Detect grid structure (horizontal and vertical lines) in the image.
        """
        # Edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Dilate to connect nearby edges
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        # Hough line detection
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, 
                                 minLineLength=100, maxLineGap=10)
        
        if lines is None:
            return None
        
        vertical_lines = []
        horizontal_lines = []
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            
            # Calculate angle
            if x2 - x1 == 0:
                angle = 90
            else:
                angle = abs(np.degrees(np.arctan((y2 - y1) / (x2 - x1))))
            
            # Classify as vertical or horizontal
            if angle > 80:  # Nearly vertical
                vertical_lines.append(int((x1 + x2) / 2))
            elif angle < 10:  # Nearly horizontal
                horizontal_lines.append(int((y1 + y2) / 2))
        
        # Remove duplicate lines (cluster nearby lines)
        vertical_lines = self._cluster_lines(sorted(set(vertical_lines)), threshold=20)
        horizontal_lines = self._cluster_lines(sorted(set(horizontal_lines)), threshold=20)
        
        if len(vertical_lines) < 2 or len(horizontal_lines) < 2:
            return None
        
        return {
            'vertical_lines': sorted(vertical_lines),
            'horizontal_lines': sorted(horizontal_lines)
        }
    
    def _cluster_lines(self, lines: List[int], threshold: int = 20) -> List[int]:
        """Cluster nearby lines into single lines"""
        if not lines:
            return []
        
        clustered = [lines[0]]
        for line in lines[1:]:
            if line - clustered[-1] > threshold:
                clustered.append(line)
            else:
                # Merge with previous (take average)
                clustered[-1] = (clustered[-1] + line) // 2
        
        return clustered
    
    def _find_cell_for_point(self, x: float, y: float, 
                              vertical_lines: List[int], 
                              horizontal_lines: List[int]) -> Optional[Tuple[int, int, int, int]]:
        """
        Find which cell a point belongs to.
        Returns (left, right, top, bottom) of the cell, or None if not in any cell.
        """
        # Find horizontal boundaries
        cell_left = None
        cell_right = None
        for i, vl in enumerate(vertical_lines):
            if vl <= x:
                cell_left = vl
            if vl >= x and cell_right is None:
                cell_right = vl
                break
        
        # Find vertical boundaries
        cell_top = None
        cell_bottom = None
        for i, hl in enumerate(horizontal_lines):
            if hl <= y:
                cell_top = hl
            if hl >= y and cell_bottom is None:
                cell_bottom = hl
                break
        
        if all(v is not None for v in [cell_left, cell_right, cell_top, cell_bottom]):
            return (cell_left, cell_right, cell_top, cell_bottom)
        
        return None
    
    def _filter_handwritten_chars(self, image: np.ndarray, chars: List[Dict]) -> List[Dict]:
        """
        Filter to keep only handwritten characters, exclude printed ones.
        Uses multiple criteria:
        1. Ink darkness (handwritten is darker)
        2. Stroke width variation (handwritten has more variation)
        3. Edge sharpness (printed has sharper edges)
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        handwritten_chars = []
        
        for char_info in chars:
            bbox = np.array(char_info['bbox'])
            char_img = self.crop_char(gray, bbox)
            
            if char_img.size == 0:
                continue
            
            # Check if this is likely handwritten
            is_handwritten, confidence = self._is_handwritten(char_img)
            
            if is_handwritten:
                char_info['handwritten_confidence'] = confidence
                handwritten_chars.append(char_info)
        
        return handwritten_chars
    
    def _is_handwritten(self, char_img: np.ndarray) -> Tuple[bool, float]:
        """
        Determine if a character image is handwritten or printed.
        Returns (is_handwritten, confidence)
        
        Criteria:
        1. Ink darkness: handwritten chars typically have darker pixels (lower gray values)
        2. Stroke width variation: handwritten chars have more variation in stroke width
        3. Ink density: handwritten chars often have denser ink
        """
        if char_img.size == 0:
            return False, 0.0
        
        # Normalize size
        if char_img.shape[0] < 10 or char_img.shape[1] < 10:
            return False, 0.0
        
        # Binary threshold
        _, binary = cv2.threshold(char_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Feature 1: Average darkness of ink pixels
        # Handwritten chars have darker ink (lower gray value where there's ink)
        ink_pixels = char_img[binary > 0]
        if len(ink_pixels) == 0:
            return False, 0.0
        
        avg_darkness = np.mean(ink_pixels)
        darkness_score = 1.0 if avg_darkness < 100 else (200 - avg_darkness) / 100.0
        darkness_score = max(0, min(1, darkness_score))
        
        # Feature 2: Ink density (ratio of ink pixels)
        ink_ratio = np.sum(binary > 0) / binary.size
        density_score = min(1.0, ink_ratio * 5)  # Normalize to 0-1
        
        # Feature 3: Stroke width variation (using distance transform)
        dist_transform = cv2.distanceTransform(binary, cv2.DIST_L2, 5)
        if np.max(dist_transform) > 0:
            stroke_widths = dist_transform[dist_transform > 0]
            if len(stroke_widths) > 10:
                stroke_std = np.std(stroke_widths)
                stroke_mean = np.mean(stroke_widths)
                # Handwritten has more variation
                variation_score = min(1.0, stroke_std / (stroke_mean + 1e-6))
            else:
                variation_score = 0.5
        else:
            variation_score = 0.5
        
        # Feature 4: Edge irregularity (handwritten has less uniform edges)
        edges = cv2.Canny(char_img, 50, 150)
        edge_pixels = np.sum(edges > 0)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        irregularity_score = 0.5
        if contours:
            total_perimeter = sum(cv2.arcLength(c, True) for c in contours)
            if total_perimeter > 0:
                # Higher ratio = more irregular = more likely handwritten
                irregularity_score = min(1.0, edge_pixels / total_perimeter / 2)
        
        # Combined score (weighted average)
        weights = {
            'darkness': 0.35,
            'density': 0.25,
            'variation': 0.25,
            'irregularity': 0.15
        }
        
        combined_score = (
            weights['darkness'] * darkness_score +
            weights['density'] * density_score +
            weights['variation'] * variation_score +
            weights['irregularity'] * irregularity_score
        )
        
        # Threshold to determine handwritten vs printed
        # Printed chars typically score lower (lighter, more uniform)
        threshold = 0.45
        is_handwritten = combined_score > threshold
        
        return is_handwritten, combined_score
    
    def _split_text_bbox(self, text: str, bbox: np.ndarray) -> List[Dict]:
        """
        将多字文本框等分为单字框
        Args:
            text: 文本内容
            bbox: 文本框四角坐标
        Returns:
            单字框列表
        """
        n = len(text)
        if n <= 1:
            return [{'char': text, 'bbox': bbox, 'confidence': 1.0}]
        
        # 计算每个字的宽度
        top_left, top_right = bbox[0], bbox[1]
        bottom_right, bottom_left = bbox[2], bbox[3]
        
        chars = []
        for i, char in enumerate(text):
            # 线性插值计算每个字的边界
            ratio_start = i / n
            ratio_end = (i + 1) / n
            
            tl = top_left + (top_right - top_left) * ratio_start
            tr = top_left + (top_right - top_left) * ratio_end
            br = bottom_left + (bottom_right - bottom_left) * ratio_end
            bl = bottom_left + (bottom_right - bottom_left) * ratio_start
            
            char_bbox = np.array([tl, tr, br, bl])
            chars.append({
                'char': char,
                'bbox': char_bbox,
                'confidence': 1.0
            })
        
        return chars
    
    def crop_char(self, image: np.ndarray, bbox: np.ndarray) -> np.ndarray:
        """
        从图像中裁剪单字区域
        Args:
            image: 原图像
            bbox: 边界框坐标
        Returns:
            裁剪后的单字图像
        """
        # 转换为整数坐标
        bbox = bbox.astype(np.int32)
        
        # 获取最小外接矩形
        x_min = max(0, bbox[:, 0].min())
        x_max = min(image.shape[1], bbox[:, 0].max())
        y_min = max(0, bbox[:, 1].min())
        y_max = min(image.shape[0], bbox[:, 1].max())
        
        return image[y_min:y_max, x_min:x_max]
