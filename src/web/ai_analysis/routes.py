# -*- coding: utf-8 -*-
"""
AI试卷分析路由模块
使用大语言模型分析试卷成绩，生成分析报告
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error
import httpx
import json

from ..auth.dependencies import get_db_connection, require_teacher, CurrentUser

router = APIRouter(prefix="/api/ai-analysis", tags=["AI分析"])

# AI API配置（使用通义千问）
QWEN_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
QWEN_API_KEY = "sk-64b7fb2c08b44369981491e4c65b03f6"


class AnalysisRequest(BaseModel):
    """分析请求"""
    exam_id: int
    subject_id: int
    class_id: Optional[int] = None


async def call_qwen_api(prompt: str) -> str:
    """调用通义千问API"""
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
                    "content": """你是一位经验丰富的教育专家和数据分析师。
你的任务是根据学生的考试成绩数据，生成专业的试卷分析报告。
分析报告应该包括：
1. 整体情况概述
2. 成绩分布分析
3. 存在的问题
4. 教学建议
5. 对学生的具体建议

请用中文回答，语言要专业但易于理解。"""
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
            else:
                return f"API调用失败: {response.text}"
    except Exception as e:
        return f"AI分析服务暂时不可用: {str(e)}"


def generate_local_analysis(stats: dict, scores: list) -> str:
    """本地生成分析报告（备用方案）"""
    avg = stats.get('avg_score', 0)
    max_score = stats.get('max_score', 0)
    min_score = stats.get('min_score', 0)
    pass_rate = stats.get('pass_rate', 0)
    excellent_rate = stats.get('excellent_rate', 0)
    total = stats.get('total_count', 0)
    
    # 成绩分布
    score_ranges = {'优秀(85+)': 0, '良好(75-84)': 0, '及格(60-74)': 0, '不及格(<60)': 0}
    for s in scores:
        score = s.get('score', 0) or 0
        if score >= 85:
            score_ranges['优秀(85+)'] += 1
        elif score >= 75:
            score_ranges['良好(75-84)'] += 1
        elif score >= 60:
            score_ranges['及格(60-74)'] += 1
        else:
            score_ranges['不及格(<60)'] += 1
    
    report = f"""## 试卷分析报告

### 一、整体情况

本次考试共有 **{total}** 名学生参加。

| 指标 | 数值 |
|------|------|
| 平均分 | {avg:.1f} |
| 最高分 | {max_score} |
| 最低分 | {min_score} |
| 及格率 | {pass_rate:.1f}% |
| 优秀率 | {excellent_rate:.1f}% |

### 二、成绩分布

