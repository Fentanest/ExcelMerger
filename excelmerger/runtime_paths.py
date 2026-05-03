import os
import sys


def resource_path(relative_path):
    """Return an absolute path that works in dev and PyInstaller builds."""
    base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base_path, relative_path)


def poi_jar_dir():
    return resource_path(os.path.join("lib", "poi"))


def bundled_java_home():
    java_home = resource_path(os.path.join("lib", "jre"))
    if os.path.isdir(java_home):
        return java_home
    return ""
