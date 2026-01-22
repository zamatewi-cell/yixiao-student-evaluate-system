# -*- coding: utf-8 -*-
"""
成绩单与报告生成模块
生成可打印的学生成绩单和评价报告
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
import io

from ..auth.dependencies import get_db_connection, require_teacher, CurrentUser

router = APIRouter(prefix="/api/report", tags=["报告生成"])


def generate_html_report(student: dict, scores: list, comments: dict, school_info: dict) -> str:
    """生成HTML格式的成绩单（可直接打印或转PDF）"""
    
    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>学生成绩报告单 - {student['name']}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: "Microsoft YaHei", SimHei, sans-serif; 
            padding: 20mm;
            background: white;
        }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .header h1 {{ font-size: 24px; margin-bottom: 10px; }}
        .header p {{ color: #666; font-size: 14px; }}
        
        .student-info {{ 
            display: flex; 
            justify-content: space-between;
            margin-bottom: 20px;
            padding: 15px;
            background: #f5f5f5;
            border-radius: 8px;
        }}
        .student-info div {{ text-align: center; }}
        .student-info .label {{ color: #666; font-size: 12px; }}
        .student-info .value {{ font-size: 16px; font-weight: bold; margin-top: 5px; }}
        
        .section {{ margin-bottom: 25px; }}
        .section-title {{ 
            font-size: 16px; 
            font-weight: bold; 
            border-left: 4px solid #1890ff;
            padding-left: 10px;
            margin-bottom: 15px;
        }}
        
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin-bottom: 20px;
        }}
        th, td {{ 
            border: 1px solid #ddd; 
            padding: 10px; 
            text-align: center;
        }}
        th {{ background: #f0f0f0; font-weight: bold; }}
        
        .score-excellent {{ color: #52c41a; font-weight: bold; }}
        .score-pass {{ color: #1890ff; }}
        .score-fail {{ color: #ff4d4f; }}
        
        .comment-box {{
            padding: 15px;
            background: #fafafa;
            border-radius: 8px;
            border: 1px solid #e8e8e8;
            line-height: 1.8;
        }}
        
        .footer {{
            margin-top: 40px;
            display: flex;
            justify-content: space-between;
        }}
        .footer .sign-area {{
            text-align: center;
        }}
        .footer .sign-line {{
            width: 150px;
            border-bottom: 1px solid #333;
            margin-top: 40px;
        }}
        
        .print-only {{ display: none; }}
        @media print {{
            body {{ padding: 10mm; }}
            .print-only {{ display: block; }}
            .no-print {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{school_info.get('school_name', '学校')}学生成绩报告单</h1>
        <p>{student.get('semester_name', '')} · 打印时间：{datetime.now().strftime('%Y年%m月%d日')}</p>
    </div>
    
    <div class="student-info">
        <div>
            <div class="label">姓名</div>
            <div class="value">{student['name']}</div>
        </div>
        <div>
            <div class="label">学号</div>
            <div class="value">{student.get('student_no', '-')}</div>
        </div>
        <div>
            <div class="label">班级</div>
            <div class="value">{student.get('class_name', '-')}</div>
        </div>
        <div>
            <div class="label">班主任</div>
            <div class="value">{student.get('head_teacher', '-')}</div>
        </div>
    </div>
"""
    
    # 成绩表格
    if scores:
        html += """
    <div class="section">
        <h3 class="section-title">学业成绩</h3>
        <table>
            <thead>
                <tr>
                    <th>考试</th>
                    <th>科目</th>
                    <th>分数</th>
                    <th>班级排名</th>
                    <th>年级排名</th>
                    <th>等级</th>
                </tr>
            </thead>
            <tbody>
"""
        for s in scores:
            score = s.get('score', 0) or 0
            if score >= 85:
                score_class = 'score-excellent'
                grade = '优秀'
            elif score >= 60:
                score_class = 'score-pass'
                grade = '合格'
            else:
                score_class = 'score-fail'
                grade = '待提高'
            
            html += f"""
                <tr>
                    <td>{s.get('exam_name', '-')}</td>
                    <td>{s.get('subject_name', '-')}</td>
                    <td class="{score_class}">{score}</td>
                    <td>{s.get('class_rank', '-')}</td>
                    <td>{s.get('grade_rank', '-')}</td>
                    <td>{grade}</td>
                </tr>
"""
        html += """
            </tbody>
        </table>
    </div>
"""
    
    # 评语
    if comments:
        html += f"""
    <div class="section">
        <h3 class="section-title">教师评语</h3>
        <div class="comment-box">
            {comments.get('teacher_comment', comments.get('ai_comment', '暂无评语'))}
        </div>
    </div>
"""
    
    # 页脚签名区
    html += f"""
    <div class="footer">
        <div class="sign-area">
            <p>班主任签名</p>
            <div class="sign-line"></div>
        </div>
        <div class="sign-area">
            <p>学校盖章</p>
            <div class="sign-line"></div>
        </div>
        <div class="sign-area">
            <p>家长签名</p>
            <div class="sign-line"></div>
        </div>
    </div>
    
    <script>
        // 自动打印
        // window.onload = function() {{ window.print(); }}
    </script>
</body>
</html>
"""
    return html


