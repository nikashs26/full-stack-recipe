#!/usr/bin/env python3
"""
Quick script to install requirements for Render deployment
Run this with: python3 install_requirements.py
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
    """Install requirements for Render deployment"""
    print("🔧 Installing Requirements for Render Deployment")
    print("=" * 60)
    
    # Get the correct python command
    python_cmd = sys.executable
    print(f"Using Python: {python_cmd}")
    
    # Check if requirements file exists
    requirements_file = "backend/requirements-render-comprehensive.txt"
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
    print("\n💡 You can now run: python3 simple_chromadb_test.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
