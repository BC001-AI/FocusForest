# -*- coding: utf-8 -*-
"""
MessageServer 统一编译脚本
支持编译 MessageServer 核心模块为 pyd
优化版本：不修改原始文件，使用独立的编译目录
"""
import os
import re
import sys
import shutil
from pathlib import Path
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
from Cython.Build import cythonize
import numpy as np

# ============================================
# 配置
# ============================================

base_dir = Path(__file__).parent.parent
print(f"项目根目录: {base_dir}")

# 编译输出目录
build_dir = base_dir / 'message_server' / 'build' / 'compiled'
build_dir.mkdir(parents=True, exist_ok=True)

# MessageServer 核心模块配置
MESSAGE_SERVER_MODULES = [
    {
        'name': 'message_server',
        'source': 'message_server/message_server.py',
        'dest': 'message_server.py'
    }
]

# ============================================
# 自定义构建类
# ============================================

class CustomBuildExt(build_ext):
    """自定义构建类，简化文件名"""
    def get_ext_filename(self, ext_name):
        filename = super().get_ext_filename(ext_name)
        # 去平台标识（适用于 Windows）
        # 匹配格式：.cp314-win_amd64.pyd 或 .cpython-314-win_amd64.pyd
        filename = re.sub(
            r'\.(cp|cpython)-?\d*-?(win_amd64|mingw_x86_64)\.pyd$',
            '.pyd',
            filename
        )
        # 保留路径层次（如 message_server.pyd）
        # 使用修改后的filename，确保去除了平台标识
        return filename

# ============================================
# 编译 MessageServer 核心模块
# ============================================

