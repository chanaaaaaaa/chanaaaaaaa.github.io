# -*- coding: utf-8 -*-
"""預設路徑與常數。"""
import os

DEFAULT_CODELIB = os.path.join(os.path.expanduser("~"), "Downloads", "git", "CodeLib", "code")
ALT_CODELIB = os.path.join(os.path.expanduser("~"), "Downloads", "CodeLib", "code")
DEFAULT_OUTPUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
