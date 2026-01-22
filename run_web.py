# -*- coding: utf-8 -*-
"""
Start the AI Calligraphy Web Server
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# Create necessary directories
(project_root / 'uploads').mkdir(exist_ok=True)
(project_root / 'src' / 'web' / 'static').mkdir(parents=True, exist_ok=True)

def check_mysql():
    """Check MySQL connection"""
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Zrx@060309'
        )
        conn.close()
        return True
    except Exception as e:
        print(f"MySQL connection failed: {e}")
        print("Please make sure MySQL is running")
        return False

def main():
    print("=" * 60)
    print("  AI Calligraphy Grading System - Web Server")
    print("=" * 60)
    
    # Check MySQL
    print("\nChecking MySQL connection...")
    if not check_mysql():
        print("\nWarning: MySQL not available. Starting anyway...")
    
    print("\nStarting server...")
    print("Open browser: http://localhost:8000")
    print("API docs: http://localhost:8000/docs")
    print("Press Ctrl+C to stop\n")
    
    import uvicorn
    uvicorn.run(
        "src.web.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    main()