@router.get("/student-report/{student_id}")
async def generate_student_report(
    student_id: int,
    semester_id: Optional[int] = None,
    exam_id: Optional[int] = None,
    current_user: CurrentUser = Depends(require_teacher)
):
    """生成学生成绩报告单（HTML格式）"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取学生信息
        cursor.execute("""
            SELECT s.*, c.name as class_name, g.name as grade_name,
                   t.name as head_teacher, sem.name as semester_name
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
            LEFT JOIN grades g ON c.grade_id = g.id
            LEFT JOIN teachers t ON c.head_teacher_id = t.id
            LEFT JOIN semesters sem ON sem.is_current = TRUE
            WHERE s.id = %s
        """, (student_id,))
        student = cursor.fetchone()
        
        if not student:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="学生不存在")
        
        # 获取成绩
        sql = """
            SELECT es.score, es.class_rank, es.grade_rank,
                   e.name as exam_name, sub.subject_name
            FROM exam_scores es
            JOIN exams e ON es.exam_id = e.id
            JOIN exam_subjects sub ON es.subject_id = sub.id
            WHERE es.student_id = %s
        """
        params = [student_id]
        
        if exam_id:
            sql += " AND es.exam_id = %s"
            params.append(exam_id)
        
        sql += " ORDER BY e.exam_date DESC, sub.sort_order"
        
        cursor.execute(sql, tuple(params))
        scores = cursor.fetchall()
        
        # 获取评语
        cursor.execute("""
            SELECT ai_comment, teacher_comment
            FROM comments
            WHERE student_id = %s
            ORDER BY created_at DESC LIMIT 1
        """, (student_id,))
        comments = cursor.fetchone() or {}
        
        # 获取学校信息
        cursor.execute("SELECT config_key, config_value FROM system_configs WHERE config_key LIKE 'school_%'")
        school_rows = cursor.fetchall()
        school_info = {row['config_key']: row['config_value'] for row in school_rows}
        
        cursor.close()
        conn.close()
        
        # 生成HTML报告
        html_content = generate_html_report(student, scores, comments, school_info)
        
        return StreamingResponse(
            io.BytesIO(html_content.encode('utf-8')),
            media_type='text/html',
            headers={
                'Content-Disposition': f'inline; filename=report_{student["student_no"]}_{datetime.now().strftime("%Y%m%d")}.html'
            }
        )
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/class-report/{class_id}")
async def generate_class_report(
    class_id: int,
    exam_id: int,
    current_user: CurrentUser = Depends(require_teacher)
):
    """生成班级成绩汇总报告"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取班级信息
        cursor.execute("""
            SELECT c.name as class_name, g.name as grade_name, e.name as exam_name
            FROM classes c
            LEFT JOIN grades g ON c.grade_id = g.id
            LEFT JOIN exams e ON e.id = %s
            WHERE c.id = %s
        """, (exam_id, class_id))
        info = cursor.fetchone()
        
        if not info:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="班级不存在")
        
        # 获取班级学生成绩
        cursor.execute("""
            SELECT s.student_no, s.name as student_name,
                   GROUP_CONCAT(CONCAT(sub.subject_name, ':', IFNULL(es.score, '-')) SEPARATOR '|') as scores,
                   SUM(es.score) as total_score
            FROM students s
            LEFT JOIN exam_scores es ON s.id = es.student_id AND es.exam_id = %s
            LEFT JOIN exam_subjects sub ON es.subject_id = sub.id
            WHERE s.class_id = %s AND s.status = 'active'
            GROUP BY s.id, s.student_no, s.name
            ORDER BY total_score DESC
        """, (exam_id, class_id))
        students = cursor.fetchall()
        
        # 获取科目列表
        cursor.execute("""
            SELECT subject_name FROM exam_subjects 
            WHERE exam_id = %s ORDER BY sort_order
        """, (exam_id,))
        subjects = [r['subject_name'] for r in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        # 处理成绩数据
        for student in students:
            score_dict = {}
            if student.get('scores'):
                for item in student['scores'].split('|'):
                    if ':' in item:
                        subj, score = item.split(':')
                        score_dict[subj] = score
            student['score_details'] = score_dict
            student['total_score'] = float(student['total_score']) if student['total_score'] else 0
        
        return {
            "data": {
                "info": info,
                "subjects": subjects,
                "students": students
            }
        }
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))
