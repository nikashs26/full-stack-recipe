#!/usr/bin/env python3
"""
Test script to verify Python environment and dependencies
"""

import sys
import os

print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Current working directory: {os.getcwd()}")

# Test core dependencies
try:
    import flask
    print(f"✓ Flask {flask.__version__} imported successfully")
except ImportError as e:
    print(f"✗ Flask import failed: {e}")

try:
    import chromadb
    print(f"✓ ChromaDB imported successfully")
except ImportError as e:
    print(f"✗ ChromaDB import failed: {e}")

try:
    import numpy
    print(f"✓ NumPy {numpy.__version__} imported successfully")
except ImportError as e:
    print(f"✗ NumPy import failed: {e}")

print("Python environment test complete!")
