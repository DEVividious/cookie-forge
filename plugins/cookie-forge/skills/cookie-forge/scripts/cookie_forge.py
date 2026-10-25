#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "shapely>=2.0", "opencv-python-headless", "manifold3d>=2.5",
#                 "matplotlib", "trimesh", "pymupdf", "pillow"]
# ///
"""Command-line entry point of cookie-forge (`uv run cookie_forge.py --help`).

The code lives in the `forge` package next to this file; uv installs the dependencies listed above.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from forge.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
