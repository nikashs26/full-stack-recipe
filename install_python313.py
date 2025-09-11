#!/usr/bin/env python3
"""
Install requirements for Python 3.13 (local development)
Run this with: python3 install_python313.py
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n🔧 {description}")
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout:
                print(f"Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(f"Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} - EXCEPTION: {e}")
        return False

def main():
    """Install requirements for Python 3.13"""
    print("🔧 Installing Requirements for Python 3.13")
    print("=" * 60)
    
    # Get the correct python command
    python_cmd = sys.executable
    print(f"Using Python: {python_cmd}")
    
    # Check Python version
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 13:
        requirements_file = "backend/requirements-python313.txt"
        print(f"✅ Python 3.13+ detected - using compatible requirements")
    else:
        requirements_file = "backend/requirements-render-comprehensive.txt"
        print(f"ℹ️ Python {version.major}.{version.minor} detected - using Render requirements")
    
    # Check if requirements file exists
    if not os.path.exists(requirements_file):
        print(f"❌ Requirements file not found: {requirements_file}")
        return False
    
    print(f"✅ Requirements file found: {requirements_file}")
    
    # Install requirements
    success = run_command(
        f"{python_cmd} -m pip install --upgrade pip",
        "Upgrading pip"
    )
    
    if not success:
        print("⚠️ Pip upgrade failed, but continuing...")
    
    success = run_command(
        f"{python_cmd} -m pip install -r {requirements_file}",
        f"Installing requirements from {requirements_file}"
    )
    
    if not success:
        print("❌ Requirements installation failed")
        return False
    
    # Test ChromaDB import
    success = run_command(
        f"{python_cmd} -c \"import chromadb; print('ChromaDB version:', chromadb.__version__)\"",
        "Testing ChromaDB import"
    )
    
    if not success:
        print("❌ ChromaDB import test failed")
        return False
    
    print("\n🎉 Requirements installed successfully!")
    print("✅ ChromaDB is working")
    print("\n💡 You can now run: python3 test_python313.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
