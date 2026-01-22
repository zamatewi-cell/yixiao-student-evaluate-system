# -*- coding: utf-8 -*-
"""
AI Scoring Module using Qwen Vision API
"""

import os
import base64
import json
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from openai import OpenAI


class QwenAIScorer:
    """AI Scorer using Qwen Vision API"""
    
    def __init__(self, api_key: str = None, config: dict = None):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.config = config or {}
        
        if not self.api_key:
            raise ValueError("API key required")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        self.model = "qwen-vl-plus"
        
        scoring_config = self.config.get("scoring", {})
        weights = scoring_config.get("weights", {})
        self.weight_center = weights.get("center_of_mass", 0.25)
        self.weight_stroke = weights.get("stroke_accuracy", 0.40)
        self.weight_structure = weights.get("structure", 0.35)
    
    def _encode_image_to_base64(self, image: np.ndarray) -> str:
        _, buffer = cv2.imencode(".png", image)
        return base64.b64encode(buffer).decode("utf-8")
    
    def _encode_image_file_to_base64(self, image_path: str) -> str:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def score_single_char(self, student_image: np.ndarray, template_image: np.ndarray,
                          char: str) -> Dict:
        student_b64 = self._encode_image_to_base64(student_image)
        template_b64 = self._encode_image_to_base64(template_image)
        
        comparison = np.hstack([student_image, template_image])
        comparison_b64 = self._encode_image_to_base64(comparison)
        
        prompt = self._build_scoring_prompt(char)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{comparison_b64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            result_text = response.choices[0].message.content.strip()
            result = self._parse_json_response(result_text)
            
            if result:
                return result
            else:
                return self._create_fallback_result(char)
                
        except Exception as e:
            print(f"AI scoring error: {e}")
            return self._create_fallback_result(char, error=str(e))
    
    def _build_scoring_prompt(self, char: str) -> str:
        return f"""You are a professional calligraphy teacher. Please score the handwritten character "{char}".

Left side is student writing, right side is standard template.

Score these 3 dimensions (0-100 each):
1. Center of mass (25% weight): Is the center position correct? Are proportions balanced?
2. Stroke accuracy (40% weight): Are strokes straight/curved properly? Are lengths/angles accurate?
3. Structure (35% weight): Are stroke relationships and spacing correct?

Return JSON format:
{{
    "char": "{char}",
    "scores": {{
        "center_of_mass": <0-100>,
        "stroke_accuracy": <0-100>,
        "structure": <0-100>
    }},
    "total_score": <weighted total, 1 decimal>,
    "grade": "<Excellent/Good/Medium/Pass/NeedImprovement>",
    "feedback": {{
        "strengths": ["<good point 1>", "<good point 2>"],
        "improvements": ["<improvement 1>", "<improvement 2>"],
        "suggestions": ["<suggestion 1>", "<suggestion 2>"]
    }},
    "overall_comment": "<one sentence summary>"
}}

Only return JSON, no other text."""
    
    def score_image(self, image_path: str) -> Dict:
        image = cv2.imread(image_path)
        if image is None:
            return {"error": f"Cannot read image: {image_path}"}
        
        image_b64 = self._encode_image_file_to_base64(image_path)
        
        prompt = """You are a professional calligraphy teacher. Please evaluate this calligraphy work.

Evaluate these dimensions:
1. Overall layout: Are characters evenly sized? Is spacing appropriate?
2. Stroke quality: Are strokes smooth and strong?
3. Structure: Is each character properly structured?
4. Aesthetics: Overall visual appeal

Return JSON format:
{
    "overall_score": <0-100>,
    "grade": "<Excellent/Good/Medium/Pass/NeedImprovement>",
    "dimensions": {
        "layout": <0-100>,
        "stroke_quality": <0-100>,
        "structure": <0-100>,
        "aesthetics": <0-100>
    },
    "detected_chars": ["<detected characters>"],
    "char_count": <number>,
    "feedback": {
        "strengths": ["<strength 1>", "<strength 2>"],
        "improvements": ["<improvement 1>", "<improvement 2>"],
        "suggestions": ["<suggestion 1>", "<suggestion 2>"]
    },
    "overall_comment": "<one sentence summary>"
}

Only return JSON."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_b64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                max_tokens=1500
            )
            
            result_text = response.choices[0].message.content.strip()
            result = self._parse_json_response(result_text)
            
            if result:
                return result
            else:
                return {"error": "Failed to parse AI response", "raw_response": result_text}
                
        except Exception as e:
            return {"error": f"AI scoring failed: {str(e)}"}
    
    def _parse_json_response(self, text: str) -> Optional[Dict]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                try:
                    return json.loads(text[start:end].strip())
                except:
                    pass
        
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except:
                pass
        
        return None
    
    def _create_fallback_result(self, char: str, error: str = None) -> Dict:
        return {
            "char": char,
            "scores": {
                "center_of_mass": 70,
                "stroke_accuracy": 70,
                "structure": 70
            },
            "total_score": 70.0,
            "grade": "Medium",
            "feedback": {
                "strengths": ["Keep practicing"],
                "improvements": ["More practice needed"],
                "suggestions": ["Practice with copybook"]
            },
            "overall_comment": "AI scoring temporarily unavailable" if error else "Keep going!",
            "error": error
        }
    
    def compare_with_template(self, student_image: np.ndarray, template_image: np.ndarray,
                               char: str) -> Dict:
        student_b64 = self._encode_image_to_base64(student_image)
        template_b64 = self._encode_image_to_base64(template_image)
        
        prompt = f"""As a professional calligraphy teacher, analyze the differences between student writing and template for character "{char}".

First image is student writing, second is standard template.

Analyze:
1. Stroke comparison: Which strokes are good, which need improvement
2. Structure comparison: How does overall structure differ
3. Center comparison: Is the center position correct
4. Specific suggestions: Detailed improvement methods

Return JSON:
{{
    "char": "{char}",
    "stroke_analysis": [
        {{"stroke_name": "<name>", "status": "<good/medium/needs_improvement>", "detail": "<description>"}}
    ],
    "structure_diff": "<structure difference description>",
    "center_diff": "<center difference description>",
    "detailed_suggestions": ["<suggestion 1>", "<suggestion 2>"],
    "practice_tips": ["<tip 1>", "<tip 2>"]
}}

Only return JSON."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{student_b64}"}
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{template_b64}"}
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                max_tokens=1500
            )
            
            result_text = response.choices[0].message.content.strip()
            return self._parse_json_response(result_text) or {"raw_response": result_text}
            
        except Exception as e:
            return {"error": str(e)}


