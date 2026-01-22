"""
FastAPI 服务接口
- 提供 HTTP API 用于书法批改
"""

import io
import cv2
import numpy as np
import yaml
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# 延迟导入，避免循环依赖
grader = None


def get_grader():
    """获取或初始化 grader 实例"""
    global grader
    if grader is None:
        from src.api.grader import CalligraphyGrader
        config_path = Path(__file__).parent.parent.parent / "configs" / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        grader = CalligraphyGrader(config)
    return grader


# 创建 FastAPI 应用
app = FastAPI(
    title="AI 硬笔书法批改系统",
    description="基于计算机视觉的硬笔书法自动批改 API",
    version="1.0.0"
)


class GradeResponse(BaseModel):
    """批改响应模型"""
    overall_score: Optional[float] = None
    char_count: Optional[int] = None
    chars: Optional[list] = None
    error: Optional[str] = None


class CharGradeRequest(BaseModel):
    """单字批改请求"""
    char: str


@app.get("/")
async def root():
    """API 根路径"""
    return {
        "message": "AI 硬笔书法批改系统 API",
        "version": "1.0.0",
        "endpoints": {
            "POST /grade": "批改整张书法图片",
            "POST /grade/char": "批改单个字（需指定汉字）",
            "GET /templates/{char}": "获取标准字模板信息"
        }
    }


@app.post("/grade", response_model=GradeResponse)
async def grade_image(file: UploadFile = File(...)):
    """
    批改整张书法图片
    
    - **file**: 上传的图片文件 (支持 jpg, png 等常见格式)
    
    返回每个检测到的汉字的评分和反馈
    """
    # 检查文件类型
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件")
    
    try:
        # 读取图片数据
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="无法解析图片")
        
        # 保存临时文件用于处理
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            cv2.imwrite(tmp.name, image)
            tmp_path = tmp.name
        
        # 批改
        result = get_grader().grade(tmp_path)
        
        # 清理临时文件
        Path(tmp_path).unlink(missing_ok=True)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@app.post("/grade/char")
async def grade_single_char(
    file: UploadFile = File(...),
    char: str = None
):
    """
    批改单个字
    
    - **file**: 单字图片
    - **char**: 对应的汉字字符（用于匹配标准模板）
    """
    if not char:
        raise HTTPException(status_code=400, detail="请指定汉字字符")
    
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片文件")
    
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="无法解析图片")
        
        result = get_grader().grade_single_char(image, char)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@app.get("/templates/{char}")
async def get_template_info(char: str):
    """
    获取标准字模板信息
    
    - **char**: 汉字字符
    """
    g = get_grader()
    template = g.scorer.load_template(char)
    
    if template is None:
        raise HTTPException(status_code=404, detail=f"未找到字符 '{char}' 的标准模板")
    
    # 返回模板的基本信息（不返回图像数据）
    features = g._get_template_features(char)
    
    return {
        "char": char,
        "has_template": True,
        "features": {
            "center_of_mass": features.get('center_of_mass'),
            "ratios": features.get('ratios'),
            "stroke_count": features.get('stroke_features', {}).get('stroke_count')
        }
    }


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"}
