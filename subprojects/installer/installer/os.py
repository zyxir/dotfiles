"""Utility for detecting the operating system."""

import os
import platform

IS_WINDOWS = platform.system() == "Windows"

IS_LINUX = platform.system() == "Linux"

IS_WSL = IS_LINUX and os.path.exists("/proc/sys/fs/binfmt_misc/WSLInterop")
