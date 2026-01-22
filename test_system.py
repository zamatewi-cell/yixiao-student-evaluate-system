import sys
sys.path.insert(0, '.')
from pathlib import Path
import cv2
import numpy as np

print("="*50)
print("Test 1: Font Rendering")
print("="*50)

font_files = list(Path('data/templates').glob('*.ttf'))
print(f'Found fonts: {len(font_files)}')

if font_files:
    from src.utils.font_renderer import FontRenderer
    renderer = FontRenderer(str(font_files[0]))
    print(f'Font loaded: {font_files[0].name}')
    
    # Test with Unicode code point
    test_char = chr(27704)  # yong (forever)
    img = renderer.render_char(test_char)
    print(f'Rendered char: shape={img.shape}, non-zero={np.sum(img > 0)}')
    
    output_dir = Path('outputs/test_renders')
    output_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_dir / 'test_yong.png'), img)
    print('[OK] Font rendering test passed')
else:
    print('[FAIL] No font files found')

print("\n" + "="*50)
print("Test 2: GNT Parsing")
print("="*50)

gnt_dir = Path('data/datasets/CASIA-HWDB/Gnt1.0Test')
gnt_files = list(gnt_dir.glob('*.gnt'))
print(f'Found GNT files: {len(gnt_files)}')

if gnt_files:
    from src.utils.dataset_parser import GNTParser
    parser = GNTParser(str(gnt_files[0]))
    samples = parser.parse_to_list(max_samples=5)
    print(f'Parsed {len(samples)} samples')
    
    output_dir = Path('outputs/test_gnt')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, (char, img) in enumerate(samples):
        print(f'  Sample {i}: char={repr(char)}, shape={img.shape}')
        cv2.imwrite(str(output_dir / f'sample_{i}.png'), img)
    
    print('[OK] GNT parsing test passed')
else:
    print('[FAIL] No GNT files found')

print("\n" + "="*50)
print("Test 3: Feature Extraction")
print("="*50)

from src.extraction.stroke_extractor import StrokeExtractor

config = {'extraction': {'min_stroke_length': 5}}
extractor = StrokeExtractor(config)

if font_files:
    from src.utils.font_renderer import FontRenderer
    renderer = FontRenderer(str(font_files[0]))
    test_img = renderer.render_char(chr(27704))
    
    features = extractor.extract_all_features(test_img)
    print(f'Center of mass: {features["center_of_mass"]}')
    print(f'Ratios: {features["ratios"]}')
    print(f'Stroke length: {features["stroke_features"]["total_length"]}')
    print('[OK] Feature extraction test passed')

print("\n" + "="*50)
print("Test 4: Scoring")
print("="*50)

import yaml
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

from src.scoring.scorer import CalligraphyScorer

scorer = CalligraphyScorer(config)
template = scorer.load_template(chr(27704))

if template is not None:
    print(f'Template loaded: shape={template.shape}')
    
    template_features = extractor.extract_all_features(template)
    
    # Simulate student with offset
    student_img = template.copy()
    M = np.float32([[1, 0, 5], [0, 1, 3]])
    student_img = cv2.warpAffine(student_img, M, (256, 256))
    student_features = extractor.extract_all_features(student_img)
    
    result = scorer.score_char(student_features, template_features)
    print(f'Score: {result["total_score"]} ({result["grade"]})')
    print(f'Dimensions: {result["dimensions"]}')
    print('[OK] Scoring test passed')
else:
    print('[FAIL] Template not loaded')

print("\n" + "="*50)
print("Test 5: Feedback Generation")
print("="*50)

from src.feedback.generator import FeedbackGenerator

generator = FeedbackGenerator()

mock_result = {
    'total_score': 78.5,
    'grade': 'Good',
    'dimensions': {'center_of_mass': 85, 'stroke_accuracy': 72, 'structure': 80},
    'student_features': {
        'center_of_mass': {'x': 0.52, 'y': 0.48},
        'ratios': {'upper_ratio': 0.55, 'left_ratio': 0.48},
        'stroke_features': {'total_length': 1200, 'stroke_count': 8}
    },
    'template_features': {
        'center_of_mass': {'x': 0.5, 'y': 0.5},
        'ratios': {'upper_ratio': 0.5, 'left_ratio': 0.5},
        'stroke_features': {'total_length': 1300, 'stroke_count': 8}
    }
}

feedback = generator.generate_feedback(mock_result)
text = generator.format_feedback_text(feedback)
print(text)
print('[OK] Feedback generation test passed')

print("\n" + "="*50)
print("Test 6: Full Pipeline")
print("="*50)

from src.utils.dataset_parser import preprocess_handwriting_image

if gnt_files:
    parser = GNTParser(str(gnt_files[0]))
    samples = parser.parse_to_list(max_samples=20)
    
    test_char, test_img = samples[0]
    print(f'Testing with char: {repr(test_char)}')
    
    # Preprocess
    processed = preprocess_handwriting_image(test_img, (256, 256))
    
    # Load template
    template = scorer.load_template(test_char)
    
    if template is not None:
        student_features = extractor.extract_all_features(processed)
        template_features = extractor.extract_all_features(template)
        
        result = scorer.score_char(student_features, template_features)
        feedback = generator.generate_feedback(result)
        
        print(f'Score: {result["total_score"]} ({result["grade"]})')
        
        output_dir = Path('outputs/test_pipeline')
        output_dir.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_dir / 'student.png'), processed)
        cv2.imwrite(str(output_dir / 'template.png'), template)
        comparison = np.hstack([processed, template])
        cv2.imwrite(str(output_dir / 'comparison.png'), comparison)
        
        print('[OK] Full pipeline test passed')
        print(f'Results saved to {output_dir}')
    else:
        print(f'[WARN] No template for {repr(test_char)}')

print("\n" + "="*50)
print("All tests completed!")
print("="*50)
