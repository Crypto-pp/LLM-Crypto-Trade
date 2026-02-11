#!/usr/bin/env python3
"""
监控工具
查看系统指标、告警和性能
"""

import sys
import requests
import json
from typing import Dict, Any


def get_metrics() -> Dict[str, Any]:
    """获取Prometheus指标"""
    try:
        response = requests.get('http://localhost:9090/api/v1/query', params={
            'query': 'up'
        })
        return response.json()
    except Exception as e:
        print(f"错误: {e}")
        return {}


def get_alerts() -> Dict[str, Any]:
    """获取告警"""
    try:
        response = requests.get('http://localhost:9090/api/v1/alerts')
        return response.json()
    except Exception as e:
        print(f"错误: {e}")
        return {}


def get_performance() -> Dict[str, Any]:
    """获取性能指标"""
    try:
        response = requests.get('http://localhost:8000/health')
        return response.json()
    except Exception as e:
        print(f"错误: {e}")
        return {}


def main():
    if len(sys.argv) < 2:
        print("用法: python monitor.py [metrics|alerts|performance]")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'metrics':
        print("=== 系统指标 ===")
        data = get_metrics()
        print(json.dumps(data, indent=2))
    elif command == 'alerts':
        print("=== 告警信息 ===")
        data = get_alerts()
        print(json.dumps(data, indent=2))
    elif command == 'performance':
        print("=== 性能指标 ===")
        data = get_performance()
        print(json.dumps(data, indent=2))
    else:
        print(f"未知命令: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