class HybridScorer:
    """Hybrid Scorer combining algorithmic + AI scoring"""
    
    def __init__(self, config: dict, api_key: str = None):
        self.config = config
        
        from src.scoring.scorer import CalligraphyScorer
        from src.extraction.stroke_extractor import StrokeExtractor
        
        self.algo_scorer = CalligraphyScorer(config)
        self.extractor = StrokeExtractor(config)
        
        self.ai_scorer = None
        if api_key:
            try:
                self.ai_scorer = QwenAIScorer(api_key=api_key, config=config)
                print("AI Scorer initialized")
            except Exception as e:
                print(f"AI Scorer init failed: {e}")
        
        self.ai_weight = 0.6
    
    def score_char(self, student_image: np.ndarray, template_image: np.ndarray,
                   char: str, use_ai: bool = True) -> Dict:
        student_features = self.extractor.extract_all_features(student_image)
        template_features = self.extractor.extract_all_features(template_image)
        algo_result = self.algo_scorer.score_char(student_features, template_features)
        
        if not use_ai or self.ai_scorer is None:
            return algo_result
        
        try:
            ai_result = self.ai_scorer.score_single_char(student_image, template_image, char)
            
            if "error" in ai_result:
                return algo_result
            
            blended_result = self._blend_scores(algo_result, ai_result)
            return blended_result
            
        except Exception as e:
            print(f"AI scoring failed, using algorithmic only: {e}")
            return algo_result
    
    def _blend_scores(self, algo_result: Dict, ai_result: Dict) -> Dict:
        algo_weight = 1 - self.ai_weight
        
        algo_dims = algo_result.get("dimensions", {})
        ai_scores = ai_result.get("scores", {})
        
        blended_dims = {
            "center_of_mass": (
                algo_dims.get("center_of_mass", 70) * algo_weight +
                ai_scores.get("center_of_mass", 70) * self.ai_weight
            ),
            "stroke_accuracy": (
                algo_dims.get("stroke_accuracy", 70) * algo_weight +
                ai_scores.get("stroke_accuracy", 70) * self.ai_weight
            ),
            "structure": (
                algo_dims.get("structure", 70) * algo_weight +
                ai_scores.get("structure", 70) * self.ai_weight
            )
        }
        
        total_score = (
            blended_dims["center_of_mass"] * 0.25 +
            blended_dims["stroke_accuracy"] * 0.40 +
            blended_dims["structure"] * 0.35
        )
        
        if total_score >= 90:
            grade = "Excellent"
        elif total_score >= 75:
            grade = "Good"
        elif total_score >= 60:
            grade = "Medium"
        elif total_score >= 45:
            grade = "Pass"
        else:
            grade = "NeedImprovement"
        
        return {
            "total_score": round(total_score, 1),
            "grade": grade,
            "dimensions": {k: round(v, 1) for k, v in blended_dims.items()},
            "algo_score": algo_result.get("total_score"),
            "ai_score": ai_result.get("total_score"),
            "feedback": ai_result.get("feedback", {}),
            "overall_comment": ai_result.get("overall_comment", ""),
            "scoring_method": "hybrid"
        }
