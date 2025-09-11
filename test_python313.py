#!/usr/bin/env python3
"""
Test script for Python 3.13 compatibility
Run this with: python3 test_python313.py
"""

import sys
import subprocess
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

def test_python_version():
    """Test Python version"""
    print("🐍 Python Version Check")
    print("=" * 30)
    
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 13:
        print("✅ Python 3.13+ detected - using compatible requirements")
        return "313"
    elif version.major == 3 and version.minor == 11:
        print("✅ Python 3.11 detected - using Render requirements")
        return "311"
    else:
        print(f"⚠️ Python {version.major}.{version.minor} detected - may have compatibility issues")
        return "other"

def test_chromadb_installation():
    """Test ChromaDB installation with appropriate requirements"""
    print("\n🧪 ChromaDB Installation Test")
    print("=" * 40)
    
    python_version = test_python_version()
    
    if python_version == "313":
        requirements_file = "backend/requirements-python313.txt"
        print(f"Using Python 3.13 compatible requirements: {requirements_file}")
    else:
        requirements_file = "backend/requirements-render-comprehensive.txt"
        print(f"Using Render requirements: {requirements_file}")
    
    # Check if requirements file exists
    if not os.path.exists(requirements_file):
        print(f"❌ Requirements file not found: {requirements_file}")
        return False
    
    # Install requirements
    python_cmd = sys.executable
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
    
    return True

def test_chromadb_functionality():
    """Test ChromaDB functionality"""
    print("\n🧪 ChromaDB Functionality Test")
    print("=" * 40)
    
    test_script = """
import chromadb
import tempfile
import os

# Create temporary directory
temp_dir = tempfile.mkdtemp()
print(f"Using temp directory: {temp_dir}")

try:
    # Test client creation
    client = chromadb.PersistentClient(path=temp_dir)
    print("✅ ChromaDB client created")
    
    # Test embedding function
    embedding_function = chromadb.utils.embedding_functions.DefaultEmbeddingFunction()
    print("✅ Embedding function created")
    
    # Test collection creation
    collection = client.get_or_create_collection(
        name="test_collection",
        embedding_function=embedding_function
    )
    print("✅ Collection created")
    
    # Test basic operations
    collection.add(
        ids=["test1"],
        documents=["This is a test document"],
        metadatas=[{"type": "test"}]
    )
    print("✅ Document added")
    
    # Test retrieval
    results = collection.get(ids=["test1"])
    if results['ids']:
        print("✅ Document retrieved successfully")
        print(f"Retrieved document: {results['documents'][0]}")
    else:
        print("❌ Document retrieval failed")
        exit(1)
    
    print("✅ All ChromaDB tests passed!")
    
except Exception as e:
    print(f"❌ ChromaDB test failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
finally:
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
"""
    
    # Write test script to temporary file
    with open("temp_chromadb_test.py", "w") as f:
        f.write(test_script)
    
    try:
        python_cmd = sys.executable
        success = run_command(
            f"{python_cmd} temp_chromadb_test.py",
            "Testing ChromaDB functionality"
        )
        return success
    finally:
        # Cleanup
        if os.path.exists("temp_chromadb_test.py"):
            os.remove("temp_chromadb_test.py")

def main():
    """Run all tests"""
    print("🧪 Python 3.13 ChromaDB Test")
    print("=" * 50)
    
    # Test installation
    install_success = test_chromadb_installation()
    
    if not install_success:
        print("\n❌ Installation failed - cannot proceed with functionality test")
        return False
    
    # Test functionality
    functionality_success = test_chromadb_functionality()
    
    print("\n" + "=" * 50)
    print("📊 Test Results")
    print("=" * 50)
    print(f"ChromaDB Installation: {'✅ PASS' if install_success else '❌ FAIL'}")
    print(f"ChromaDB Functionality: {'✅ PASS' if functionality_success else '❌ FAIL'}")
    
    if install_success and functionality_success:
        print("\n🎉 All tests passed! ChromaDB works with your Python version")
        print("\n💡 For Render deployment, the app will use Python 3.11 compatible requirements")
        return True
    else:
        print("\n❌ Some tests failed - check installation")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
