# -*- coding: utf-8 -*-
"""
文件夹监控模块 - 监控扫描仪输出目录
"""
import os
import sys
import time
import threading
from pathlib import Path
from datetime import datetime

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("Warning: watchdog not installed. Folder watching disabled.")
    print("Install with: pip install watchdog")


class ScannerFolderHandler(FileSystemEventHandler):
    """扫描仪文件夹事件处理器"""
    
    def __init__(self, upload_dir: str, use_ai: bool = True, callback=None):
        self.upload_dir = upload_dir
        self.use_ai = use_ai
        self.callback = callback
        self.processing = set()  # 正在处理的文件
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    
    def on_created(self, event):
        """文件创建事件"""
        if event.is_directory:
            return
        
        file_path = event.src_path
        ext = Path(file_path).suffix.lower()
        
        if ext not in self.image_extensions:
            return
        
        # 避免重复处理
        if file_path in self.processing:
            return
        
        self.processing.add(file_path)
        
        # 延迟处理，等待文件写入完成
        threading.Timer(2.0, self._process_file, args=[file_path]).start()
    
    def _process_file(self, file_path: str):
        """处理文件"""
        try:
            # 检查文件是否存在且可读
            if not os.path.exists(file_path):
                return
            
            # 等待文件写入完成
            time.sleep(1)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] New file detected: {Path(file_path).name}")
            
            from .auto_grade import process_scanned_image
            result = process_scanned_image(file_path, self.upload_dir, self.use_ai)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Result: {result['message']}")
            
            if self.callback:
                self.callback(result)
            
            # 移动已处理文件
            processed_dir = Path(file_path).parent / 'processed'
            processed_dir.mkdir(exist_ok=True)
            try:
                import shutil
                shutil.move(file_path, str(processed_dir / Path(file_path).name))
            except:
                pass
            
        except Exception as e:
            print(f"Processing error: {e}")
        finally:
            self.processing.discard(file_path)


class ScannerWatcher:
    """扫描仪文件夹监控器"""
    
    def __init__(self, watch_folder: str, upload_dir: str, use_ai: bool = True):
        self.watch_folder = watch_folder
        self.upload_dir = upload_dir
        self.use_ai = use_ai
        self.observer = None
        self.running = False
        self.results = []
    
    def _on_result(self, result: dict):
        """处理结果回调"""
        self.results.append(result)
    
    def start(self):
        """启动监控"""
        if not WATCHDOG_AVAILABLE:
            print("Error: watchdog not available")
            return False
        
        if self.running:
            return True
        
        # 确保目录存在
        Path(self.watch_folder).mkdir(parents=True, exist_ok=True)
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
        
        handler = ScannerFolderHandler(
            upload_dir=self.upload_dir,
            use_ai=self.use_ai,
            callback=self._on_result
        )
        
        self.observer = Observer()
        self.observer.schedule(handler, self.watch_folder, recursive=False)
        self.observer.start()
        self.running = True
        
        print(f"Scanner watcher started. Monitoring: {self.watch_folder}")
        return True
    
    def stop(self):
        """停止监控"""
        if self.observer and self.running:
            self.observer.stop()
            self.observer.join()
            self.running = False
            print("Scanner watcher stopped.")
    
    def is_running(self) -> bool:
        """检查是否运行中"""
        return self.running
    
    def get_results(self) -> list:
        """获取处理结果"""
        return self.results


# 全局监控器实例
_watcher_instance = None


def get_watcher() -> ScannerWatcher:
    """获取全局监控器实例"""
    global _watcher_instance
    return _watcher_instance


def start_watcher(watch_folder: str, upload_dir: str, use_ai: bool = True) -> ScannerWatcher:
    """启动全局监控器"""
    global _watcher_instance
    
    if _watcher_instance and _watcher_instance.is_running():
        _watcher_instance.stop()
    
    _watcher_instance = ScannerWatcher(watch_folder, upload_dir, use_ai)
    _watcher_instance.start()
    return _watcher_instance


def stop_watcher():
    """停止全局监控器"""
    global _watcher_instance
    if _watcher_instance:
        _watcher_instance.stop()


if __name__ == "__main__":
    # 测试用
    import argparse
    
    parser = argparse.ArgumentParser(description="Scanner Folder Watcher")
    parser.add_argument('--watch', type=str, default='E:/scanner_output', help='Watch folder')
    parser.add_argument('--upload', type=str, default='./uploads', help='Upload folder')
    parser.add_argument('--no-ai', action='store_true', help='Disable AI scoring')
    
    args = parser.parse_args()
    
    watcher = start_watcher(args.watch, args.upload, not args.no_ai)
    
    print(f"Watching folder: {args.watch}")
    print("Press Ctrl+C to stop...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_watcher()
        print("Stopped.")
