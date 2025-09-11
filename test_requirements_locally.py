#!/usr/bin/env python3
"""
Test script to verify requirements work locally before deploying to Render
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

def get_python_command():
    """Get the correct python command for this system"""
    import sys
    return sys.executable

def test_requirements_installation():
    """Test installing the requirements file"""
    print("🧪 Testing Requirements Installation")
    print("=" * 50)
    
    python_cmd = get_python_command()
    print(f"Using Python: {python_cmd}")
    
    # Test installing requirements
    success = run_command(
        f"{python_cmd} -m pip install -r backend/requirements-render-comprehensive.txt",
        "Installing requirements from requirements-render-comprehensive.txt"
    )
    
    if not success:
        return False
    
    # Test ChromaDB import
    success = run_command(
        f"{python_cmd} -c \"import chromadb; print('ChromaDB version:', chromadb.__version__)\"",
        "Testing ChromaDB import and version"
    )
    
    if not success:
        return False
    
    # Test other critical imports
    critical_imports = [
        "numpy",
        "sqlalchemy", 
        "pydantic",
        "flask",
        "flask_cors"
    ]
    
    for module in critical_imports:
        success = run_command(
            f"{python_cmd} -c \"import {module}; print('{module} imported successfully')\"",
            f"Testing {module} import"
        )
        if not success:
            return False
    
    return True

def test_chromadb_functionality():
    """Test basic ChromaDB functionality"""
    print("\n🧪 Testing ChromaDB Functionality")
    print("=" * 50)
    
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
        print("✅ Document retrieved")
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
        python_cmd = get_python_command()
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
    print("🧪 Local Requirements Test")
    print("=" * 50)
    
    # Test requirements installation
    install_success = test_requirements_installation()
    
    if not install_success:
        print("\n❌ Requirements installation failed - cannot proceed")
        return False
    
    # Test ChromaDB functionality
    chromadb_success = test_chromadb_functionality()
    
    print("\n" + "=" * 50)
    print("📊 Test Results")
    print("=" * 50)
    print(f"Requirements Installation: {'✅ PASS' if install_success else '❌ FAIL'}")
    print(f"ChromaDB Functionality: {'✅ PASS' if chromadb_success else '❌ FAIL'}")
    
    if install_success and chromadb_success:
        print("\n🎉 All tests passed! Requirements should work on Render")
        return True
    else:
        print("\n❌ Some tests failed - check requirements file")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