"""
    for range_name, count in score_ranges.items():
        pct = count / total * 100 if total > 0 else 0
        report += f"- {range_name}: {count}人 ({pct:.1f}%)\n"
    
    # 评价
    report += "\n### 三、整体评价\n\n"
    
    if avg >= 85:
        report += "本次考试整体成绩**优秀**，说明学生对知识掌握较好。\n"
    elif avg >= 75:
        report += "本次考试整体成绩**良好**，大部分学生能够掌握基础知识。\n"
    elif avg >= 60:
        report += "本次考试整体成绩**一般**，需要加强对薄弱环节的辅导。\n"
    else:
        report += "本次考试整体成绩**不理想**，建议全面复习相关知识点。\n"
    
    if pass_rate < 60:
        report += "\n⚠️ **警示**: 及格率较低，建议：\n"
        report += "1. 分析学生失分的主要原因\n"
        report += "2. 针对共性问题进行集中讲解\n"
        report += "3. 对后进生进行个别辅导\n"
    
    if excellent_rate > 30:
        report += "\n✨ **亮点**: 优秀率较高，可以：\n"
        report += "1. 适当提高教学难度\n"
        report += "2. 让优秀学生帮助其他同学\n"
    
    report += "\n### 四、教学建议\n\n"
    report += "1. 针对错误率较高的题目进行重点讲解\n"
    report += "2. 设计针对性练习巩固薄弱知识点\n"
    report += "3. 关注学习困难学生，提供个性化辅导\n"
    report += "4. 定期进行小测验，及时了解学情\n"
    
    report += f"\n---\n*分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*"
    
    return report


@router.post("/generate")
async def generate_analysis(
    request: AnalysisRequest,
    current_user: CurrentUser = Depends(require_teacher)
):
    """生成AI试卷分析"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取考试和科目信息
        cursor.execute("""
            SELECT e.name as exam_name, es.subject_name, es.full_score, es.pass_score, es.excellent_score
            FROM exams e
            JOIN exam_subjects es ON e.id = es.exam_id
            WHERE e.id = %s AND es.id = %s
        """, (request.exam_id, request.subject_id))
        exam_info = cursor.fetchone()
        
        if not exam_info:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="考试或科目不存在")
        
        # 获取成绩数据
        sql = """
            SELECT s.name as student_name, c.name as class_name, sc.score
            FROM exam_scores sc
            JOIN students s ON sc.student_id = s.id
            LEFT JOIN classes c ON s.class_id = c.id
            WHERE sc.exam_id = %s AND sc.subject_id = %s AND sc.score IS NOT NULL
        """
        params = [request.exam_id, request.subject_id]
        
        if request.class_id:
            sql += " AND s.class_id = %s"
            params.append(request.class_id)
        
        cursor.execute(sql, tuple(params))
        scores = cursor.fetchall()
        
        if not scores:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=400, detail="没有可分析的成绩数据")
        
        # 计算统计数据
        score_values = [s['score'] for s in scores if s['score'] is not None]
        total_count = len(score_values)
        avg_score = sum(score_values) / total_count if total_count > 0 else 0
        max_score = max(score_values) if score_values else 0
        min_score = min(score_values) if score_values else 0
        pass_count = sum(1 for s in score_values if s >= exam_info['pass_score'])
        excellent_count = sum(1 for s in score_values if s >= exam_info['excellent_score'])
        
        stats = {
            'total_count': total_count,
            'avg_score': avg_score,
            'max_score': float(max_score),
            'min_score': float(min_score),
            'pass_count': pass_count,
            'excellent_count': excellent_count,
            'pass_rate': pass_count / total_count * 100 if total_count > 0 else 0,
            'excellent_rate': excellent_count / total_count * 100 if total_count > 0 else 0
        }
        
        # 构建AI分析的prompt
        prompt = f"""请分析以下考试成绩数据并生成专业的分析报告：

考试名称：{exam_info['exam_name']}
科目：{exam_info['subject_name']}
满分：{exam_info['full_score']}分
及格线：{exam_info['pass_score']}分
优秀线：{exam_info['excellent_score']}分

成绩统计：
- 参考人数：{stats['total_count']}人
- 平均分：{stats['avg_score']:.1f}
- 最高分：{stats['max_score']}
- 最低分：{stats['min_score']}
- 及格人数：{stats['pass_count']}人（{stats['pass_rate']:.1f}%）
- 优秀人数：{stats['excellent_count']}人（{stats['excellent_rate']:.1f}%）

各分数段分布：
"""
        # 计算分数段
        ranges = [(90, 100, '90-100'), (80, 89, '80-89'), (70, 79, '70-79'), 
                  (60, 69, '60-69'), (0, 59, '0-59')]
        for low, high, label in ranges:
            count = sum(1 for s in score_values if low <= s <= high)
            prompt += f"- {label}分：{count}人\n"
        
        prompt += "\n请生成完整的试卷分析报告，包括整体评价、问题分析和教学建议。"
        
        # 尝试调用AI API
        try:
            analysis_content = await call_qwen_api(prompt)
            if not analysis_content or "API调用失败" in analysis_content or "不可用" in analysis_content:
                # 使用本地分析
                analysis_content = generate_local_analysis(stats, scores)
        except Exception:
            # 使用本地分析
            analysis_content = generate_local_analysis(stats, scores)
        
        # 保存分析结果
        cursor.execute("SELECT id FROM teachers WHERE user_id = %s", (current_user.id,))
        teacher = cursor.fetchone()
        teacher_id = teacher['id'] if teacher else None
        
        cursor.execute("""
            INSERT INTO exam_analysis 
            (exam_id, subject_id, class_id, teacher_id, analysis_content, 
             avg_score, max_score, min_score, pass_count, excellent_count, total_count, pass_rate, excellent_rate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                analysis_content = VALUES(analysis_content),
                avg_score = VALUES(avg_score),
                max_score = VALUES(max_score),
                min_score = VALUES(min_score),
                pass_count = VALUES(pass_count),
                excellent_count = VALUES(excellent_count),
                total_count = VALUES(total_count),
                pass_rate = VALUES(pass_rate),
                excellent_rate = VALUES(excellent_rate),
                updated_at = NOW()
        """, (
            request.exam_id, request.subject_id, request.class_id, teacher_id, analysis_content,
            stats['avg_score'], stats['max_score'], stats['min_score'],
            stats['pass_count'], stats['excellent_count'], stats['total_count'],
            stats['pass_rate'], stats['excellent_rate']
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "message": "分析生成成功",
            "analysis": analysis_content,
            "stats": stats
        }
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{exam_id}/{subject_id}")
async def get_analysis_history(
    exam_id: int,
    subject_id: int,
    class_id: Optional[int] = None,
    current_user: CurrentUser = Depends(require_teacher)
):
    """获取历史分析记录"""
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="数据库连接失败")
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        sql = """
            SELECT ea.*, t.name as teacher_name, c.name as class_name
            FROM exam_analysis ea
            LEFT JOIN teachers t ON ea.teacher_id = t.id
            LEFT JOIN classes c ON ea.class_id = c.id
            WHERE ea.exam_id = %s AND ea.subject_id = %s
        """
        params = [exam_id, subject_id]
        
        if class_id:
            sql += " AND (ea.class_id = %s OR ea.class_id IS NULL)"
            params.append(class_id)
        
        sql += " ORDER BY ea.created_at DESC"
        
        cursor.execute(sql, tuple(params))
        analyses = cursor.fetchall()
        
        # 格式化
        for a in analyses:
            for key in ['avg_score', 'max_score', 'min_score', 'pass_rate', 'excellent_rate']:
                if a.get(key):
                    a[key] = float(a[key])
            if a.get('created_at'):
                a['created_at'] = str(a['created_at'])
            if a.get('updated_at'):
                a['updated_at'] = str(a['updated_at'])
        
        cursor.close()
        conn.close()
        return {"data": analyses}
    except Error as e:
        if conn: conn.close()
        raise HTTPException(status_code=500, detail=str(e))
