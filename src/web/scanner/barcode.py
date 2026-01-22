# -*- coding: utf-8 -*-
"""
条码识别模块
"""
import os
from pathlib import Path
from typing import Optional, Tuple
import numpy as np
import cv2

try:
    from pyzbar.pyzbar import decode
    from PIL import Image
    PYZBAR_AVAILABLE = True
except ImportError:
    PYZBAR_AVAILABLE = False
    print("Warning: pyzbar not installed. Barcode recognition disabled.")


def read_barcode_from_image(image_path: str) -> Optional[str]:
    """
    从图片中读取条码
    
    Args:
        image_path: 图片路径
        
    Returns:
        条码内容，如果未找到返回None
    """
    if not PYZBAR_AVAILABLE:
        return None
    
    try:
        # 尝试多种方式读取图片
        img = None
        
        # 方式1: PIL直接读取
        try:
            img = Image.open(image_path)
        except:
            pass
        
        # 方式2: OpenCV读取（支持中文路径）
        if img is None:
            try:
                cv_img = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
                if cv_img is not None:
                    img = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
            except:
                pass
        
        if img is None:
            return None
        
        # 解码条码
        barcodes = decode(img)
        
        for barcode in barcodes:
            # 返回第一个识别到的条码
            data = barcode.data.decode('utf-8')
            return data
        
        # 如果没有识别到，尝试预处理后再识别
        return _read_barcode_with_preprocessing(img)
        
    except Exception as e:
        print(f"Barcode read error: {e}")
        return None


def _read_barcode_with_preprocessing(img: Image.Image) -> Optional[str]:
    """
    对图片进行预处理后再尝试识别条码
    """
    if not PYZBAR_AVAILABLE:
        return None
    
    try:
        # 转换为灰度
        gray = img.convert('L')
        
        # 尝试不同的处理方式
        for threshold in [127, 100, 150, 80]:
            # 二值化
            binary = gray.point(lambda x: 255 if x > threshold else 0)
            barcodes = decode(binary)
            if barcodes:
                return barcodes[0].data.decode('utf-8')
        
        # 尝试放大
        width, height = img.size
        if width < 1000:
            enlarged = img.resize((width * 2, height * 2), Image.Resampling.LANCZOS)
            barcodes = decode(enlarged)
            if barcodes:
                return barcodes[0].data.decode('utf-8')
        
        return None
    except Exception:
        return None


def read_barcode_from_region(image_path: str, region: Tuple[int, int, int, int] = None) -> Optional[str]:
    """
    从图片的指定区域读取条码
    
    Args:
        image_path: 图片路径
        region: 区域 (x, y, width, height)，如果为None则自动检测顶部区域
        
    Returns:
        条码内容
    """
    if not PYZBAR_AVAILABLE:
        return None
    
    try:
        # 读取图片
        cv_img = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if cv_img is None:
            return None
        
        h, w = cv_img.shape[:2]
        
        if region:
            x, y, rw, rh = region
            cropped = cv_img[y:y+rh, x:x+rw]
        else:
            # 默认检测顶部20%区域（条码通常贴在上方）
            cropped = cv_img[0:int(h*0.2), :]
        
        # 转换为PIL格式
        img = Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB))
        
        barcodes = decode(img)
        if barcodes:
            return barcodes[0].data.decode('utf-8')
        
        return None
    except Exception as e:
        print(f"Region barcode read error: {e}")
        return None


def generate_barcode_image(content: str, output_path: str = None) -> Optional[str]:
    """
    生成条码图片
    
    Args:
        content: 条码内容
        output_path: 输出路径，如果为None则返回base64
        
    Returns:
        文件路径或base64字符串
    """
    try:
        import barcode
        from barcode.writer import ImageWriter
        from io import BytesIO
        import base64
        
        code128 = barcode.get_barcode_class('code128')
        barcode_obj = code128(content, writer=ImageWriter())
        
        if output_path:
            barcode_obj.save(output_path.replace('.png', ''))
            return output_path
        else:
            buffer = BytesIO()
            barcode_obj.write(buffer)
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        print(f"Barcode generation error: {e}")
        return None
