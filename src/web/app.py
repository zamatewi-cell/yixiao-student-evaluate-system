# -*- coding: utf-8 -*-
"""
AI Calligraphy Web Application - Backend API
学生成长综合素质评价系统
FastAPI + MySQL
"""
import os
import sys
import json
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import routers
from .auth import router as auth_router
from .admin import router as admin_router
from .teacher import router as teacher_router
from .student import router as student_router
from .statistics import router as statistics_router
from .exam import router as exam_router
from .attendance import router as attendance_router
from .import_export import import_export_router
from .ai_analysis import ai_analysis_router
from .teacher_role import teacher_role_router
from .wrong_answer import wrong_answer_router
from .system_config import system_config_router
from .audit_log import audit_log_router
from .notice import notice_router
from .report import report_router
from .health import health_router

# Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Zrx@060309',
    'database': 'calligraphy_ai',
    'charset': 'utf8mb4'
}

UPLOAD_DIR = Path(__file__).parent.parent.parent / 'uploads'
UPLOAD_DIR.mkdir(exist_ok=True)

# Load grading config
CONFIG_PATH = Path(__file__).parent.parent.parent / 'configs' / 'config.yaml'
if CONFIG_PATH.exists():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        GRADING_CONFIG = yaml.safe_load(f)
else:
    GRADING_CONFIG = {}

# API Key for Qwen
QWEN_API_KEY = 'sk-64b7fb2c08b44369981491e4c65b03f6'

