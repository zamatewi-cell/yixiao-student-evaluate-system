"""
Test AI Scoring with Qwen Vision API
"""

import sys
import os
sys.path.insert(0, '.')

import cv2
import numpy as np
import yaml
from pathlib import Path

# API Key
API_KEY = "sk-64b7fb2c08b44369981491e4c65b03f6"


def test_ai_scorer_direct():
    """Test AI scorer directly"""
    print("\n" + "="*50)
    print("Test 1: Direct AI Scorer")
    print("="*50)
    
    from src.scoring.ai_scorer import QwenAIScorer
    from src.utils.font_renderer import FontRenderer
    
    try:
        # Initialize
        scorer = QwenAIScorer(api_key=API_KEY)
        print("[OK] AI Scorer initialized")
        
        # Get font renderer
        font_files = list(Path('data/templates').glob('*.ttf'))
        if not font_files:
            print("[FAIL] No font files found")
            return False
        
        renderer = FontRenderer(str(font_files[0]))
        
        # Render template
        test_char = chr(27704)  # yong (forever)
        template = renderer.render_char(test_char)
        print(f"[OK] Template rendered for '{test_char}'")
        
        # Create simulated student writing (slightly modified)
        student = template.copy()
        M = np.float32([[1, 0, 8], [0, 1, 5]])
        student = cv2.warpAffine(student, M, (256, 256))
        # Add some noise
        noise = np.random.randint(0, 30, student.shape, dtype=np.uint8)
        student = cv2.add(student, noise)
        
        print("Testing AI scoring...")
        result = scorer.score_single_char(student, template, test_char)
        
        if 'error' in result and result.get('error'):
            print(f"[WARN] AI scoring returned error: {result.get('error')}")
        else:
            print(f"[OK] AI Scoring result:")
            print(f"  Total Score: {result.get('total_score')}")
            print(f"  Grade: {result.get('grade')}")
            print(f"  Scores: {result.get('scores')}")
            print(f"  Comment: {result.get('overall_comment')}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hybrid_scorer():
    """Test hybrid scorer (AI + algorithmic)"""
    print("\n" + "="*50)
    print("Test 2: Hybrid Scorer")
    print("="*50)
    
    from src.scoring.ai_scorer import HybridScorer
    from src.utils.font_renderer import FontRenderer
    
    # Load config
    config_path = Path('configs/config.yaml')
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    else:
        config = {
            'paths': {'templates': 'data/templates'},
            'scoring': {'weights': {'center_of_mass': 0.25, 'stroke_accuracy': 0.40, 'structure': 0.35}},
            'extraction': {}
        }
    
    try:
        # Initialize hybrid scorer
        scorer = HybridScorer(config=config, api_key=API_KEY)
        print("[OK] Hybrid Scorer initialized")
        
        # Get template and student
        font_files = list(Path('data/templates').glob('*.ttf'))
        renderer = FontRenderer(str(font_files[0]))
        
        test_char = chr(27704)
        template = renderer.render_char(test_char)
        
        # Create student writing
        student = template.copy()
        M = np.float32([[1, 0, 5], [0, 1, 3]])
        student = cv2.warpAffine(student, M, (256, 256))
        
        print("Testing hybrid scoring...")
        result = scorer.score_char(student, template, test_char, use_ai=True)
        
        print(f"[OK] Hybrid Scoring result:")
        print(f"  Total Score: {result.get('total_score')}")
        print(f"  Grade: {result.get('grade')}")
        print(f"  Algo Score: {result.get('algo_score')}")
        print(f"  AI Score: {result.get('ai_score')}")
        print(f"  Dimensions: {result.get('dimensions')}")
        print(f"  Method: {result.get('scoring_method')}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_grader_with_ai():
    """Test CalligraphyGrader with AI"""
    print("\n" + "="*50)
    print("Test 3: CalligraphyGrader with AI")
    print("="*50)
    
    from src.api.grader import CalligraphyGrader
    from src.utils.font_renderer import FontRenderer
    
    # Load config
    config_path = Path('configs/config.yaml')
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    else:
        config = {
            'paths': {'templates': 'data/templates'},
            'scoring': {'weights': {'center_of_mass': 0.25, 'stroke_accuracy': 0.40, 'structure': 0.35}},
            'extraction': {},
            'preprocess': {'target_size': [256, 256]}
        }
    
    try:
        # Initialize grader with AI
        grader = CalligraphyGrader(config=config, api_key=API_KEY, use_ai=True)
        print("[OK] Grader with AI initialized")
        
        # Create test character
        font_files = list(Path('data/templates').glob('*.ttf'))
        renderer = FontRenderer(str(font_files[0]))
        
        test_char = chr(27704)
        template = renderer.render_char(test_char)
        
        # Create student writing
        student = template.copy()
        M = np.float32([[1, 0, 5], [0, 1, 3]])
        student = cv2.warpAffine(student, M, (256, 256))
        
        print("Testing single char grading with AI...")
        result = grader.grade_single_char_with_ai(student, test_char)
        
        print(f"[OK] Result:")
        print(f"  Score: {result.get('score')}")
        print(f"  Grade: {result.get('grade')}")
        print(f"  Method: {result.get('scoring_method')}")
        if result.get('overall_comment'):
            print(f"  Comment: {result.get('overall_comment')}")
        
        # Save comparison
        output_dir = Path('outputs/test_ai')
        output_dir.mkdir(parents=True, exist_ok=True)
        comparison = np.hstack([student, template])
        cv2.imwrite(str(output_dir / 'ai_test_comparison.png'), comparison)
        print(f"[OK] Comparison saved to {output_dir}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_gnt_sample():
    """Test AI scoring with real GNT sample"""
    print("\n" + "="*50)
    print("Test 4: AI Scoring with GNT Sample")
    print("="*50)
    
    from src.api.grader import CalligraphyGrader
    from src.utils.dataset_parser import GNTParser, preprocess_handwriting_image
    
    # Load config
    config_path = Path('configs/config.yaml')
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    else:
        config = {
            'paths': {'templates': 'data/templates'},
            'scoring': {'weights': {'center_of_mass': 0.25, 'stroke_accuracy': 0.40, 'structure': 0.35}},
            'extraction': {},
            'preprocess': {'target_size': [256, 256]}
        }
    
    try:
        # Initialize grader
        grader = CalligraphyGrader(config=config, api_key=API_KEY, use_ai=True)
        
        # Get GNT sample
        gnt_dir = Path('data/datasets/CASIA-HWDB/Gnt1.0Test')
        gnt_files = list(gnt_dir.glob('*.gnt'))
        
        if not gnt_files:
            print("[SKIP] No GNT files found")
            return True
        
        parser = GNTParser(str(gnt_files[0]))
        samples = parser.parse_to_list(max_samples=30)
        
        # Find a common character
        test_sample = None
        for char, img in samples:
            # Check if we have template for this char
            template = grader._get_template_image(char)
            if template is not None:
                test_sample = (char, img)
                break
        
        if test_sample is None:
            print("[SKIP] No matching sample found")
            return True
        
        char, student_img = test_sample
        print(f"Testing with char: {repr(char)}")
        
        # Preprocess
        processed = preprocess_handwriting_image(student_img, (256, 256))
        
        print("Running AI scoring...")
        result = grader.grade_single_char_with_ai(processed, char)
        
        print(f"[OK] Result:")
        print(f"  Char: {char}")
        print(f"  Score: {result.get('score')}")
        print(f"  Grade: {result.get('grade')}")
        print(f"  Method: {result.get('scoring_method')}")
        
        # Save
        output_dir = Path('outputs/test_ai')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        template = grader._get_template_image(char)
        if template is not None:
            comparison = np.hstack([processed, template])
            cv2.imwrite(str(output_dir / f'gnt_test_{ord(char)}.png'), comparison)
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*60)
    print("  AI Scoring Test Suite")
    print("="*60)
    
    results = {}
    
    results['Direct AI Scorer'] = test_ai_scorer_direct()
    results['Hybrid Scorer'] = test_hybrid_scorer()
    results['Grader with AI'] = test_grader_with_ai()
    results['GNT Sample Test'] = test_with_gnt_sample()
    
    # Summary
    print("\n" + "="*60)
    print("  Test Results Summary")
    print("="*60)
    
    passed = sum(1 for r in results.values() if r)
    failed = len(results) - passed
    
    for name, result in results.items():
        status = "[OK] PASS" if result else "[FAIL]"
        print(f"  {name}: {status}")
    
    print("-" * 60)
    print(f"  Total: {passed} passed, {failed} failed")
    print("="*60)


if __name__ == "__main__":
    main()
