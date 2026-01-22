# -*- coding: utf-8 -*-
"""
错题分析模块
支持错题记录、知识点分析、AI智能诊断
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
import httpx
import json

from ..auth.dependencies import get_db_connection, require_teacher, CurrentUser

router = APIRouter(prefix="/api/wrong-answer", tags=["错题分析"])

# AI API配置
QWEN_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
QWEN_API_KEY = "sk-64b7fb2c08b44369981491e4c65b03f6"


class WrongAnswerRecord(BaseModel):
    """错题记录"""
    student_id: int
    exam_id: int
    subject_id: int
    question_number: int
    question_content: str
    correct_answer: Optional[str] = None
    student_answer: Optional[str] = None
    knowledge_point: Optional[str] = None
    error_type: Optional[str] = None  # 计算错误/概念混淆/粗心/不会


class WrongAnswerBatch(BaseModel):
    """批量错题录入"""
    exam_id: int
    subject_id: int
    records: List[WrongAnswerRecord]


class AnalysisRequest(BaseModel):
    """分析请求"""
    student_id: Optional[int] = None
    class_id: Optional[int] = None
    exam_id: Optional[int] = None
    subject_id: Optional[int] = None


async def call_ai_analysis(prompt: str) -> str:
    """调用AI分析"""
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "qwen-turbo",
        "input": {
            "messages": [
                {
                    "role": "system",
                    "content": """你是一位经验丰富的教育专家，擅长分析学生的错题情况。
请根据提供的错题数据，分析学生的知识点掌握情况，找出薄弱环节，并提供针对性的学习建议。

分析报告应包含：
1. 错误类型分布
2. 薄弱知识点识别
3. 问题根因分析
4. 针对性学习建议
5. 推荐练习方向

请用清晰的中文输出，语言专业但易于理解。"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        },
        "parameters": {
            "result_format": "message",
            "max_tokens": 2000,
            "temperature": 0.7
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(QWEN_API_URL, headers=headers, json=payload)
            if response.status_code == 200:
                result = response.json()
                return result.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "")
            return ""
    except Exception:
        return ""


def generate_local_analysis(wrong_answers: list) -> str:
    """本地生成分析报告"""
    total = len(wrong_answers)
    if total == 0:
        return "暂无错题数据"
    
    # 统计错误类型
    error_types = {}
    knowledge_points = {}
    
    for wa in wrong_answers:
        et = wa.get('error_type', '未分类')
        kp = wa.get('knowledge_point', '未分类')
        error_types[et] = error_types.get(et, 0) + 1
        knowledge_points[kp] = knowledge_points.get(kp, 0) + 1
    
    report = f"""## 错题分析报告

### 一、基本情况
- 错题总数: **{total}** 道

### 二、错误类型分布
"""
    for et, count in sorted(error_types.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        report += f"- {et}: {count}道 ({pct:.1f}%)\n"
    
    report += "\n### 三、薄弱知识点\n"
    for kp, count in sorted(knowledge_points.items(), key=lambda x: -x[1])[:5]:
        report += f"- **{kp}**: {count}道错题\n"
    
    report += """
### 四、学习建议
1. 重点复习上述薄弱知识点
2. 针对计算错误，注意做题时的审题和验算
3. 针对概念混淆，建议重新学习相关定义
4. 建议每周进行一次错题回顾

---
*分析时间: """ + datetime.now().strftime('%Y-%m-%d %H:%M') + "*"
    
    return report


# ============== 错题记录 ==============

@router.post("/record")
async def record_wrong_answer(
    record: WrongAnswerRecord,
    current_user: CurrentUser = Depends(require_teacher)
):
    """记录单条错题"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO wrong_answers 
            (student_id, exam_id, subject_id, question_number, 
             question_content, correct_answer, student_answer, 
             knowledge_point, error_type, recorded_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            record.student_id, record.exam_id, record.subject_id,
            record.question_number, record.question_content,
            record.correct_answer, record.student_answer,
            record.knowledge_point, record.error_type, current_user.id
        ))
        
        conn.commit()
        record_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        return {"message": "错题记录成功", "id": record_id}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def batch_record_wrong_answers(
    batch: WrongAnswerBatch,
    current_user: CurrentUser = Depends(require_teacher)
):
    """批量录入错题"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor()
        success_count = 0
        
        for record in batch.records:
            try:
                cursor.execute("""
                    INSERT INTO wrong_answers 
                    (student_id, exam_id, subject_id, question_number,
                     question_content, correct_answer, student_answer,
                     knowledge_point, error_type, recorded_by, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """, (
                    record.student_id, batch.exam_id, batch.subject_id,
                    record.question_number, record.question_content,
                    record.correct_answer, record.student_answer,
                    record.knowledge_point, record.error_type, current_user.id
                ))
                success_count += 1
            except Exception:
                pass
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": f"批量录入完成，成功{success_count}条", "success_count": success_count}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== 错题查询 ==============

@router.get("/student/{student_id}")
async def get_student_wrong_answers(
    student_id: int,
    exam_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    current_user: CurrentUser = Depends(require_teacher)
):
    """获取学生错题列表"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        sql = """
            SELECT wa.*, e.name as exam_name, es.subject_name
            FROM wrong_answers wa
            JOIN exams e ON wa.exam_id = e.id
            JOIN exam_subjects es ON wa.subject_id = es.id
            WHERE wa.student_id = %s
        """
        params = [student_id]
        
        if exam_id:
            sql += " AND wa.exam_id = %s"
            params.append(exam_id)
        if subject_id:
            sql += " AND wa.subject_id = %s"
            params.append(subject_id)
        
        sql += " ORDER BY wa.created_at DESC"
        
        cursor.execute(sql, tuple(params))
        results = cursor.fetchall()
        
        # 格式化日期
        for r in results:
            if r.get('created_at'):
                r['created_at'] = str(r['created_at'])
        
        cursor.close()
        conn.close()
        
        return {"data": results}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/class/{class_id}")
async def get_class_wrong_answers(
    class_id: int,
    exam_id: Optional[int] = None,
    current_user: CurrentUser = Depends(require_teacher)
):
    """获取班级错题统计"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 知识点错误统计
        sql = """
            SELECT wa.knowledge_point, COUNT(*) as count
            FROM wrong_answers wa
            JOIN students s ON wa.student_id = s.id
            WHERE s.class_id = %s
        """
        params = [class_id]
        
        if exam_id:
            sql += " AND wa.exam_id = %s"
            params.append(exam_id)
        
        sql += " GROUP BY wa.knowledge_point ORDER BY count DESC LIMIT 10"
        
        cursor.execute(sql, tuple(params))
        knowledge_stats = cursor.fetchall()
        
        # 错误类型统计
        sql2 = """
            SELECT wa.error_type, COUNT(*) as count
            FROM wrong_answers wa
            JOIN students s ON wa.student_id = s.id
            WHERE s.class_id = %s
        """
        if exam_id:
            sql2 += " AND wa.exam_id = %s"
        sql2 += " GROUP BY wa.error_type ORDER BY count DESC"
        
        cursor.execute(sql2, tuple(params))
        error_type_stats = cursor.fetchall()
        
        # 学生错题数量排名
        sql3 = """
            SELECT s.id, s.name, COUNT(wa.id) as wrong_count
            FROM students s
            LEFT JOIN wrong_answers wa ON s.id = wa.student_id
            WHERE s.class_id = %s
        """
        if exam_id:
            sql3 += " AND (wa.exam_id = %s OR wa.exam_id IS NULL)"
        sql3 += " GROUP BY s.id, s.name ORDER BY wrong_count DESC LIMIT 10"
        
        cursor.execute(sql3, tuple(params))
        student_stats = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "data": {
                "knowledge_stats": knowledge_stats,
                "error_type_stats": error_type_stats,
                "student_stats": student_stats
            }
        }
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