# FastAPI app
app = FastAPI(
    title="学生综合素质评价系统",
    description="Student Comprehensive Quality Evaluation System API",
    version="2.2.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
STATIC_DIR = Path(__file__).parent / 'static'
STATIC_DIR.mkdir(exist_ok=True)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Register routers
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(teacher_router)
app.include_router(student_router)
app.include_router(statistics_router)
app.include_router(exam_router)
app.include_router(attendance_router)
app.include_router(import_export_router)
app.include_router(ai_analysis_router)
app.include_router(teacher_role_router)
app.include_router(wrong_answer_router)
app.include_router(system_config_router)
app.include_router(audit_log_router)
app.include_router(notice_router)
app.include_router(report_router)
app.include_router(health_router)

# Response Models
class GradingResult(BaseModel):
    id: int
    filename: str
    original_filename: str
    upload_time: str
    overall_score: Optional[float]
    grade: Optional[str]
    char_count: int
    ai_comment: Optional[str]
    strengths: Optional[str]
    suggestions: Optional[str]
    status: str
    file_url: str


class SearchResult(BaseModel):
    total: int
    page: int
    page_size: int
    results: List[GradingResult]


# Database connection
def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Database connection error: {e}")
        return None


def init_database():
    """Initialize database tables"""
    try:
        # Connect without database first
        config_no_db = DB_CONFIG.copy()
        config_no_db.pop('database', None)
        conn = mysql.connector.connect(**config_no_db)
        cursor = conn.cursor()
        
        # Create database
        cursor.execute("CREATE DATABASE IF NOT EXISTS calligraphy_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute("USE calligraphy_ai")
        
        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS grading_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                original_filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                overall_score DECIMAL(5,2),
                grade VARCHAR(20),
                char_count INT DEFAULT 0,
                ai_comment TEXT,
                strengths TEXT,
                suggestions TEXT,
                char_details JSON,
                status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_filename (filename),
                INDEX idx_original_filename (original_filename),
                INDEX idx_upload_time (upload_time),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialized successfully")
        return True
    except Error as e:
        print(f"Database init error: {e}")
        return False


# Grading function
def grade_image(image_path: str, use_ai: bool = True) -> dict:
    """Grade an image using the grading system"""
    try:
        from src.api.grader import CalligraphyGrader
        
        grader = CalligraphyGrader(
            config=GRADING_CONFIG,
            api_key=QWEN_API_KEY if use_ai else None,
            use_ai=use_ai
        )
        
        # Basic grading
        result = grader.grade(image_path)
        
        # AI grading if enabled
        ai_result = {}
        if use_ai and hasattr(grader, 'grade_with_ai'):
            try:
                ai_result = grader.grade_with_ai(image_path)
            except Exception as e:
                print(f"AI grading error: {e}")
        
        return {
            'success': True,
            'overall_score': result.get('overall_score', 0),
            'char_count': result.get('char_count', 0),
            'chars': result.get('chars', []),
            'ai_comment': ai_result.get('overall_comment', ''),
            'strengths': ', '.join(ai_result.get('feedback', {}).get('strengths', [])),
            'suggestions': ', '.join(ai_result.get('feedback', {}).get('suggestions', []))
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_grade_from_score(score: float) -> str:
    """Convert score to grade"""
    if score >= 90:
        return "Excellent"
    elif score >= 80:
        return "Good"
    elif score >= 70:
        return "Medium"
    elif score >= 60:
        return "Pass"
    else:
        return "NeedImprove"


# API Endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    init_database()


@app.get("/", response_class=HTMLResponse)
async def root():
    """Redirect to frontend"""
    return """
    <html>
        <head><meta http-equiv="refresh" content="0; url=/static/index.html"></head>
        <body>Redirecting...</body>
    </html>
    """


@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...), use_ai: bool = True):
    """Upload and grade an image with barcode recognition"""
    # Validate file type
    allowed_types = ['image/jpeg', 'image/png', 'image/bmp']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, BMP images are allowed")
    
    # Generate unique filename
    ext = Path(file.filename).suffix or '.jpg'
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    try:
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
    
    # Try to read barcode from image
    barcode_value = None
    student_id = None
    try:
        from .scanner.barcode import read_barcode_from_image
        barcode_value = read_barcode_from_image(str(file_path))
        
        # If barcode found, try to match student
        if barcode_value:
            conn_temp = get_db_connection()
            if conn_temp:
                cursor_temp = conn_temp.cursor(dictionary=True)
                cursor_temp.execute(
                    "SELECT id, name FROM students WHERE student_no = %s OR barcode = %s",
                    (barcode_value, barcode_value)
                )
                student = cursor_temp.fetchone()
                if student:
                    student_id = student['id']
                cursor_temp.close()
                conn_temp.close()
    except Exception as e:
        print(f"Barcode reading error: {e}")
    
    # Insert record into database
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO grading_records (filename, original_filename, file_path, barcode, student_id, status)
            VALUES (%s, %s, %s, %s, %s, 'processing')
        """, (unique_filename, file.filename, str(file_path), barcode_value, student_id))
        conn.commit()
        record_id = cursor.lastrowid
        cursor.close()
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    
    # Grade the image
    grade_result = grade_image(str(file_path), use_ai=use_ai)
    
    # Update record with results
    try:
        cursor = conn.cursor()
        if grade_result['success']:
            score = grade_result['overall_score']
            grade = get_grade_from_score(score) if score else None
            
            cursor.execute("""
                UPDATE grading_records 
                SET overall_score = %s, grade = %s, char_count = %s,
                    ai_comment = %s, strengths = %s, suggestions = %s,
                    char_details = %s, status = 'completed'
                WHERE id = %s
            """, (
                score, grade, grade_result['char_count'],
                grade_result.get('ai_comment', ''),
                grade_result.get('strengths', ''),
                grade_result.get('suggestions', ''),
                json.dumps(grade_result.get('chars', []), ensure_ascii=False),
                record_id
            ))
        else:
            cursor.execute("""
                UPDATE grading_records 
                SET status = 'failed', error_message = %s
                WHERE id = %s
            """, (grade_result.get('error', 'Unknown error'), record_id))
        
        conn.commit()
        cursor.close()
    except Error as e:
        print(f"Update error: {e}")
    finally:
        conn.close()
    
    # Return result
    return {
        "id": record_id,
        "filename": unique_filename,
        "original_filename": file.filename,
        "file_url": f"/uploads/{unique_filename}",
        "barcode": barcode_value,
        "student_id": student_id,
        "overall_score": grade_result.get('overall_score'),
        "grade": get_grade_from_score(grade_result.get('overall_score', 0)) if grade_result['success'] else None,
        "char_count": grade_result.get('char_count', 0),
        "ai_comment": grade_result.get('ai_comment', ''),
        "strengths": grade_result.get('strengths', ''),
        "suggestions": grade_result.get('suggestions', ''),
        "status": "completed" if grade_result['success'] else "failed",
        "error": grade_result.get('error') if not grade_result['success'] else None
    }


@app.get("/api/records")
async def get_records(
    search: Optional[str] = Query(None, description="Search by filename"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """Get grading records with search and pagination"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Build query
        where_clause = ""
        params = []
        
        if search:
            where_clause = "WHERE original_filename LIKE %s OR filename LIKE %s"
            search_pattern = f"%{search}%"
            params = [search_pattern, search_pattern]
        
        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM grading_records {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # Get records
        offset = (page - 1) * page_size
        query = f"""
            SELECT id, filename, original_filename, file_path, upload_time,
                   overall_score, grade, char_count, ai_comment, strengths, suggestions, status, barcode, student_id
            FROM grading_records
            {where_clause}
            ORDER BY upload_time DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, params + [page_size, offset])
        records = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Format results
        results = []
        for r in records:
            results.append({
                "id": r['id'],
                "filename": r['filename'],
                "original_filename": r['original_filename'],
                "upload_time": r['upload_time'].strftime('%Y-%m-%d %H:%M:%S') if r['upload_time'] else '',
                "overall_score": float(r['overall_score']) if r['overall_score'] else None,
                "grade": r['grade'],
                "char_count": r['char_count'],
                "ai_comment": r['ai_comment'],
                "strengths": r['strengths'],
                "suggestions": r['suggestions'],
                "status": r['status'],
                "file_url": f"/uploads/{r['filename']}",
                "barcode": r.get('barcode'),
                "student_id": r.get('student_id')
            })
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "results": results
        }
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Query error: {e}")


@app.get("/api/records/{record_id}")
async def get_record_detail(record_id: int):
    """Get detailed grading record"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM grading_records WHERE id = %s
        """, (record_id,))
        record = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")
        
        # Parse char_details JSON
        char_details = []
        if record.get('char_details'):
            try:
                char_details = json.loads(record['char_details'])
            except:
                pass
        
        return {
            "id": record['id'],
            "filename": record['filename'],
            "original_filename": record['original_filename'],
            "upload_time": record['upload_time'].strftime('%Y-%m-%d %H:%M:%S') if record['upload_time'] else '',
            "overall_score": float(record['overall_score']) if record['overall_score'] else None,
            "grade": record['grade'],
            "char_count": record['char_count'],
            "ai_comment": record['ai_comment'],
            "strengths": record['strengths'],
            "suggestions": record['suggestions'],
            "char_details": char_details,
            "status": record['status'],
            "file_url": f"/uploads/{record['filename']}"
        }
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Query error: {e}")


@app.delete("/api/records/{record_id}")
async def delete_record(record_id: int):
    """Delete a grading record"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Get file path first
        cursor.execute("SELECT file_path FROM grading_records WHERE id = %s", (record_id,))
        record = cursor.fetchone()
        
        if not record:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="Record not found")
        
        # Delete from database
        cursor.execute("DELETE FROM grading_records WHERE id = %s", (record_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        # Delete file
        try:
            file_path = Path(record['file_path'])
            if file_path.exists():
                file_path.unlink()
        except:
            pass
        
        return {"message": "Record deleted successfully"}
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Delete error: {e}")


@app.get("/api/stats")
async def get_stats():
    """Get grading statistics"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # Total records
        cursor.execute("SELECT COUNT(*) as total FROM grading_records")
        total = cursor.fetchone()['total']
        
        # Average score
        cursor.execute("SELECT AVG(overall_score) as avg_score FROM grading_records WHERE status = 'completed'")
        avg_score = cursor.fetchone()['avg_score']
        
        # Grade distribution
        cursor.execute("""
            SELECT grade, COUNT(*) as count 
            FROM grading_records 
            WHERE status = 'completed' AND grade IS NOT NULL
            GROUP BY grade
        """)
        grade_dist = {row['grade']: row['count'] for row in cursor.fetchall()}
        
        # Total characters graded
        cursor.execute("SELECT SUM(char_count) as total_chars FROM grading_records WHERE status = 'completed'")
        total_chars = cursor.fetchone()['total_chars'] or 0
        
        cursor.close()
        conn.close()
        
        return {
            "total_records": total,
            "average_score": round(float(avg_score), 1) if avg_score else 0,
            "grade_distribution": grade_dist,
            "total_characters": int(total_chars)
        }
    except Error as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Stats error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
