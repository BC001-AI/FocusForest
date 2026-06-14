#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MessageServer - 消息服务器
启动器（编译版本）
"""

import sys
import os
import webbrowser
import time
import threading
from pathlib import Path

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

compiled_dir = project_root / 'message_server' / 'build' / 'compiled'
if str(compiled_dir) not in sys.path:
    sys.path.insert(0, str(compiled_dir))

def start_message_server():
    print("=" * 60)
    print("MessageServer - 消息服务器（编译版本）")
    print("=" * 60)
    print()
    print("正在启动消息服务器...")
    print(f"工作目录: {project_root}")
    print()

    try:
        from message_server import app
    except ImportError as e:
        print(f"错误: 无法导入message_server模块: {e}")
        print("请确保已正确编译pyd模块")
        sys.exit(1)

    host = '0.0.0.0'
    port = 1002

    print(f"消息服务器地址: http://{host}:{port}")
    print(f"按 Ctrl+C 停止服务器")
    print("=" * 60)
    print()

    def open_admin_page():
        time.sleep(2)
        if getattr(sys, 'frozen', False):
            admin_html_path = Path(sys.executable).parent / '_internal' / 'message_admin.html'
        else:
            admin_html_path = Path(__file__).parent / 'message_admin.html'

        if admin_html_path.exists():
            admin_path = admin_html_path.resolve()
            if os.name == 'nt':
                file_url = f'file:///{admin_path.as_posix()}'
                webbrowser.open(file_url)
            else:
                webbrowser.open(f'file://{admin_path.as_posix()}')

    open_thread = threading.Thread(target=open_admin_page)
    open_thread.daemon = True
    open_thread.start()

    try:
        app.run(host=host, port=port, debug=False)
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as server_error:
        print(f"\n服务器启动失败: {server_error}")
        sys.exit(1)

if __name__ == '__main__':
    start_message_server()
