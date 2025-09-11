#!/usr/bin/env python3
"""
Simple ChromaDB test for Python 3.13
Just tests if we can install and use ChromaDB
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

def test_chromadb_only():
    """Test installing just ChromaDB"""
    print("🧪 Testing ChromaDB Installation (Minimal)")
    print("=" * 50)
    
    python_cmd = sys.executable
    print(f"Using Python: {python_cmd}")
    
    # First, try to install just ChromaDB
    success = run_command(
        f"{python_cmd} -m pip install chromadb",
        "Installing ChromaDB only"
    )
    
    if not success:
        print("❌ ChromaDB installation failed")
        return False
    
    # Test import
    success = run_command(
        f"{python_cmd} -c \"import chromadb; print('ChromaDB version:', chromadb.__version__)\"",
        "Testing ChromaDB import"
    )
    
    if not success:
        print("❌ ChromaDB import failed")
        return False
    
    return True

def test_chromadb_functionality():
    """Test basic ChromaDB functionality"""
    print("\n🧪 Testing ChromaDB Functionality")
    print("=" * 40)
    
    test_script = """
import chromadb
import tempfile
import os

print("Creating temporary directory...")
temp_dir = tempfile.mkdtemp()
print(f"Using temp directory: {temp_dir}")

try:
    print("Creating ChromaDB client...")
    client = chromadb.PersistentClient(path=temp_dir)
    print("✅ ChromaDB client created")
    
    print("Creating embedding function...")
    embedding_function = chromadb.utils.embedding_functions.DefaultEmbeddingFunction()
    print("✅ Embedding function created")
    
    print("Creating collection...")
    collection = client.get_or_create_collection(
        name="test_collection",
        embedding_function=embedding_function
    )
    print("✅ Collection created")
    
    print("Testing basic operations...")
    collection.add(
        ids=["test1"],
        documents=["This is a test document"],
        metadatas=[{"type": "test"}]
    )
    print("✅ Document added")
    
    print("Testing retrieval...")
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
    print("Cleaning up...")
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
    print("✅ Cleanup completed")
"""
    
    # Write test script to temporary file
    with open("temp_chromadb_simple_test.py", "w") as f:
        f.write(test_script)
    
    try:
        python_cmd = sys.executable
        success = run_command(
            f"{python_cmd} temp_chromadb_simple_test.py",
            "Testing ChromaDB functionality"
        )
        return success
    finally:
        # Cleanup
        if os.path.exists("temp_chromadb_simple_test.py"):
            os.remove("temp_chromadb_simple_test.py")

def main():
    """Run simple ChromaDB test"""
    print("🧪 Simple ChromaDB Test for Python 3.13")
    print("=" * 60)
    
    # Test ChromaDB installation
    install_success = test_chromadb_only()
    
    if not install_success:
        print("\n❌ ChromaDB installation failed")
        print("\n💡 This might be due to Python 3.13 compatibility issues")
        print("💡 For development, you might want to use Python 3.11 or 3.12")
        print("💡 For Render deployment, Python 3.11 will be used automatically")
        return False
    
    # Test functionality
    functionality_success = test_chromadb_functionality()
    
    print("\n" + "=" * 60)
    print("📊 Test Results")
    print("=" * 60)
    print(f"ChromaDB Installation: {'✅ PASS' if install_success else '❌ FAIL'}")
    print(f"ChromaDB Functionality: {'✅ PASS' if functionality_success else '❌ FAIL'}")
    
    if install_success and functionality_success:
        print("\n🎉 ChromaDB works with Python 3.13!")
        print("💡 You can now develop locally with Python 3.13")
        print("💡 Render will use Python 3.11 for deployment")
        return True
    else:
        print("\n❌ ChromaDB has issues with Python 3.13")
        print("💡 Consider using Python 3.11 or 3.12 for development")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
