"""
AI 硬笔书法批改系统 - 主入口
"""

import argparse
import yaml
from pathlib import Path


def load_config(config_path: str = "configs/config.yaml") -> dict:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="AI 硬笔书法批改系统")
    parser.add_argument('--mode', type=str, choices=['grade', 'train', 'api'], 
                        default='grade', help='运行模式：grade(批改) / train(训练) / api(启动服务)')
    parser.add_argument('--image', type=str, help='待批改的图片路径')
    parser.add_argument('--config', type=str, default='configs/config.yaml', help='配置文件路径')
    
    args = parser.parse_args()
    config = load_config(args.config)
    
    if args.mode == 'grade':
        if not args.image:
            print("请指定待批改的图片路径：--image <path>")
            return
        # TODO: 调用批改流程
        print(f"正在批改图片: {args.image}")
        from src.api.grader import CalligraphyGrader
        grader = CalligraphyGrader(config)
        result = grader.grade(args.image)
        print(result)
        
    elif args.mode == 'train':
        # TODO: 调用训练流程
        print("训练模式 - 待实现")
        
    elif args.mode == 'api':
        # 启动 FastAPI 服务
        import uvicorn
        from src.api.server import app
        uvicorn.run(app, host=config['api']['host'], port=config['api']['port'])


if __name__ == "__main__":
    main()
