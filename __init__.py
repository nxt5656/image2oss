"""Top-level package for image2oss."""

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY",
]

__author__ = """nxt5656"""
__email__ = "nxt5656@live.cn"
__version__ = "0.0.4"

from .src.image2oss.nodes import NODE_CLASS_MAPPINGS
from .src.image2oss.nodes import NODE_DISPLAY_NAME_MAPPINGS

WEB_DIRECTORY = "./web"