def compile_message_server_modules():
    """编译 MessageServer 核心模块"""
    print("=" * 60)
    print("编译 MessageServer 核心模块")
    print("=" * 60)
    
    # 第一步：复制文件到编译目录
    print("\n第一步：复制核心模块文件到编译目录")
    print("-" * 60)
    
    for module in MESSAGE_SERVER_MODULES:
        source_file = base_dir / module['source']
        dest_file = build_dir / module['dest']
        
        if source_file.exists():
            # 复制文件（不修改原始文件）
            shutil.copy2(source_file, dest_file)
            print(f"已复制: {module['source']} -> {module['dest']}")
        else:
            print(f"警告: 文件不存在 {module['source']}")
    
    # 第二步：创建启动器
    print("\n第二步：创建启动器")
    print("-" * 60)
    
    launcher_content = '''#!/usr/bin/env python
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

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 添加编译目录到Python路径
compiled_dir = project_root / 'message_server' / 'build' / 'compiled'
if str(compiled_dir) not in sys.path:
    sys.path.insert(0, str(compiled_dir))

def start_message_server():
    """启动消息服务器"""
    print("=" * 60)
    print("MessageServer - 消息服务器（编译版本）")
    print("=" * 60)
    print()
    print("正在启动消息服务器...")
    print(f"工作目录: {project_root}")
    print()
    
    # 导入message_server模块
    try:
        from message_server import app
    except ImportError as e:
        print(f"错误: 无法导入message_server模块: {e}")
        print("请确保已正确编译pyd模块")
        sys.exit(1)
    
    # 获取配置
    host = '0.0.0.0'
    port = 1002
    
    # 启动服务器
    print(f"消息服务器地址: http://{host}:{port}")
    print(f"按 Ctrl+C 停止服务器")
    print("=" * 60)
    print()
    
    # 自动打开管理界面
    def open_admin_page():
        """延迟打开管理界面"""
        time.sleep(2)  # 等待服务器启动
        print("准备打开管理界面...")
        
        # 获取message_admin.html的路径
        if getattr(sys, 'frozen', False):
            # 打包后的环境 - 在_internal目录下查找
            admin_html_path = Path(sys.executable).parent / '_internal' / 'message_admin.html'
        else:
            # 开发环境
            admin_html_path = Path(__file__).parent / 'message_server' / 'message_admin.html'
        
        print(f"管理界面路径: {admin_html_path}")
        print(f"文件是否存在: {admin_html_path.exists()}")
        
        if admin_html_path.exists():
            print(f"正在打开管理界面...")
            # 使用绝对路径
            admin_path = admin_html_path.resolve()
            print(f"绝对路径: {admin_path}")
            
            # Windows系统使用file://协议
            if os.name == 'nt':
                file_url = f'file:///{admin_path.as_posix()}'
                print(f"浏览器URL: {file_url}")
                webbrowser.open(file_url)
            else:
                webbrowser.open(f'file://{admin_path.as_posix()}')
        else:
            print(f"警告: 找不到管理界面文件: {admin_html_path}")
    
    # 在后台线程中打开管理界面
    print("启动后台线程打开管理界面...")
    open_thread = threading.Thread(target=open_admin_page)
    open_thread.daemon = True
    open_thread.start()
    
    # 运行Flask应用
    try:
        app.run(host=host, port=port, debug=False)
    except KeyboardInterrupt:
        print("\\n服务器已停止")
    except Exception as server_error:
        print(f"\\n服务器启动失败: {server_error}")
        sys.exit(1)

if __name__ == '__main__':
    start_message_server()
'''
    
    launcher_file = base_dir / 'message_server' / 'run_compiled.py'
    with open(launcher_file, 'w', encoding='utf-8') as f:
        f.write(launcher_content)
    
    print(f"已创建启动器: message_server/run_compiled.py")
    
    # 第三步：编译pyd模块
    print("\n第三步：编译pyd模块")
    print("-" * 60)
    
    # 获取numpy头文件路径
    numpy_include = np.get_include()
    
    # 构建扩展模块列表
    extensions = []
    
    for module in MESSAGE_SERVER_MODULES:
        module_file = build_dir / module['dest']
        
        if module_file.exists():
            print(f"准备编译: {module['name']}")
            
            ext = Extension(
                module['name'],
                sources=[str(module_file)],
                include_dirs=[numpy_include],
            )
            extensions.append(ext)
        else:
            print(f"警告: 模块文件不存在 {module_file}")
    
    if not extensions:
        print("错误: 没有找到要编译的 MessageServer 模块")
        return False
    
    print(f"\n准备编译 {len(extensions)} 个 MessageServer 模块...")
    
    # 编译设置
    setup_args = {
        'name': 'MessageServerCore',
        'version': '1.0.0',
        'description': 'MessageServer核心模块（编译版）',
        'cmdclass': {'build_ext': CustomBuildExt},
        'ext_modules': cythonize(
            extensions,
            compiler_directives={
                'language_level': 3,
                'embedsignature': True,
            },
            annotate=True,
        )
    }
    
    # 执行编译
    try:
        # 切换到编译目录进行编译
        original_dir = Path.cwd()
        os.chdir(str(build_dir))
        sys.argv = ['setup.py', 'build_ext', '--inplace']
        setup(**setup_args)
        os.chdir(str(original_dir))
        
        print("\n" + "=" * 60)
        print("MessageServer 核心模块编译完成！")
        print("=" * 60)
        
        # 列出生成的pyd文件
        pyd_files = list(build_dir.glob('*.pyd'))
        if pyd_files:
            print(f"\n生成的pyd文件:")
            for pyd_file in pyd_files:
                print(f"  - {pyd_file.name}")
        
        return True
        
    except Exception as compile_error:
        print(f"\n编译失败: {compile_error}")
        import traceback
        traceback.print_exc()
        return False

# ============================================
# 主函数
# ============================================

def main():
    """主函数"""
    print("\n")
    print("MessageServer 统一编译脚本（优化版）")
    print("=" * 60)
    print("特点：不修改原始文件，使用独立编译目录")
    print("=" * 60)
    
    print("\n开始编译 MessageServer 核心模块...")
    
    success = compile_message_server_modules()
    
    print("\n" + "=" * 60)
    if success:
        print("编译完成！")
        print("\n使用方法:")
        print("  开发版本: python message_server/message_server.py")
        print("  编译版本: python message_server/run_compiled.py")
        print("\n下一步:")
        print("1. 检查生成的pyd文件")
        print("2. 运行打包脚本:")
        print("   python message_server/02_package_message_server.py")
    else:
        print("编译失败")
    print("=" * 60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断编译过程")
        sys.exit(1)
    except Exception as main_error:
        print(f"\n\n编译过程出错: {main_error}")
        import traceback
        traceback.print_exc()
        sys.exit(1)