# ============== AI分析 ==============

@router.post("/analyze")
async def analyze_wrong_answers(
    request: AnalysisRequest,
    current_user: CurrentUser = Depends(require_teacher)
):
    """AI分析错题情况"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 构建查询条件
        sql = """
            SELECT wa.*, s.name as student_name, e.name as exam_name, es.subject_name
            FROM wrong_answers wa
            JOIN students s ON wa.student_id = s.id
            JOIN exams e ON wa.exam_id = e.id
            JOIN exam_subjects es ON wa.subject_id = es.id
            WHERE 1=1
        """
        params = []
        
        if request.student_id:
            sql += " AND wa.student_id = %s"
            params.append(request.student_id)
        if request.class_id:
            sql += " AND s.class_id = %s"
            params.append(request.class_id)
        if request.exam_id:
            sql += " AND wa.exam_id = %s"
            params.append(request.exam_id)
        if request.subject_id:
            sql += " AND wa.subject_id = %s"
            params.append(request.subject_id)
        
        sql += " ORDER BY wa.created_at DESC LIMIT 100"
        
        cursor.execute(sql, tuple(params))
        wrong_answers = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        if not wrong_answers:
            return {"analysis": "暂无错题数据可分析", "stats": {}}
        
        # 构建AI分析提示
        prompt = f"请分析以下{len(wrong_answers)}道错题的情况：\n\n"
        
        for i, wa in enumerate(wrong_answers[:20], 1):  # 限制提示长度
            prompt += f"**错题{i}**\n"
            prompt += f"- 题目: {wa.get('question_content', '未知')}\n"
            prompt += f"- 知识点: {wa.get('knowledge_point', '未分类')}\n"
            prompt += f"- 错误类型: {wa.get('error_type', '未分类')}\n"
            prompt += f"- 正确答案: {wa.get('correct_answer', '无')}\n"
            prompt += f"- 学生答案: {wa.get('student_answer', '无')}\n\n"
        
        prompt += "\n请生成详细的错题分析报告和学习建议。"
        
        # 尝试AI分析
        analysis = await call_ai_analysis(prompt)
        if not analysis:
            analysis = generate_local_analysis(wrong_answers)
        
        # 统计数据
        error_types = {}
        knowledge_points = {}
        for wa in wrong_answers:
            et = wa.get('error_type', '未分类')
            kp = wa.get('knowledge_point', '未分类')
            error_types[et] = error_types.get(et, 0) + 1
            knowledge_points[kp] = knowledge_points.get(kp, 0) + 1
        
        return {
            "analysis": analysis,
            "stats": {
                "total_count": len(wrong_answers),
                "error_types": error_types,
                "knowledge_points": knowledge_points
            }
        }
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))
