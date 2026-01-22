# -*- coding: utf-8 -*-
"""
One-Click Student Work Grading Script
Usage:
    python grade_all.py           # Algorithmic scoring only
    python grade_all.py --ai      # With AI scoring (hybrid)
    python grade_all.py --help    # Show help
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np
import yaml
from pathlib import Path
from datetime import datetime
import argparse


def print_banner():
    print("\n" + "=" * 70)
    print("       AI Calligraphy Grading System - One-Click Test")
    print("       AI Hard-Pen Calligraphy Grading System")
    print("=" * 70)


def load_config():
    """Load configuration file"""
    config_path = Path('configs/config.yaml')
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    else:
        return {
            'paths': {'templates': 'data/templates'},
            'scoring': {
                'weights': {'center_of_mass': 0.25, 'stroke_accuracy': 0.40, 'structure': 0.35}
            },
            'extraction': {},
            'preprocess': {'target_size': [256, 256]}
        }


def find_images(folder_path):
    """Find all image files in folder"""
    folder = Path(folder_path)
    if not folder.exists():
        return []
    
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', 
                  '*.JPG', '*.JPEG', '*.PNG', '*.BMP']
    images = []
    for ext in extensions:
        images.extend(folder.glob(ext))
    
    return sorted(set(images))


def grade_single_image(grader, image_path, use_ai=False, api_key=None):
    """Grade a single image and return results"""
    result = {
        'file': str(image_path),
        'success': False,
        'score': 0,
        'char_count': 0,
        'details': []
    }
    
    try:
        # Basic grading
        grade_result = grader.grade(str(image_path))
        
        if 'error' in grade_result:
            result['error'] = grade_result['error']
            return result
        
        result['success'] = True
        result['score'] = grade_result.get('overall_score', 0)
        result['char_count'] = grade_result.get('char_count', 0)
        result['chars'] = grade_result.get('chars', [])
        
        # AI analysis if enabled
        if use_ai and hasattr(grader, 'grade_with_ai'):
            try:
                ai_result = grader.grade_with_ai(str(image_path))
                result['ai_score'] = ai_result.get('overall_score')
                result['ai_comment'] = ai_result.get('overall_comment')
                result['ai_feedback'] = ai_result.get('feedback', {})
            except Exception as e:
                result['ai_error'] = str(e)
        
    except Exception as e:
        result['error'] = str(e)
    
    return result


def print_result(result, index, verbose=True):
    """Print grading result for one image"""
    filename = Path(result['file']).name
    
    print("\n" + "-" * 60)
    print("[{}] {}".format(index, filename))
    print("-" * 60)
    
    if not result['success']:
        print("  ERROR: {}".format(result.get('error', 'Unknown error')))
        return
    
    print("  Overall Score: {} points".format(result['score']))
    print("  Characters Detected: {}".format(result['char_count']))
    
    # Show AI results if available
    if 'ai_score' in result:
        print("\n  [AI Analysis]")
        print("  AI Score: {}".format(result.get('ai_score', 'N/A')))
        if result.get('ai_comment'):
            comment = result['ai_comment']
            if len(comment) > 60:
                comment = comment[:60] + "..."
            print("  Comment: {}".format(comment))
    
    # Show character details
    if verbose and result.get('chars'):
        print("\n  [Character Details]")
        chars = result['chars']
        
        # Show up to 10 characters
        display_chars = chars[:10]
        for char_info in display_chars:
            char = char_info.get('char', '?')
            score = char_info.get('score')
            grade = char_info.get('grade', '')
            
            if score is not None:
                print("    '{}': {:.1f} ({})".format(char, score, grade))
            else:
                status = char_info.get('feedback', 'No template')
                if isinstance(status, list):
                    status = status[0] if status else 'N/A'
                print("    '{}': {}".format(char, status))
        
        if len(chars) > 10:
            print("    ... and {} more characters".format(len(chars) - 10))


def print_summary(results):
    """Print summary of all grading results"""
    print("\n" + "=" * 70)
    print("                         SUMMARY")
    print("=" * 70)
    
    total = len(results)
    success = sum(1 for r in results if r['success'])
    failed = total - success
    
    print("\n  Total Images: {}".format(total))
    print("  Successfully Graded: {}".format(success))
    print("  Failed: {}".format(failed))
    
    if success > 0:
        scores = [r['score'] for r in results if r['success'] and r['score'] is not None]
        if scores:
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)
            
            print("\n  [Score Statistics]")
            print("  Average Score: {:.1f}".format(avg_score))
            print("  Highest Score: {:.1f}".format(max_score))
            print("  Lowest Score: {:.1f}".format(min_score))
        
        total_chars = sum(r['char_count'] for r in results if r['success'])
        print("  Total Characters Graded: {}".format(total_chars))
    
    # Score ranking
    if success > 1:
        print("\n  [Ranking by Score]")
        sorted_results = sorted(
            [r for r in results if r['success'] and r['score'] is not None],
            key=lambda x: x['score'],
            reverse=True
        )
        for i, r in enumerate(sorted_results, 1):
            filename = Path(r['file']).name
            print("    {}. {}: {:.1f}".format(i, filename, r['score']))


def save_results_to_file(results, output_path):
    """Save results to a text file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("AI Calligraphy Grading Results\n")
        f.write("Generated: {}\n".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        f.write("=" * 60 + "\n\n")
        
        for i, result in enumerate(results, 1):
            filename = Path(result['file']).name
            f.write("[{}] {}\n".format(i, filename))
            
            if result['success']:
                f.write("    Score: {}\n".format(result['score']))
                f.write("    Characters: {}\n".format(result['char_count']))
                
                if 'ai_score' in result:
                    f.write("    AI Score: {}\n".format(result.get('ai_score')))
                    if result.get('ai_comment'):
                        f.write("    AI Comment: {}\n".format(result['ai_comment']))
                
                if result.get('chars'):
                    f.write("    Details:\n")
                    for char_info in result['chars']:
                        char = char_info.get('char', '?')
                        score = char_info.get('score')
                        if score is not None:
                            f.write("      '{}': {:.1f}\n".format(char, score))
            else:
                f.write("    Error: {}\n".format(result.get('error', 'Unknown')))
            
            f.write("\n")
    
    print("\n  Results saved to: {}".format(output_path))


def main():
    parser = argparse.ArgumentParser(
        description="One-click grading for all student works",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--ai', action='store_true',
                        help='Enable AI scoring (hybrid mode)')
    parser.add_argument('--api-key', type=str,
                        default='sk-64b7fb2c08b44369981491e4c65b03f6',
                        help='Qwen API key for AI scoring')
    parser.add_argument('--folder', type=str,
                        default='data/student_samples/raw',
                        help='Folder containing student works')
    parser.add_argument('--save', action='store_true',
                        help='Save results to file')
    parser.add_argument('--brief', action='store_true',
                        help='Brief output (no character details)')
    
    args = parser.parse_args()
    
    print_banner()
    
    # Find images
    images = find_images(args.folder)
    
    if not images:
        print("\n  ERROR: No images found in '{}'".format(args.folder))
        print("  Please place image files (.jpg, .png, .bmp) in the folder.")
        return
    
    print("\n  Found {} image(s) in: {}".format(len(images), args.folder))
    print("  Mode: {}".format('AI Hybrid Scoring' if args.ai else 'Algorithmic Scoring'))
    
    # Load config and initialize grader
    print("\n  Initializing grader...")
    config = load_config()
    
    from src.api.grader import CalligraphyGrader
    
    if args.ai:
        grader = CalligraphyGrader(config=config, api_key=args.api_key, use_ai=True)
        print("  AI scoring enabled (Algorithm 40% + AI 60%)")
    else:
        grader = CalligraphyGrader(config=config, use_ai=False)
        print("  Using algorithmic scoring only")
    
    # Grade all images
    print("\n  Starting grading process...")
    results = []
    
    for i, image_path in enumerate(images, 1):
        print("\n  Processing [{}/{}]: {}".format(i, len(images), image_path.name), end="", flush=True)
        
        result = grade_single_image(grader, image_path, 
                                    use_ai=args.ai, 
                                    api_key=args.api_key if args.ai else None)
        results.append(result)
        
        if result['success']:
            print(" -> Score: {}".format(result['score']))
        else:
            print(" -> ERROR")
    
    # Print detailed results
    print("\n\n" + "=" * 70)
    print("                      DETAILED RESULTS")
    print("=" * 70)
    
    for i, result in enumerate(results, 1):
        print_result(result, i, verbose=not args.brief)
    
    # Print summary
    print_summary(results)
    
    # Save results if requested
    if args.save:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = Path('outputs') / 'grading_results_{}.txt'.format(timestamp)
        output_path.parent.mkdir(exist_ok=True)
        save_results_to_file(results, output_path)
    
    print("\n" + "=" * 70)
    print("                     GRADING COMPLETE")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
