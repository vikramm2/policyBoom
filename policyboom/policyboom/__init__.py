"""
PolicyBoom - Enterprise Legal Risk Intelligence CLI

Analyze Terms of Service and Privacy Policies with multi-domain scanning.
"""

__version__ = "0.1.0"

from .scanner import scan

__all__ = ["scan", "__version__"]
