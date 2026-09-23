#!/usr/bin/env python3
"""
LeadForge — Example usage scripts
"""

import subprocess
import os
import sys

# 确保从项目根目录运行
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

def run_basic():
    """基础用法"""
    print("=" * 60)
    print("Example 1: Basic usage")
    print("=" * 60)
    cmd = [sys.executable, "leadforge.py", "workflow automation", "--max-leads", "3"]
    result = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, "PYTHONPATH": ROOT})
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

def run_with_output():
    """带输出文件"""
    print("=" * 60)
    print("Example 2: Save results to JSON")
    print("=" * 60)
    cmd = [sys.executable, "leadforge.py", "AI coding assistant", "--max-leads", "3", "--output", "results.json"]
    result = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, "PYTHONPATH": ROOT})
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

def run_report():
    """生成报告"""
    print("=" * 60)
    print("Example 3: Generate HTML report")
    print("=" * 60)
    if os.path.exists("results.json"):
        cmd = [sys.executable, "leadforge_report.py", "results.json", "--format", "html", "--output", "report.html"]
        result = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, "PYTHONPATH": ROOT})
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        print("\nOpen report.html in browser to view")

def run_console_report():
    """控制台报告"""
    print("=" * 60)
    print("Example 4: Console report")
    print("=" * 60)
    if os.path.exists("results.json"):
        cmd = [sys.executable, "leadforge_report.py", "results.json", "--format", "console"]
        result = subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, "PYTHONPATH": ROOT})
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

if __name__ == "__main__":
    if not os.environ.get("NVIDIA_API_KEY"):
        print("❌ NVIDIA_API_KEY not set. Get free key at https://build.nvidia.com")
        sys.exit(1)

    run_basic()
    run_with_output()
    run_report()
    run_console_report()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)