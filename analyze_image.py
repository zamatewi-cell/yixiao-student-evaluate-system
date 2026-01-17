# -*- coding: utf-8 -*-
"""
Analyze image to understand printed vs handwritten distinction
"""
import sys
sys.path.insert(0, '.')

import cv2
import numpy as np
from pathlib import Path

def analyze_char_features(image_path):
    """Analyze character features in the image"""
    # Read image with Chinese path support
    img = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        print("Cannot read image")
        return
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    print("Image shape:", img.shape)
    print("Gray value range:", gray.min(), "-", gray.max())
    
    # Use PaddleOCR to detect
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(use_angle_cls=True, lang='ch')
    result = ocr.ocr(img, cls=True)
    
    if not result or not result[0]:
        print("No text detected")
        return
    
    print("\nAnalyzing {} detected text regions:".format(len(result[0])))
    print("-" * 80)
    
    features_list = []
    
    for i, line in enumerate(result[0][:20]):  # First 20
        bbox = np.array(line[0]).astype(np.int32)
        text = line[1][0]
        
        # Crop region
        x_min = max(0, bbox[:, 0].min())
        x_max = min(gray.shape[1], bbox[:, 0].max())
        y_min = max(0, bbox[:, 1].min())
        y_max = min(gray.shape[0], bbox[:, 1].max())
        
        char_img = gray[y_min:y_max, x_min:x_max]
        
        if char_img.size == 0:
            continue
        
        # Binary
        _, binary = cv2.threshold(char_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Features
        ink_pixels = char_img[binary > 0]
        if len(ink_pixels) == 0:
            continue
        
        avg_darkness = np.mean(ink_pixels)
        min_darkness = np.min(ink_pixels)
        ink_ratio = np.sum(binary > 0) / binary.size
        
        # Stroke width variation
        dist = cv2.distanceTransform(binary, cv2.DIST_L2, 5)
        stroke_widths = dist[dist > 0]
        if len(stroke_widths) > 5:
            stroke_std = np.std(stroke_widths)
            stroke_mean = np.mean(stroke_widths)
            variation = stroke_std / (stroke_mean + 1e-6)
        else:
            variation = 0
        
        features = {
            'text': text,
            'avg_darkness': avg_darkness,
            'min_darkness': min_darkness,
            'ink_ratio': ink_ratio,
            'stroke_variation': variation
        }
        features_list.append(features)
        
        print("{:2d}. '{}' | Darkness: {:.0f} (min:{:.0f}) | InkRatio: {:.3f} | StrokeVar: {:.3f}".format(
            i+1, text[:10], avg_darkness, min_darkness, ink_ratio, variation
        ))
    
    # Analyze distribution
    print("\n" + "=" * 80)
    print("FEATURE DISTRIBUTION ANALYSIS")
    print("=" * 80)
    
    darknesses = [f['avg_darkness'] for f in features_list]
    ink_ratios = [f['ink_ratio'] for f in features_list]
    variations = [f['stroke_variation'] for f in features_list]
    
    print("\nDarkness: min={:.1f}, max={:.1f}, mean={:.1f}, std={:.1f}".format(
        min(darknesses), max(darknesses), np.mean(darknesses), np.std(darknesses)
    ))
    print("InkRatio: min={:.3f}, max={:.3f}, mean={:.3f}, std={:.3f}".format(
        min(ink_ratios), max(ink_ratios), np.mean(ink_ratios), np.std(ink_ratios)
    ))
    print("StrokeVar: min={:.3f}, max={:.3f}, mean={:.3f}, std={:.3f}".format(
        min(variations), max(variations), np.mean(variations), np.std(variations)
    ))
    
    # Try to find a good threshold
    print("\n" + "=" * 80)
    print("POTENTIAL THRESHOLDS")
    print("=" * 80)
    
    # Sort by darkness
    sorted_by_darkness = sorted(features_list, key=lambda x: x['avg_darkness'])
    print("\nTop 5 DARKEST (likely handwritten):")
    for f in sorted_by_darkness[:5]:
        print("  '{}': darkness={:.0f}".format(f['text'][:10], f['avg_darkness']))
    
    print("\nTop 5 LIGHTEST (likely printed):")
    for f in sorted_by_darkness[-5:]:
        print("  '{}': darkness={:.0f}".format(f['text'][:10], f['avg_darkness']))

if __name__ == "__main__":
    image_path = "data/student_samples/raw/学生作品_001.jpg"
    analyze_char_features(image_path)
