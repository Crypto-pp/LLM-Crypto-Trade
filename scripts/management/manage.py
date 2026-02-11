#!/usr/bin/env python3
"""
系统管理CLI工具
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd: str):
    """运行shell命令"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode


def status():
    """查看服务状态"""
    print("=== 服务状态 ===")
    return run_command("docker-compose -f config/docker-compose.yml ps")


def start(service: str = None):
    """启动服务"""
    if service:
        print(f"启动服务: {service}")
        return run_command(f"docker-compose -f config/docker-compose.yml start {service}")
    else:
        print("启动所有服务")
        return run_command("./scripts/deployment/start_services.sh")


def stop(service: str = None):
    """停止服务"""
    if service:
        print(f"停止服务: {service}")
        return run_command(f"docker-compose -f config/docker-compose.yml stop {service}")
    else:
        print("停止所有服务")
        return run_command("./scripts/deployment/stop_services.sh")


def logs(service: str = None, follow: bool = False):
    """查看日志"""
    cmd = "docker-compose -f config/docker-compose.yml logs"
    if follow:
        cmd += " -f"
    if service:
        cmd += f" {service}"
    return run_command(cmd)


def health():
    """健康检查"""
    print("=== 健康检查 ===")
    return run_command("curl -s http://localhost:8000/health | python -m json.tool")


def main():
    parser = argparse.ArgumentParser(description="Crypto-Trade 系统管理工具")
    subparsers = parser.add_subparsers(dest='command', help='命令')

    # status命令
    subparsers.add_parser('status', help='查看服务状态')

    # start命令
    start_parser = subparsers.add_parser('start', help='启动服务')
    start_parser.add_argument('service', nargs='?', help='服务名称（可选）')

    # stop命令
    stop_parser = subparsers.add_parser('stop', help='停止服务')
    stop_parser.add_argument('service', nargs='?', help='服务名称（可选）')

    # logs命令
    logs_parser = subparsers.add_parser('logs', help='查看日志')
    logs_parser.add_argument('service', nargs='?', help='服务名称（可选）')
    logs_parser.add_argument('-f', '--follow', action='store_true', help='持续输出日志')

    # health命令
    subparsers.add_parser('health', help='健康检查')

    args = parser.parse_args()

    if args.command == 'status':
        sys.exit(status())
    elif args.command == 'start':
        sys.exit(start(args.service))
    elif args.command == 'stop':
        sys.exit(stop(args.service))
    elif args.command == 'logs':
        sys.exit(logs(args.service, args.follow))
    elif args.command == 'health':
        sys.exit(health())
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
