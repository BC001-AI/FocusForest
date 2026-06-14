#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FocusForest - 专注森林
启动器（编译版本）
"""

import sys
import os
from pathlib import Path

project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

compiled_dir = project_root / 'build' / 'compiled'
if str(compiled_dir) not in sys.path:
    sys.path.insert(0, str(compiled_dir))

from ui.app import FocusApp


if __name__ == "__main__":
    app = FocusApp()
    app.mainloop()
