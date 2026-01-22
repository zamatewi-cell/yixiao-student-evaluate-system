# -*- coding: utf-8 -*-
"""扫描仪集成模块"""
from .barcode import read_barcode_from_image, read_barcode_from_region, generate_barcode_image
from .auto_grade import process_scanned_image, auto_grade_folder
from .watcher import ScannerWatcher, start_watcher, stop_watcher, get_watcher

__all__ = [
    'read_barcode_from_image',
    'read_barcode_from_region',
    'generate_barcode_image',
    'process_scanned_image',
    'auto_grade_folder',
    'ScannerWatcher',
    'start_watcher',
    'stop_watcher',
    'get_watcher'
]
